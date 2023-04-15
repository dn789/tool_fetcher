"""
Utility functions
"""
import json
import os
import re

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
        return
    return alnum_count / total


def get_terms_from_tagged_sents(sents):
    terms = []
    for sent in sents:
        current_term = []
        last_index = len(sent['labels']) - 1
        for index, (word, tag) in enumerate(zip(sent['text'], sent['labels'])):
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


def make_term_patterns(terms_ignore_case, terms_keep_case=None):
    """
    Makes regex patterns to find terms in text.

    Parameters
    ----------
    terms_ignore_case : iterable
        Terms to match ignoring case (don't have common word aliases).
    terms_keep_case : iterable, optional
        Terms to match case-sensitively.
    """
    term_patterns = {}

    for terms in (terms_ignore_case, terms_keep_case):
        key = 'ignore_case' if terms is terms_ignore_case else 'keep_case'
        if not terms:
            term_patterns[key] = None
            continue
        terms = set(terms)
        update = set()
        for term in terms:
            update.add(term.replace('-', ' '))
            update.add(term.replace(' ', '-'))
        terms.update(update)
        sorted_terms = sorted(terms, key=len, reverse=True)
        escaped_terms = [re.escape(term) for term in sorted_terms]
        flags = re.IGNORECASE if key == 'ignore_case' else 0
        term_pattern = re.compile(
            rf'\b({"|".join(escaped_terms)})\b', flags=flags)
        term_patterns[key] = term_pattern

    return term_patterns


def match_terms_in_sents(term_patterns, sents, return_terms_only=False):
    """
    Finds terms in sentences using regex, returning a dictionary of tagged 
    sentences and a list of matched terms.
    """
    tagged_sents = []
    matched_terms = set()
    for sent in sents:
        sent = prepare_sent_NER(sent)
        spans = set()
        spans.update([match.span()
                     for match in re.finditer(term_patterns['ignore_case'], sent)])
        if term_patterns['keep_case']:
            spans.update([match.span()
                          for match in re.finditer(term_patterns['keep_case'], sent)])
        spans = sorted(spans, key=lambda x: (x[0], -x[1]))
        last_stop = 0
        text, labels = [], []
        for index, (start, stop) in enumerate(spans):
            matched_terms.add(sent[start:stop])
            if index != 0 and start in spans[index - 1]:
                continue
            for word in sent[last_stop:start].split():
                text.append(word)
                labels.append('O')
            for index, word in enumerate(sent[start:stop].split()):
                text.append(word)
                labels.append('B-Term' if not index else 'I-Term')
            last_stop = stop
        if last_stop != len(sent):
            for word in sent[last_stop:].split():
                text.append(word)
                labels.append('O')
        if text:
            tagged_sent = {'text': text, 'labels': labels}
            tagged_sents.append(tagged_sent)
    if return_terms_only:
        return matched_terms
    return tagged_sents, matched_terms


def prepare_sent_NER(sent):
    return re.sub(PUNCT_PATTERN, r' \1 ', sent)


def sent_filter(sent):
    if 5 <= len(sent.split()) <= 100 and get_alpha_prop(sent) >= .85:
        return True


def sent_tokenize_web_doc(text, method):
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


def read(path):
    if type(path) != str:
        path = os.path.join(*[x for x in path])
    return open(path, encoding='utf-8').read()


def read_lines(path):
    if type(path) != str:
        path = os.path.join(*[x for x in path])
    return open(path, encoding='utf-8').read().strip().split('\n')


def write(to_write, path):
    if type(path) != str:
        path = os.path.join(*[x for x in path])
    with open(path, 'w', encoding='utf-8') as f:
        f.write(to_write)


def write_lines(to_write, path):
    if type(path) != str:
        path = os.path.join(*[x for x in path])
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(to_write))


def read_iob(path):
    return open(path, encoding='utf-8').read().strip().split('\n\n')


def write_iob(path, to_write=None):
    with open(path, 'w', encoding='utf-8')as f:
        f.write('\n\n'.join(to_write))
