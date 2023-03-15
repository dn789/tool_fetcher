"""
PDF text extraction and sentence tokenization.
"""

from pdfminer import high_level
from pdfminer.layout import LAParams


COMMON_WORDS_DIR = 'data/find_terms/common_words.txt'
COMMON_WORDS = set(
    open(COMMON_WORDS_DIR, encoding='utf-8').read().strip().split('\n'))


def tokenize_doc(doc, sent_tokenize_method, use_line_ends=True):
    """
    Tokenizes sentences in document.

    Parameters
    ----------
    doc : list of str or str
        List of lines or file path.
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

    if type(doc) == str:
        doc = open(doc, encoding='utf-8').read().strip().split('\n')
    lines = [''] + [line for line in doc if line.strip()] + ['']

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
