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
        return 0
    return alnum_count / total


def get_terms_from_tagged_sent(sent):
    terms = []
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


def prepare_sent_NER(sent):
    return re.sub(PUNCT_PATTERN, r' \1 ', sent)


def sent_filter(sent):
    if 5 <= len(sent.split()) <= 100 and get_alpha_prop(sent) >= .9:
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
