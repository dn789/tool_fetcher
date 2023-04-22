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
    load_json,
    make_term_patterns,
    match_terms_in_sents,
    read,
    read_lines,
    sent_filter,
    sent_tokenize_web_doc,
    write,
    write_lines
)
from . import pdf_utils


def get_file_summary(corpus_summary, filename, sents):
    file_summary = corpus_summary['files'][filename] = {}
    for sent in sents:
        word_count = len(sent['labels'])
        corpus_summary['corpus']['total']['sent_count'] += 1
        corpus_summary['corpus']['total']['word_count'] += word_count
    terms = get_terms_from_tagged_sents(sents)
    for term in terms:
        file_summary[term] = file_summary.setdefault(term, 0) + 1


def replace_terms_with_oov(term_patterns, term_sets, train_sents, test1_sents, test2_sents=()):
    """
    Replaces terms in test and dev sentences with terms that don't occur in
    train sentences.
    """
    ignore_case_terms, _ = term_sets
    ignore_case_terms = set([term.lower().replace('-', ' ')
                            for term in ignore_case_terms])
    vocab = set(get_terms_from_tagged_sents(train_sents))
    vocab_ignore_case, vocab_keep_case = set(), set()
    for term in vocab:
        if re.match(term_patterns['ignore_case'], rf'{term}$'):
            vocab_ignore_case.add(term)
        if re.match(term_patterns['keep_case'], rf'{term}$'):
            vocab_keep_case.add(term)
    vocab_patterns = make_term_patterns(
        vocab_ignore_case, vocab_keep_case)
    all_oov_terms = []
    for term in ignore_case_terms:
        if not re.match(vocab_patterns['ignore_case'], rf'{term}$'):
            all_oov_terms.append(term)
    return_sets = {}
    for sents in (test1_sents, test2_sents):
        key = 'test1' if sents is test1_sents else 'test2'
        terms = set(get_terms_from_tagged_sents(sents))
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

        for index, sent_dict in enumerate(sents):
            if not get_terms_from_tagged_sents([sent_dict]):
                continue
            sent = ' '.join(sent_dict['text'])
            sent = re.sub(vocab_patterns['ignore_case'], re_sub_oov, sent)
            if vocab_patterns['keep_case']:
                sent = re.sub(vocab_patterns['keep_case'], re_sub_oov, sent)
            if key == 'test2':
                sent = re.sub(test1_patterns['ignore_case'],
                              re_sub_oov, sent)
                if test1_patterns['keep_case']:
                    sent = re.sub(test1_patterns['keep_case'],
                                  re_sub_oov, sent)
            sent_dict = match_terms_in_sents(
                term_patterns, [sent])
            sents[index] = sent_dict[0]

        return_sets[key] = [x for x in sents if x]

        if key == 'test1' and test2_sents:
            test_terms_ignore_case, test_terms_keep_case = set(), set()
            for term in terms:
                if re.match(vocab_patterns['ignore_case'], f'{term}$') or re.match(vocab_patterns['keep_case'], f'{term}$'):
                    continue
                if re.match(term_patterns['ignore_case'], f'{term}$'):
                    test_terms_ignore_case.add(term)
                if re.match(term_patterns['keep_case'], f'{term}$'):
                    test_terms_keep_case.add(term)
            test1_patterns = make_term_patterns(
                test_terms_ignore_case, test_terms_keep_case)
    train_terms = set(get_terms_from_tagged_sents(train_sents))
    test1_terms = set(get_terms_from_tagged_sents(test1_sents))
    test2_terms = set(get_terms_from_tagged_sents(test2_sents))
    assert not train_terms & test1_terms
    assert not train_terms & test2_terms
    assert not test1_terms & test2_terms
    return return_sets


