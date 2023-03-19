"""
Uses terms to make a training NER corpus.
"""

import json
import os
import random
import re

from tqdm.auto import tqdm
from bs4 import BeautifulSoup

from .utils import (
    get_terms_from_tagged_sents,
    make_re_patterns,
    match_terms_in_sents,
    normalize_term,
    prepare_sent_NER,
    sent_filter,
    sent_tokenize_web_doc)
from . import pdf_utils


def add_to_summary(summary, words):
    for word in words:
        summary.setdefault(word, 0)
        summary[word] += 1


def get_file_summary(corpus_summary, filename, sents):
    file_summary = corpus_summary['files'][filename] = {}
    for sent in sents:
        word_count = len(sent.split('\n'))
        corpus_summary['corpus']['total']['sent_count'] += 1
        corpus_summary['corpus']['total']['word_count'] += word_count
    terms = get_terms_from_tagged_sents(*sents)
    add_to_summary(file_summary, terms)


def get_out_of_vocabulary_prop(train_test_sets):
    """
    Reports type and token out-of-vocabulary proportion in test(dev and/or
    test) sets, i.e. the proportion of entity types and tokens in the test sets
    that don't occur in the training set. (Approximate)
    """
    train_sents = train_test_sets[0]
    test_sents = []
    for set_ in train_test_sets[1:]:
        test_sents.extend(set_)
    assert len(train_sents) > len(test_sents)
    train_dict, test_dict = {}, {}
    for sents in (train_sents, test_sents):
        dict_ = train_dict if sents is train_sents else test_dict
        terms = [normalize_term(term) for term in set(
            get_terms_from_tagged_sents(*sents))]
        add_to_summary(dict_, terms)
    type_oov = set(test_dict.keys()).difference(set(train_dict.keys()))
    type_oov_count = len(type_oov)
    type_oov_prop = type_oov_count / len(test_dict)
    token_oov_count = sum([test_dict[x] for x in type_oov])
    token_oov_prop = token_oov_count / sum(test_dict.values())
    overlap_dict = {
        'type_oov_count': type_oov_count,
        'type_oov_prop': round(type_oov_prop, 2),
        'token_oov_count': token_oov_count,
        'token_oov_prop': round(token_oov_prop, 2)
    }
    return overlap_dict


def replace_terms_with_oov(term_patterns, term_sets, train_sents, test1_sents, test2_sents=()):
    """
    Replaces terms in test and dev sentences with terms that don't occur in 
    train sentences.
    """
    ignore_case_pattern, keep_case_pattern = term_patterns
    ignore_case_terms, _ = term_sets
    ignore_case_terms = set([term.lower().replace('-', ' ')
                            for term in ignore_case_terms])
    vocab = set(get_terms_from_tagged_sents(*train_sents))
    vocab_ignore_case, vocab_keep_case = set(), set()
    for term in vocab:
        if re.match(ignore_case_pattern, rf'{term}$'):
            vocab_ignore_case.add(term)
        if re.match(keep_case_pattern, rf'{term}$'):
            vocab_keep_case.add(term)
    vocab_ignore_case_pattern, vocab_keep_case_pattern = make_re_patterns(
        vocab_ignore_case, vocab_keep_case)
    all_oov_terms = []
    for term in ignore_case_terms:
        if not re.match(vocab_ignore_case_pattern, rf'{term}$'):
            all_oov_terms.append(term)
    return_sets = {}
    for sents in (test1_sents, test2_sents):
        key = 'test1' if sents is test1_sents else 'test2'
        terms = set(get_terms_from_tagged_sents(*sents))
        if test2_sents:
            if key == 'test1':
                oov_terms = all_oov_terms[:round(len(all_oov_terms) / 2)]
            else:
                oov_terms = all_oov_terms[round(len(all_oov_terms) / 2):]
        else:
            oov_terms = all_oov_terms

        replace_dict = {}

        def re_sub_oov(match):
            return replace_dict.get(match.group(0), match.group(0))

        oov_index = 0
        last_oov_index = len(oov_terms) - 1
        for term in terms:
            if oov_index > last_oov_index:
                oov_index = 0
            replace_dict[term] = oov_terms[oov_index]
            oov_index += 1

        for index, sent in enumerate(sents):
            if not get_terms_from_tagged_sents(sent):
                continue
            sent = ' '.join([line.split()[0] for line in sent.split('\n')])
            sent = re.sub(vocab_ignore_case_pattern, re_sub_oov, sent)
            if vocab_keep_case_pattern:
                sent = re.sub(vocab_keep_case_pattern, re_sub_oov, sent)
            if key == 'test2':
                sent = re.sub(test1_terms_ignore_case_pattern,
                              re_sub_oov, sent)
                if test1_terms_keep_case_pattern:
                    sent = re.sub(test1_terms_keep_case_pattern,
                                  re_sub_oov, sent)
            sent = match_terms_in_sents(
                term_patterns, sent, dont_filter_sents=True)[0]
            sents[index] = sent
        return_sets[key] = sents

        if key == 'test1' and test2_sents:
            test_terms_ignore_case, test_terms_keep_case = set(), set()
            for term in terms:
                if re.match(vocab_ignore_case_pattern, f'{term}$') or re.match(vocab_keep_case_pattern, f'{term}$'):
                    continue
                if re.match(ignore_case_pattern, f'{term}$'):
                    test_terms_ignore_case.add(term)
                if re.match(keep_case_pattern, f'{term}$'):
                    test_terms_keep_case.add(term)
            test1_terms_ignore_case_pattern, test1_terms_keep_case_pattern = make_re_patterns(
                test_terms_ignore_case, test_terms_keep_case)
    train_terms = set(get_terms_from_tagged_sents(*train_sents))
    test1_terms = set(get_terms_from_tagged_sents(*test1_sents))
    test2_terms = set(get_terms_from_tagged_sents(*test2_sents))
    assert not train_terms & test1_terms
    assert not train_terms & test2_terms
    assert not test1_terms & test2_terms
    return return_sets


