"""
Utility functions
"""
import json
import os
import random
import re


PUNCT = ',;:\'‘’"“”()[]{}\\/|'
PUNCT_PATTERN = rf'({"|".join([re.escape(char) for char in PUNCT])}|[.!?]+$)'


def get_alpha_prop(sent):
    total, alnum_count = 0, 0
    for char in sent:
        if char.strip():
            total += 1
            if char.isalnum():
                alnum_count += 1
    if not total:
        return
    return alnum_count / total


def get_terms_from_tagged_sents(tagged_sents):
    terms = []
    for sent in tagged_sents:
        if type(sent['text']) == str:
            sent['text'] = sent['text'].split()
        if type(sent['labels']) == str:
            sent['labels'] = sent['labels'].split()
        last_index = len(sent['labels']) - 1
        current_term = []
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


def load_json(path):
    if type(path) != str:
        path = os.path.join(*[x for x in path])
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


def remove_terms_from_corpus(terms, folder, output_folder=None, n=None):
    """
    Removes n sentences containing each term in terms from train/test sets
    in folder and updates summary.

    Parameters
    ----------
    terms : list
    folder : str
    output_folder : str, optional
        Specify output_folder to avoid overwriting corpus files. 
    n : int, optional
        Removes this number of sentences containing each term, for each term. 
        If None, removes all sentences containing each term. 
    """
    terms = set(terms)
    filenames = os.listdir(folder)
    if 'corpus_summary.json' in filenames:
        corpus_summary = load_json((folder, 'corpus_summary.json'))
    else:
        corpus_summary = {'corpus': {}}
    totals = corpus_summary['corpus']['total'] = {
        'sent_count': 0,
        'word_count': 0,
        'terms': {}
    }
    remove_counts = {term: 0 for term in terms}
    prefixes = set([filename.split('_')[0]
                    for filename in filenames])
    sets_and_counts = {prefix: 0 for prefix in prefixes if prefix in (
        'train', 'test', 'dev')}

    if output_folder:
        os.makedirs(output_folder, exist_ok=True)
    else:
        output_folder = folder
    sent_dicts_to_keep = []
    for set_name in sets_and_counts:
        sents = read_lines(os.path.join(folder, set_name + '_text.txt'))
        labels = read_lines(os.path.join(folder, set_name + '_labels.txt'))
        for sent, label_line in zip(sents, labels):
            sets_and_counts[set_name] += 1
            sent_dict = {'text': sent, 'labels': label_line}
            terms_from_sent = set(get_terms_from_tagged_sents([sent_dict]))
            matches = terms & terms_from_sent
            if matches:
                for match in matches:
                    remove_counts[match] += 1
                    if n and remove_counts[match] >= n:
                        remove_counts.pop(match)
            else:
                totals['sent_count'] += 1
                totals['word_count'] += len(sent.split())
                for term in terms_from_sent:
                    totals['terms'].setdefault(term, 0)
                    totals['terms'][term] += 1
                sent_dicts_to_keep.append(sent_dict)

    ranked_term_counts = sorted(
        totals['terms'].items(), key=lambda x: x[1], reverse=True)
    totals['terms'] = {
        term: count for term, count in ranked_term_counts}

    json.dump(corpus_summary, open(os.path.join(output_folder,
              'corpus_summary.json'), 'w', encoding='utf-8'))

    old_sent_count = sum(sets_and_counts.values())
    sets_and_proportions = {}
    for set_name, count in sets_and_counts.items():
        sets_and_proportions[set_name] = round(count / old_sent_count, 2)
    random.shuffle(sent_dicts_to_keep)
    last_index = 0
    for index, (set_name, proportion) in enumerate(sets_and_proportions.items()):
        count = round(len(sent_dicts_to_keep) * proportion)
        sent_dics_for_set = []
        if index == len(sets_and_proportions) - 1:
            sent_dics_for_set.extend(sent_dicts_to_keep[last_index:])
        else:
            sent_dics_for_set.extend(
                sent_dicts_to_keep[last_index:last_index + count])
            last_index += count
        keep_sents, keep_labels = [], []
        for sent_dict in sent_dics_for_set:
            keep_sents.append(' '.join(sent_dict['text']))
            keep_labels.append(' '.join(sent_dict['labels']))
        assert len(keep_sents) == len(keep_labels)
        write_lines(keep_sents, (output_folder, set_name + '_text.txt'))
        write_lines(keep_labels, (output_folder, set_name + '_labels.txt'))


def get_term_counts_in_corpus(corpus_dir, case_sensitive=False, print_counts=True):
    terms_dict = {}
    prefixes = set([filename.split('_')[0]
                    for filename in os.listdir(corpus_dir)])
    sets = [prefix for prefix in prefixes if prefix in (
        'train', 'test', 'dev')]
    for set_name in sets:
        sent_dicts = []
        sents = read_lines((corpus_dir, f'{set_name}_text.txt'))
        labels = read_lines((corpus_dir, f'{set_name}_labels.txt'))
        for sent, label in zip(sents, labels):
            sent_dicts.append({'text': sent.split(), 'labels': label.split()})
        terms = get_terms_from_tagged_sents(sent_dicts)
        for term in terms:
            if not case_sensitive:
                term = term.lower()
            terms_dict[term] = terms_dict.setdefault(term, 0) + 1
    ranked_terms = sorted(terms_dict.items(), key=lambda x: x[1], reverse=True)
    if print_counts:
        print('term\t\tcount')
        for term, count in ranked_terms:
            print(term, '\t\t', count)
    return ranked_terms
