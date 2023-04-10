"""
Utility functions
"""
import json
import os
import re
from tqdm import tqdm

PUNCT = ',;:\'‘’"“”()[]{}\\/|'
PUNCT_PATTERN = rf'({"|".join([re.escape(char) for char in PUNCT])}|[.!?]+$)'


def check_term_in_corpus(term, tagged_folder, corpus_summary_path, remove=False):
    """
    Displays or all sentences containing specified term for all files in 
    tagged_folder. If remove, removes all sentences containing the term and 
    updates the summary instead.
    """
    corpus_summary = json.load(open(corpus_summary_path, encoding='utf-8'))
    assert term in corpus_summary['totals']['terms']
    corpus_summary['totals']['terms'].pop(term)
    for filename, terms in corpus_summary['files'].items():
        remove_indices = []
        if term not in terms:
            continue
        corpus_summary['files']['filename'].pop(term)
        if not remove:
            print(f'{filename} :\n')
        sents = open(os.path.join(tagged_folder, filename),
                     encoding='utf-8').read().strip().split('\n\n')

        for index, sent in enumerate(sents):
            if not re.findall(rf'\b{term}\b', sent):
                continue
            if remove:
                remove_indices.append(index)
            else:
                sent = ' '.join([line.split()[0] for line in sent.split('\n')])
                print(''.join([x for x in sent if ord(x) <= 256]))
        if remove:
            for index in remove_indices:
                del sents[index]
            with open(os.path.join(tagged_folder, filename), 'w', encoding='utf-8') as f:
                f.write('\n\n'.join(sents))
            print(
                f'Deleted {len(remove_indices)} sentence(s) from {filename}.')
        print('\n------------------\n')
    if remove:
        with open(corpus_summary, 'w', encoding='utf-8') as f:
            f.write(json.dumps(corpus_summary))


def get_alpha_prop(sent):
    total, alnum_count = 0, 0
    for char in sent:
        if char.split():
            total += 1
            if char.isalnum():
                alnum_count += 1
    if not total:
        return 0
    return alnum_count / total


def get_terms_from_tagged_sents(*sents):
    terms = []
    for sent in sents:
        current_term = []
        lines = sent.split('\n')
        last_index = len(lines) - 1
        for index, line in enumerate(lines):
            word, tag = line.split()
            if tag == 'B-Term':
                if current_term:
                    terms.append(' '.join(current_term))
                current_term = [word]
            elif tag == 'I-Term':
                current_term.append(word)
            elif tag == 'O':
                if current_term:
                    terms.append(' '.join(current_term))
                    current_term = []
            if index == last_index and current_term:
                terms.append(' '.join(current_term))

    return terms


def make_re_patterns(terms_ignore_case, terms_keep_case=set()):
    """
    Makes regex patterns to find terms in text.

    Parameters
    ----------
    terms_ignore_case : iterable
        Terms to match ignoring case (don't have common word aliases).
    terms_keep_case : str, optional
        Terms to match case-sensitively (do have common word aliases).
    """
    terms_ignore_case, terms_keep_case = set(
        terms_ignore_case), set(terms_keep_case)
    for set_ in (terms_ignore_case, terms_keep_case):
        update = set()
        for term in set_:
            update.add(term.replace('-', ' '))
            update.add(term.replace(' ', '-'))
        set_.update(update)

    terms_ignore_case = sorted(terms_ignore_case, key=len, reverse=True)
    ignore_case_pattern = re.compile(
        rf'\b({"|".join([re.escape(term) for term in terms_ignore_case])})\b',
        re.IGNORECASE)
    if terms_keep_case:
        terms_keep_case = sorted(
            terms_keep_case, key=len, reverse=True)
        keep_case_pattern = re.compile(
            rf'\b({"|".join([re.escape(term) for term in terms_keep_case])})\b')
    else:
        keep_case_pattern = None
    return ignore_case_pattern, keep_case_pattern