def make_train_test_sets(folder, args_ref, train_test_split=(85, 15)):
    """Makes train, dev, and test sets and corpus summary."""
    sents = []
    corpus_summary = {
        'corpus': {
            'args': args_ref,
            'oov': {},
            'total': {
                'sent_count': 0,
                'word_count': 0,
                'terms': {}
            }, },
        'files': {}
    }
    for filename in os.listdir(folder):
        file_sents = open(os.path.join(folder, filename),
                          encoding='utf-8').read().split('\n\n')
        sents.extend(file_sents)
        get_file_summary(corpus_summary, filename, file_sents)

    for terms_dict in corpus_summary['files'].values():
        for term, count in terms_dict.items():
            corpus_summary['corpus']['total']['terms'].setdefault(term, 0)
            corpus_summary['corpus']['total']['terms'][term] += count

    random.shuffle(sents)
    assert sum(train_test_split) == 100
    sets = []
    last_index = 0
    for index, percentage in enumerate(train_test_split):
        count = round(len(sents) * (percentage / 100))
        if index == len(train_test_split) - 1:
            sets.append(sents[last_index:])
        else:
            sets.append(sents[last_index:last_index + count])
            last_index += count
    oov_dict = get_out_of_vocabulary_prop(sets)
    corpus_summary['corpus']['oov'] = oov_dict
    return sets, corpus_summary


