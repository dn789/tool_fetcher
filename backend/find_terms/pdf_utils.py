"""
PDF text extraction, sentence tokenization, and highlighting.
"""
import io

import fitz
from pdfminer import high_level
from pdfminer.layout import LAParams

PUNCT = '\'"‘’“”\(\)\[\]:,;.!?'


COMMON_WORDS_DIR = 'data/find_terms/common_words.txt'
COMMON_WORDS = set(
    open(COMMON_WORDS_DIR, encoding='utf-8').read().strip().split('\n'))


def tokenize_doc_from_text(text, sent_tokenize_method, use_line_ends=True):
    """
    Tokenizes sentences in document.

    Parameters
    ----------
    text : Extracted text from a pdf.
    sent_tokenize_method: func
        Method that takes a text string and returns a list of sentences.
    use_line_ends : bool
        Uses the presence or absence of spaces before newlines
        in text extracted from PDFs to aid tokenization. This method doesn't
        appear to work on extracted text with relatively few spaces before
        newlines, and is automatically disabled on text with fewer than 25%
        of lines ending in spaces. 

    Returns
    -------
    list of str
        List of sentences.
    """
    lines = text.split('\n')
    lines = [''] + [line for line in lines if line.strip()] + ['']

    end_space_count = 0
    word_types = set()

    for index, line in enumerate(lines):
        # Determine percentage of lines ending in spaces. If under 25%, spaces
        # at the ends of lines will not be used to aid tokenization.
        if line.endswith(' '):
            end_space_count += 1
        # Word types in document, combined with COMMON_WORDS, used as
        # a reference for recombining words split on hyphens.
        for w_index, word in enumerate(line.split()):
            # Use word tokenizer here instead?
            if not (word[0] in '-\\/' or word[-1] in '-\\/'):
                if not (lines[index - 1].endswith('-') and w_index == 0):
                    word = word.strip('\'",;:-.?!()[]\\/')
                    if len(word) > 1:
                        word_types.add(word)
    reference_words = COMMON_WORDS | word_types
    if (end_space_count / len(lines)) * 100 < 25:
        use_line_ends = False

    # Combines lines separated by hyphens and slashes.

    # If use_line_ends is True, lines ending in spaces are grouped with the
    # following line, and each group and ungrouped line is tokenized separately.
    # Otherwise, all lines are tokenized together.
    new_lines = []
    current_line = []
    for index, line in enumerate(lines):
        if not line:
            continue
        # Deletes hyphens if surrounding text combines to form a word in
        # reference_words.
        if line.endswith('-'):
            possible = line.split()[-1][:-1] + lines[index + 1].split()[0]
            possible = possible.strip('\'",;:-.?!()[]\\/')
            if possible:
                if possible[0].lower() + possible[1:] in reference_words or \
                        possible[0].upper() + possible[1:] in reference_words:
                    current_line.append(line[:-1])
                else:
                    current_line.append(line)
            else:
                current_line.append(line)
        elif line[-1] in (' ', '\\', '/'):
            current_line.append(line)
        elif current_line:
            current_line.append(line)
            if use_line_ends:
                new_lines.extend(sent_tokenize_method(''.join(current_line)))
            else:
                new_lines.append(''.join(current_line))
            current_line = []
        else:
            if use_line_ends:
                new_lines.extend(sent_tokenize_method(line))
            else:
                new_lines.append(line)

    if use_line_ends:
        tokenized_sents = new_lines
    else:
        text = ' '.join(new_lines)
        tokenized_sents = sent_tokenize_method(text)
    filtered_sents = []
    for sent in tokenized_sents:
        sent = sent.strip()
        if sent:
            filtered_sents.append(sent)
    return filtered_sents


def tokenize_doc_from_filepath(filepath, sent_tokenize_method, use_line_ends):
    return tokenize_doc_from_text(open(filepath, encoding='utf-8').read().strip(),
                                  sent_tokenize_method=sent_tokenize_method,
                                  use_line_ends=use_line_ends)


def pdf_to_txt(doc, output_path=None):
    """
    Extracts text from PDF.

    Parameters
    ----------
    doc : file object or str
        PDF or path to PDF. 
    """
    if type(doc) == str:
        fp = open(doc, 'rb')
    else:
        fp = doc
    text = high_level.extract_text(fp, laparams=LAParams())
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as outputfile:
            outputfile.write(text)
    else:
        return text


def process_word_obj(word_obj):
    """Separates punctuation from word_obj for more precise highlighting."""
    r = fitz.Rect()
    word = ''
    started = False
    for char in word_obj:
        if started:
            if char['c'] not in PUNCT:
                r |= char['bbox']
                word += char['c']
            else:
                break
        elif char['c'] not in PUNCT:
            started = True
            r |= char['bbox']
            word += char['c']
    return r, word