def match_terms_in_sents(term_patterns, *sents, dont_filter_sents=False, neg_sents_proportion=0):
    """Finds termss in sents using re matching.

    If dont_filter_sents, sentences shorter than 5 words or longer than 100 or 
    with a proportion of letters less than .9 (not including spaces) will not 
    be excluded from tagging.
    """
    ignore_case_pattern, keep_case_pattern = term_patterns
    tagged_sents = []
    sents_total, sents_with_entities = 0, 0

    for sent in tqdm(sents):
        # print(sent)
        if not dont_filter_sents and not sent_filter(sent):
            continue
        sent = prepare_sent_NER(sent)
        spans = set()
        spans.update([match.span()
                     for match in re.finditer(ignore_case_pattern, sent)])
        if keep_case_pattern:
            spans.update([match.span()
                          for match in re.finditer(keep_case_pattern, sent)])
        spans = sorted(spans, key=lambda x: (x[0], -x[1]))

        if not spans and neg_sents_proportion != -1:
            if not neg_sents_proportion or not sents_total or (1 - (sents_with_entities / sents_total)) >= neg_sents_proportion:
                continue
        if spans:
            sents_with_entities += 1
        sents_total += 1
        last_stop = 0
        tagged_sent = []
        for index, (start, stop) in enumerate(spans):
            if index != 0 and start in spans[index - 1]:
                continue
            tagged_sent.extend([(word, 'O')
                               for word in sent[last_stop:start].split()])
            tagged_sent.extend([(word, 'B-Term' if not index else 'I-Term')
                               for index, word in enumerate(sent[start:stop].split())])
            last_stop = stop
        if last_stop != len(sent):
            tagged_sent.extend([(word, 'O')
                               for word in sent[last_stop:].split()])
        if tagged_sent:
            tagged_sent = '\n'.join(
                [f'{word} {tag}' for word, tag in tagged_sent])
            tagged_sents.append(tagged_sent)
    return tagged_sents


def normalize_term(term):
    return ''.join([char.lower() for char in term if char.isalnum()])


def prepare_sent_NER(sent):
    return re.sub(PUNCT_PATTERN, r' \1 ', sent)


def sent_filter(sent):
    if 5 <= len(sent.split()) <= 100 and get_alpha_prop(sent) >= .85:
        return True


def sent_tokenize_web_doc(method, filepath):
    text = open(filepath, encoding='utf-8').read()
    sents = []
    text = text.replace('\r', '\n')
    sections = text.split('\n')
    for section in sections:
        sents.extend(method(section))
    return sents


def iob_to_json(filepath, output_path):
    sents = open(filepath, encoding='utf-8').read().split('\n\n')
    output_dicts = []
    for sent in sents:
        output_dict = {'words': [], 'ner': []}
        for line in sent.split('\n'):
            word, tag = line.split()
            output_dict['words'].append(word)
            output_dict['ner'].append(tag)
        output_dicts.append(json.dumps(output_dict))
    open(output_path, 'w', encoding='utf-8').write('\n'.join(output_dicts))


def json_to_roster(json_path, roster_dir=None, test=False):
    roster_text, roster_labels = [], []
    dicts = open(json_path, encoding='utf-8').read().split('\n')
    for line in dicts:
        dict_ = json.loads(line)
        roster_text.append(' '.join(dict_['words']))
        roster_labels.append(' '.join(dict_['ner']))
    text_output_path = 'test_text.txt' if test else 'train_text.txt'
    label_output_path = 'test_label_true.txt' if test else 'train_label_dist.txt'
    text_output_path = os.path.join(
        roster_dir, text_output_path) if roster_dir else text_output_path
    label_output_path = os.path.join(
        roster_dir, label_output_path) if roster_dir else label_output_path
    open(text_output_path, 'w', encoding='utf-8').write('\n'.join(roster_text))
    open(label_output_path, 'w', encoding='utf-8').write('\n'.join(roster_labels))


def reg_iob_to_roster(filepath, roster_dir=None, test=False):
    roster_text, roster_labels = [], []
    sents = open(filepath, encoding='utf-8').read().split('\n\n')
    for sent in sents:
        sent_text, sent_label = [], []
        for line in sent.split('\n'):
            word, tag = line.split()
            sent_text.append(word)
            sent_label.append(tag)
        roster_text.append(' '.join(sent_text))
        roster_labels.append(' '.join(sent_label))
    text_output_path = 'test_text.txt' if test else 'train_text.txt'
    label_output_path = 'test_label_true.txt' if test else 'train_label_dist.txt'
    text_output_path = os.path.join(
        roster_dir, text_output_path) if roster_dir else text_output_path
    label_output_path = os.path.join(
        roster_dir, label_output_path) if roster_dir else label_output_path
    open(text_output_path, 'w', encoding='utf-8').write('\n'.join(roster_text))
    open(label_output_path, 'w', encoding='utf-8').write('\n'.join(roster_labels))


def load_json(path):
    return json.load(open(path, encoding='utf-8'))


def read_lines(path):
    return open(path, encoding='utf-8').read().strip().split('\n')


def write_lines(path, to_write):
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(to_write))


def read_iob(path):
    return open(path, encoding='utf-8').read().strip().split('\n\n')


def write_iob(path, to_write=None):
    with open(path, 'w', encoding='utf-8')as f:
        f.write('\n\n'.join(to_write))