def make_corpus(input_folder,
                output_folder,
                train_test_split=(85, 15),
                dont_filter_sents=False,
                neg_sents_proportion_pdf=0,
                neg_sents_proportion_web=0,
                replace_test_terms_with_oov=False,
                ** kwargs):
    """Uses provided terms to make a training NER corpus.

    Can be re-run on existing output folder by adding files of the appropriate
    type to the input folder or other folders (e.g. adding a pdf to the
    input_folder, a sentence-tokenized file to the sentence_tokenized folder).
    The new data will be processed through the rest of the pipeline and added
    to the train, dev, and test sets.

    Parameters
    ----------
    input_folder : str
        Path to folder containing input files (pdfs, htm/l, and txt files). If
        None, corpus will be created from already processed files in output
        folder, if any
    output_folder : str
        Folders containing extracted, sentence-tokenized, and tagged text, and
        train, dev, and test sets go here.
    train_test_split : tuple, optional
        Percentages of sentences in train, dev, test sets. Defaults to (85, 15)
        (train and dev only).
    dont_filter_sents : bool, optional
        By default, sentences longer than 100 words or with a proportion of
        letter characters less than .9 (not including spaces) will be excluded
        from the output. Set to True to tag these as well
    neg_sents_proportion_pdf : int, optional
        The percentage of the corpus made of sentences without entities for
        pdfs. -1 to include all sentences.
    neg_sents_proportion_web : int, optional
        The percentage of the corpus made of sentences without entities for
        web documents or text files. -1 to include all sentences.
    """
    if kwargs.get('sent_tokenize_method') == 'spacy':
        import spacy
        nlp = spacy.load('en_core_web_sm')

        def sent_tokenize(text):
            sents = nlp(text).sents
            return [str(sent) for sent in sents]

    else:
        from nltk import sent_tokenize

    args_ref = {
        'train_test_split': train_test_split,
        'dont_filter_sents': dont_filter_sents,
        'neg_sents_proportion_pdf': neg_sents_proportion_pdf,
        'neg_sents_proportion_web': neg_sents_proportion_web,
        'replace_test_terms_with_oov': replace_test_terms_with_oov,
        'kwargs': kwargs
    }

    use_line_ends = kwargs.get('use_line_ends', True)
    terms_ignore_case_path = kwargs.get(
        'terms_ignore_cast_path', 'data/find_terms/tool_names_ignore_case.txt')
    terms_keep_case_path = kwargs.get(
        'terms_keep_cast_path', 'data/find_terms/tool_names_keep_case.txt')
    terms_ignore_case = set(open(
        terms_ignore_case_path, encoding='utf-8').read().split('\n'))
    terms_keep_case = set(open(terms_keep_case_path,
                               encoding='utf-8').read().split('\n'))
    term_patterns = make_re_patterns(
        terms_ignore_case, terms_keep_case)

    text_folder = os.path.join(output_folder, 'text')
    tokenized_folder = os.path.join(output_folder, 'sentence_tokenized')
    tagged_folder = os.path.join(output_folder, 'tagged')
    train_test_split_folder = os.path.join(output_folder, 'train_test_sets')

    for folder in (text_folder,
                   tokenized_folder,
                   tagged_folder,
                   train_test_split_folder):
        if not os.path.isdir(folder):
            os.makedirs(folder)
    log_path = os.path.join(output_folder, 'log.json')
    if not os.path.isfile(log_path):
        log = {}
    else:
        log = json.load(open(log_path, encoding='utf-8'))

    input_files = os.listdir(input_folder) if input_folder else None
    if input_files:
        for filename in tqdm(input_files,
                             desc='Extracting text / tokenizing sentences',
                             position=0,
                             leave=True):
            file_ref, ext = os.path.splitext(filename)
            if file_ref not in log:
                log.setdefault(file_ref, {'ext': ext, 'no_terms': False})
                open(log_path, 'w', encoding='utf-8').write(json.dumps(log))
            if f'{file_ref}.txt' in (
                    os.listdir(text_folder) + os.listdir(tagged_folder)) or log[file_ref].get('no_terms'):
                continue
            text = None
            if ext == '.txt':
                text = open(os.path.join(input_folder, filename),
                            encoding='utf-8').read()
                sents = sent_tokenize(text)
                with open(os.path.join(tokenized_folder, filename), 'w',
                          encoding='utf-8') as f:
                    f.write('\n'.join(sents))
                continue
            elif ext == '.pdf':
                text = pdf_utils.pdf_to_txt(
                    os.path.join(input_folder, filename))
            elif ext in ('.htm', '.html'):
                html = open(os.path.join(input_folder, filename),
                            encoding='utf-8').read()
                text = BeautifulSoup(html, 'lxml').text
            if text:
                with open(os.path.join(text_folder, f'{file_ref}.txt'),
                          'w', encoding='utf-8') as f:
                    f.write(text)

    for filename in tqdm(os.listdir(text_folder),
                         desc='Tokenizing sentences',
                         position=0,
                         leave=True):
        file_ref = os.path.splitext(filename)[0]
        # Uses web doc tokenization for text files manually added to text folder.
        if file_ref not in log:
            log[file_ref] = {'ext': '.html'}
        ext = log[file_ref]['ext']
        if f'{file_ref}.txt' in (os.listdir(tokenized_folder) +
                                 os.listdir(tagged_folder)) or log[file_ref].get('no_terms'):
            continue
        sents = None
        if ext == '.pdf':
            sents = pdf_utils.tokenize_doc_from_filepath(
                os.path.join(text_folder, filename), sent_tokenize,
                use_line_ends=use_line_ends)
        elif ext in ('.htm', '.html'):
            sents = sent_tokenize_web_doc(
                sent_tokenize, os.path.join(text_folder, filename))
        if sents:
            with open(os.path.join(tokenized_folder, filename), 'w', encoding='utf-8') as f:
                f.write('\n'.join(sents))

    for filename in tqdm(os.listdir(tokenized_folder),
                         desc='Finding terms',
                         position=0,
                         leave=True):
        file_ref = os.path.splitext(filename)[0]
        ext = log[file_ref]['ext']
        if f'{file_ref}.txt' in os.listdir(tagged_folder) or log[file_ref].get('no_terms'):
            continue
        sents = open(os.path.join(tokenized_folder, filename),
                     encoding='utf-8').read().strip().split('\n')
        sents = set(sents)
        neg_sents_proportion = neg_sents_proportion_pdf if ext == '.pdf' else neg_sents_proportion_web
        tagged_sents = match_terms_in_sents(
            term_patterns, *sents, dont_filter_sents=dont_filter_sents, neg_sents_proportion=neg_sents_proportion)
        if tagged_sents:
            with open(os.path.join(tagged_folder, filename), 'w', encoding='utf-8') as f:
                f.write('\n\n'.join(tagged_sents))
        else:
            log[file_ref]['no_terms'] = True
            open(log_path, 'w', encoding='utf-8').write(json.dumps(log))

    if os.listdir(tagged_folder):
        sets, summary = make_train_test_sets(
            tagged_folder, args_ref, train_test_split=train_test_split)

        if replace_test_terms_with_oov:
            return_sets = replace_terms_with_oov(
                term_patterns, (terms_ignore_case, terms_keep_case), *sets)
            sets = [set_ for set_ in (
                sets[0], return_sets['test1'], return_sets['test2']) if set_]
            summary['corpus'].pop('oov')
        labels = {0: 'train.txt', 1: 'dev.txt', 2: 'test.txt'}
        for index, set_ in enumerate(sets):
            with open(os.path.join(train_test_split_folder, labels[index]),
                      'w', encoding='utf-8') as f:
                f.write('\n\n'.join(set_))
        with open(os.path.join(train_test_split_folder, 'corpus_summary.json'),
                  'w', encoding='utf-8') as f:
            f.write(json.dumps(summary))

        print('\nCorpus is ready!')