def make_train_test_sets(folder,
                         args_ref,
                         log,
                         train_test_split=(85, 15),
                         neg_sent_proportion_pdf=.75,
                         neg_sent_proportion_web=.75,
                         dont_filter_sents=False):
    combined_sents = []
    corpus_summary = {
        'corpus': {
            'args': args_ref,
            'total': {
                'sent_count': 0,
                'word_count': 0,
                'terms': {}
            }, },
        'files': {}
    }
    for filename in os.listdir(folder):
        file_ref = os.path.splitext(filename)[0]
        neg_sent_proportion = neg_sent_proportion_pdf if log[
            file_ref]['type'] == '.pdf' else neg_sent_proportion_web
        sent_count, neg_sent_count = 0, 0
        file_sents = [json.loads(sent) for sent in read_lines(
            os.path.join(folder, file_ref + '.jsonl'))]
        for sent_dict in file_sents:
            sent = ' '.join(sent_dict['text'])
            if not dont_filter_sents and not sent_filter(sent):
                continue
            if 'B-Term' in sent_dict['labels']:
                sent_count += 1
                combined_sents.append(sent_dict)
            else:
                if not neg_sent_proportion:
                    continue
                if neg_sent_proportion == -1 or (sent_count and neg_sent_count / sent_count < neg_sent_proportion):
                    sent_count += 1
                    neg_sent_count += 1
                    combined_sents.append(sent_dict)
        get_file_summary(corpus_summary, filename, combined_sents)

    for terms_dict in corpus_summary['files'].values():
        for term, count in terms_dict.items():
            corpus_summary['corpus']['total']['terms'].setdefault(term, 0)
            corpus_summary['corpus']['total']['terms'][term] += count

    random.shuffle(combined_sents)
    assert sum(train_test_split) == 100
    sets = []
    last_index = 0
    for index, percentage in enumerate(train_test_split):
        count = round(len(combined_sents) * (percentage / 100))
        if index == len(train_test_split) - 1:
            sets.append(combined_sents[last_index:])
        else:
            sets.append(combined_sents[last_index:last_index + count])
            last_index += count
    return sets, corpus_summary


