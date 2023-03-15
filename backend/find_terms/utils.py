"""
Utility functions
"""
import json
import os
import re

PUNCT = ',;:\'‘’"“”()[]{}\\/|'
PUNCT_PATTERN = rf'({"|".join([re.escape(char) for char in PUNCT])}|[.!?]+$)'


def check_term_in_corpus(term, tagged_folder, corpus_summary):
    """
    Displays all sentences containing specified term for all files in 
    tagged_folder.
    """
    corpus_summary = json.load(open(corpus_summary, encoding='utf-8'))
    for filename, terms in corpus_summary['files'].items():
        if term not in terms:
            continue
        print(f'{filename} :\n')
        sents = open(os.path.join(tagged_folder, filename),
                     encoding='utf-8').read().strip().split('\n\n')

        for sent in sents:
            if not re.findall(rf'\b{term}\b', sent):
                continue
            sent = ' '.join([line.split()[0] for line in sent.split('\n')])
            print(''.join([x for x in sent if ord(x) <= 256]))
        print('\n------------------\n')


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