def highlight(pdf_or_path,
              terms,
              return_pdf=False,
              output_path=None,
              fast=False,
              ):
    """
    Highlights terms in PDF. Fast version (adjacent punctuation also gets
    higlighted).

    Parameters
    ----------
    pdf_or_path : file or str
        PDF file object or path to PDF. 
    terms : list, str, or (list, dict)
        List of terms to highlight, path to terms file (one term per line), or 
        terms_tree from find_terms.make_terms_tree.
    output_path : str, optional
        Path for saving highlighted PDF. Will save if provided. 
    fast : bool, default True
        Faster but less precise PDF highlight method (highlights adjacent 
        punctuation).

    Returns
    -------
    (terms, PDF), optional
    terms: list
        List of terms (from supplied terms and those found 
        by the NER model, if applicable).
    PDF: file
        Highlighted PDF.     
    """
    results_dict = {}

    terms, terms_dict = make_terms_tree(terms)

    def process_doc_words(doc_words, page):
        current_dict = terms_dict
        positions_to_highlight, current_term = [], []
        # Index of first part of word continued on next line.
        across_lines_index = None
        word_across_lines = False
        last_index = len(doc_words) - 1
        for index, doc_word in enumerate(doc_words):
            if fast:
                *position, word, _1, _2, _3 = doc_word
            else:
                position, word = process_word_obj(doc_word)
            word = word.strip('\'"‘’“”\(\)\[\]:,;.!?')
            # Continues if on second part of a word across lines.
            if word_across_lines:
                word_across_lines = False
                continue
            if word in current_dict:
                positions_to_highlight.append(position)
                current_term.append(word)
                current_dict = current_dict[word]
            elif word.endswith('-') and index != last_index:
                if fast:
                    *next_pos, next_word, _1, _2, _3 = doc_words[index + 1]
                else:
                    *next_pos, next_word, = process_word_obj(doc_words[index +
                                                                       1])
                word_across_lines = True
                # Looks ahead and add second part of word across lines.
                if word[:-1] + next_word in current_dict:
                    across_lines_index = index
                    positions_to_highlight.extend([position, next_pos])
                    current_term.extend([word[:-1], next_word])
                    current_dict = current_dict[word[:-1] + next_word]
            elif positions_to_highlight:
                current_term = ' '.join(current_term)
                if current_term in terms:
                    results_dict.setdefault(current_term, 0)
                    results_dict[current_term] += 1
                    for position in positions_to_highlight:
                        page.add_highlight_annot(position)
                else:
                    # Continues processing one index later if currently on
                    # second part of word continued on next line (otherwise
                    # second part of word will be treated as its own word).
                    if across_lines_index is not None and index == across_lines_index + 1:
                        if index != last_index:
                            target_index = index + 1
                        else:
                            return
                    else:
                        target_index = index - \
                            (len(positions_to_highlight) - 1)
                    process_doc_words(doc_words[target_index:], page)
                    return
                across_lines_index = None
                positions_to_highlight, current_term = [], []
                current_dict = terms_dict
            # Handles term at the end of page.
            if index == last_index and positions_to_highlight:
                for position in positions_to_highlight:
                    page.add_highlight_annot(position)

    if type(pdf_or_path) == str:
        doc = fitz.open(pdf_or_path)
    else:
        doc = fitz.open(stream=pdf_or_path, filetype='pdf')
    for page in doc:
        if fast:
            doc_words = page.get_text()
            return doc_words

        else:
            doc_words = []
            blocks = page.get_text('rawdict')['blocks']
            for b in blocks:
                try:
                    for l in b['lines']:
                        for s in l['spans']:
                            word = []
                            last_index = len(s['chars']) - 1
                            for index, char in enumerate(s['chars']):
                                if char['c'] not in ' \t':
                                    word.append(char)
                                if char['c'] in ' \t' or index == last_index:
                                    doc_words.append(word)
                                    word = []
                except KeyError:
                    continue

        process_doc_words(doc_words, page)
    if output_path:
        doc.save(output_path, garbage=4, deflate=True, clean=True)
    if return_pdf:
        return doc.tobytes(garbage=4, deflate=True, clean=True)


def find_terms_func():
    pass


def make_terms_tree(terms):
    """
    Makes search tree of terms to find in text.

    Parameters
    ----------
    terms : str or list
        List of terms or path to terms file (one term per line).
   """
    terms = set(terms)
    terms_dict = {}
    for term in terms:
        current_dict = terms_dict
        for word in term.split():
            current_dict.setdefault(word, {})
            current_dict = current_dict[word]
    return terms, terms_dict