def make_corpus(input,
                output,
                train_test_dir='set1',
                train_test_split=(85, 15),
                neg_sent_proportion_pdf=0,
                neg_sent_proportion_web=0,
                dont_filter_sents=False,
                replace_test_terms_with_oov=False,
                sent_tokenize_method='nltk',
                use_line_ends_for_pdf_tokenization=True,
                terms_ignore_case_path=None,
                terms_keep_case_path=None):
    """
    Uses provided terms and files to make a training NER corpus.

    Input can be PDFs, HTML and text files. Intermediate subfolders will be
    made in output folder for extracted, sentence-tokenized and tagged text.
    Re-run with files of the appropriate type added to input folder or the 
    intermediate folders (e.g. a new PDF added to the input folder or a 
    sentence-tokenized .txt file added to the sentence_tokenized folder) to add
    them to the training/test sets. 

    A new set of training/test files will be created in the train_test_sets 
    folder on every run. To make a new set with different parameters without 
    overwriting previous ones, change train_test_folder. 

    NOTE: Every parameter can be changed on re-run without modifying the
    intermediate files except for:

    sent_tokenize_method, 
    use_line_ends_for_pdf_tokenization, 
    terms_ignore_case_path, 
    terms_keep_case_path

    To change the tokenization parameters, files in the sentence_tokenized 
    folder and tagged folder should be deleted. To change the terms used for 
    tagging, files in the tagged folder should be deleted.


    Parameters
    ----------
    input : str
        Path to folder containing input files (PDFs, HTM/L, and .txt files). If
        None, training/test sets will be created from already processed files 
        in output folder.
    output : str
    train_test_folder: str, default 'set1' 
        Specify a different name if creating multiple train/test sets in the 
        same output folder. 
    train_test_split : tuple of ints, default (85, 15)
        Determines the number of training/test sets and the percentage of total
        sentences in each (must sum to 100). Training set is first. 
    dont_filter_sents : bool, default False
        By default, sentences longer than 100 words or with a proportion of
        letter characters less than .9 (not including spaces) will be excluded
        from the output. Set to True to tag these as well
    neg_sent_proportion_pdf : int, default .75
        The percentage of the corpus made of sentences without entities for
        pdfs. -1 to include all sentences.
    neg_sent_proportion_web : int, default .75
        The percentage of the corpus made of sentences without entities for
        web documents or text files. -1 to include all sentences.
    replace_test_terms_with_oov: bool, default False
        Replaces tagged entities in test set(s) with terms not present in the 
        training set. Use to evaluate model performance on unseen entities.
    sent_tokenize_method: str, default 'nltk'
        Available methods: 'nltk', 'spacy'
    use_line_ends_for_pdf_tokenization: bool, default True
        Uses the presence or absence of spaces before newlines
        in text extracted from PDFs to aid tokenization. This method doesn't
        appear to work on extracted text with relatively few spaces before
        newlines, and is automatically disabled on text with fewer than 25%
        of lines ending in spaces. 
    terms_ignore_case_path : str, 
        default 'data/find_terms/tool_names_ignore_case.txt'
        Path to file with terms to match ignoring case (don't have common word 
        aliases).
    terms_keep_case_path : str,
        default 'data/find_terms/tool_names_keep_case.txt'
        Path to file with terms to match case-sensitively.
    """
    if sent_tokenize_method == 'spacy':
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
        'neg_sent_proportion_pdf': neg_sent_proportion_pdf,
        'neg_sent_proportion_web': neg_sent_proportion_web,
        'replace_test_terms_with_oov': replace_test_terms_with_oov,
        'sent_tokenize_method': sent_tokenize_method,
        'use_line_ends_for_pdf_tokenization': use_line_ends_for_pdf_tokenization
    }

    terms_ignore_case_path = terms_ignore_case_path or 'data/find_terms/tool_names_ignore_case.txt'
    terms_keep_case_path = terms_keep_case_path or 'data/find_terms/tool_names_keep_case.txt'
    terms_ignore_case = read_lines(terms_ignore_case_path)
    terms_keep_case = read_lines(terms_keep_case_path)
    term_patterns = make_term_patterns(terms_ignore_case, terms_keep_case)

    folder_names = ('text', 'sentence_tokenized', 'tagged', train_test_dir)
    folders = {}
    for name in folder_names:
        if name is train_test_dir:
            name = 'train_test'
            path = os.path.join(
                output, 'train_test_sets', train_test_dir)
        else:
            path = os.path.join(output, name)
        folders[name] = path
        if not os.path.isdir(path):
            os.makedirs(path, exist_ok=True)
    log_path = os.path.join(output, 'log.json')
    if os.path.isfile(log_path):
        log = load_json(log_path)
    else:
        log = {}

    # Extracts text (and tokenizes sentences from .txt files)
    if input:
        text_files, tokenized_files, tagged_files = os.listdir(
            folders['text']), os.listdir(folders['sentence_tokenized']), os.listdir(folders['tagged'])
        for filename in tqdm(os.listdir(input),
                             desc='Extracting text / tokenizing sentences from input folder',
                             position=0,
                             leave=True):
            file_ref, ext = os.path.splitext(filename)
            if file_ref not in log:
                log[file_ref] = {
                    'type': 'pdf' if ext.lower() == '.pdf' else 'web'}
                json.dump(log, open(log_path, 'w', encoding='utf-8'))
            source_type = log[file_ref]['type']
            if log[file_ref].get('no_terms'):
                continue
            if f'{file_ref}.txt' in text_files + tokenized_files or f'{file_ref}.jsonl' in tagged_files:
                continue
            text = None
            print(filename)
            if ext == '.txt':
                text = read((input, filename))
                if source_type == 'pdf':
                    sents = pdf_utils.sent_tokenize_pdf(
                        text, sent_tokenize, use_line_ends=use_line_ends_for_pdf_tokenization)
                else:
                    sents = sent_tokenize(text)
                write_lines(sents, (folders['sentence_tokenized'], filename))
                continue
            elif source_type == 'pdf':
                text = pdf_utils.pdf_to_txt(
                    os.path.join(input, filename))
            elif source_type == 'web':
                html = read((input, filename))
                text = BeautifulSoup(html, 'lxml').text
            if text:
                write(text, (folders['text'], f'{file_ref}.txt'))

    # Tokenizes sentences from extracted text (PDF and web docs)
    sent_tokenized_files, tagged_files = os.listdir(
        folders['sentence_tokenized']), os.listdir(folders['tagged'])
    for filename in tqdm(os.listdir(folders['text']),
                         desc='Tokenizing sentences from text folder',
                         position=0,
                         leave=True):
        file_ref = os.path.splitext(filename)[0]
        # Uses web doc tokenization for text files manually added to text folder.
        if file_ref not in log:
            log[file_ref] = {
                'type': 'pdf' if ext.lower() == '.pdf' else 'web'}
            json.dump(log, open(log_path, 'w', encoding='utf-8'))
        source_type = log[file_ref]['type']
        if log[file_ref].get('no_terms'):
            continue
        if f'{file_ref}.txt' in sent_tokenized_files or f'{file_ref}.jsonl' in tagged_files:
            continue
        print(filename)
        sents = None
        if source_type == 'pdf':
            sents = pdf_utils.tokenize_doc_from_filepath(
                os.path.join(folders['text'], filename), sent_tokenize,
                use_line_ends=use_line_ends_for_pdf_tokenization)
        elif source_type == 'web':
            text = read(os.path.join(folders['text'], filename))
            sents = sent_tokenize_web_doc(text, sent_tokenize)
        if sents:
            write_lines(sents, (folders['sentence_tokenized'], filename))

    # Tags sentences
    tagged_files = os.listdir(folders['tagged'])
    for filename in tqdm(os.listdir(folders['sentence_tokenized']),
                         desc='Finding terms',
                         position=0,
                         leave=True):
        file_ref = os.path.splitext(filename)[0]
        if log[file_ref].get('no_terms') or f'{file_ref}.jsonl' in tagged_files:
            continue
        print(filename)
        sents = read_lines((folders['sentence_tokenized'], filename))
        sents = set(sents)
        tagged_sents, matched_terms = match_terms_in_sents(
            term_patterns, sents)
        if matched_terms:
            write_lines([json.dumps(sent) for sent in tagged_sents],
                        (folders['tagged'], file_ref + '.jsonl'))
        else:
            log[file_ref]['no_terms'] = True
            json.dump(log, open(log_path, 'w', encoding='utf-8'))

    # Makes train and test sets
    if os.listdir(folders['tagged']):
        sets, summary = make_train_test_sets(
            folders['tagged'],
            args_ref,
            log,
            train_test_split=train_test_split,
            neg_sent_proportion_pdf=neg_sent_proportion_pdf,
            neg_sent_proportion_web=neg_sent_proportion_web,
            dont_filter_sents=dont_filter_sents
        )
        if replace_test_terms_with_oov:
            return_sets = replace_terms_with_oov(
                term_patterns, term_patterns, *sets)
            sets = [set_ for set_ in (
                sets[0], return_sets['test1'], return_sets['test2']) if set_]
        set_labels = {0: 'train', 1: 'dev', 2: 'test'}
        for index, set_ in enumerate(sets):
            text_lines, label_lines = [], []
            for sent in set_:
                text_lines.append(' '.join(sent['text']))
                label_lines.append(' '.join(sent['labels']))
            write_lines(
                text_lines, (folders['train_test'], set_labels[index] + '_text.txt'))
            write_lines(
                label_lines, (folders['train_test'], set_labels[index] + '_labels.txt'))
        # Need to change this for supporting multiple entity types
        write('Term', os.path.join(folders['train_test'], 'types.txt'))
        json.dump(summary, open(os.path.join(
            folders['train_test'], 'corpus_summary.json'), 'w', encoding='utf-8'))
        print('\nCorpus complete.')
