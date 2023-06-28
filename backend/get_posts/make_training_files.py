from difflib import SequenceMatcher
import itertools
import json
import os
import re
from statistics import StatisticsError, mean, stdev

from bs4 import BeautifulSoup
from nltk import sent_tokenize, word_tokenize as nltk_word_tokenize
import pandas as pd

from get_posts.utils import get_post_set_features, get_web_page_features

FORBIDDEN_CHARS = '<>:"/\\|?*'


def add_samples_to_json(url_json=None):
    """
    Makes reference csv with paths to training data.

    """
    try:
        reference_dict = json.load(
            open('train_reference.json', encoding='utf-8'))
    except FileNotFoundError:
        reference_dict = {}

    for root, dirs, filenames in os.walk('training_data/posts/'):
        for filename in filenames:
            path = os.path.join(root, filename)
            results = json.load(open(path))
            url = results['url']
            name = filename[:-5]
            reference_dict.setdefault(url, {
                'name': name,
                'full_html_path': f'training_data/html/{name}.html',
                'full_text_path': f'training_data/text/{name}.txt'
            })
            reference_dict[url].setdefault('post_set', {
                'valid_post_set': True,
                'features': {},
                'path': path
            })

    for root, dirs, filenames in os.walk('training_data/non-posts/'):
        for filename in filenames:
            path = os.path.join(root, filename)
            results = json.load(open(path))
            url = results['url']
            name = filename[:-5]
            reference_dict.setdefault(url, {
                'name': name,
                'full_html_path': f'training_data/html/{name}.html',
                'full_text_path': f'training_data/text/{name}.txt'
            })
            reference_dict[url].setdefault('non_post_set', {
                'name': filename[:-5],
                'valid_post_set': False,
                'features': {},
                'path': path
            })

    if url_json:
        url_dict = json.load(open(url_json, encoding='utf-8'))
        for url, props in url_dict.items():
            if 'skip' in props:
                continue
            if url not in reference_dict:
                name = '.'.join([x for x in url if x not in FORBIDDEN_CHARS])
                reference_dict[url]['name'] = name
                reference_dict[url]['full_html_path'] = f'training_data/html/{name}.html'
                reference_dict[url]['full_text'] = f'training_data/text/{name}.txt'
                reference_dict[url]['page_with_posts'] = props['page_with_posts']
                reference_dict[url]['web_page_features'] = {}
            elif props['page_with_posts'] in (True, False) and 'page_with_posts' not in reference_dict[url]:
                reference_dict[url]['page_with_posts'] = props['page_with_posts']
                reference_dict[url]['web_page_features'] = {}

    open('train_reference.json', 'w',
         encoding='utf-8').write(json.dumps(reference_dict))


def add_features_to_samples(features, type_='post_set'):
    ref_dict = json.load(open('train_reference.json', encoding='utf-8'))
    try:
        temp_file = open('make_training_files_temp.txt',
                         encoding='utf-8').read().strip().split('\n')
        already_processed = [line.split('\t')[0] for line in temp_file]
    except FileNotFoundError:
        already_processed = []
    for url, props in ref_dict.items():
        if url in already_processed:
            continue
        if type_ == 'web_page' and 'web_page_features' not in props:
            continue
        print(f'Processing {url}')
        if type_ == 'post_set':
            if 'post_set' not in props and 'non_post_set' not in props:
                continue
            try:
                full_text = open(props['full_text_path'],
                                 encoding='utf-8').read()
                full_html = open(props['full_html_path'],
                                 encoding='utf-8').read()
            except FileNotFoundError:
                open('to_delete.txt', 'a').write(url + '\n')
                continue
            for k in ('post_set', 'non_post_set'):
                if k in props and props[k]:
                    feature_dict = props[k]['features']
                    try:
                        posts_dict = json.load(
                            open(props[k]['path'], encoding='utf-8'))
                    except FileNotFoundError:
                        open('to_delete.txt', 'a').write(url + '\t' + k + '\n')
                        continue
                    posts_list = posts_dict['posts']
                    if set(features) - set(feature_dict.keys()):
                        old_features = False if feature_dict else True
                        feature_dict = get_post_set_features(
                            full_text, full_html, posts_list, feature_dict, features, old_features=old_features)
                        props[k]['features'] = feature_dict

            open('make_training_files_temp.txt', 'a',
                 encoding='utf-8').write(f'{url}\t{props}' + '\n')
        elif type_ == 'web_page':
            try:
                full_text = open(props['full_text_path'],
                                 encoding='utf-8').read()
                full_html = open(props['full_html_path'],
                                 encoding='utf-8').read()
            except FileNotFoundError:
                open('to_delete.txt', 'a').write(url + '\n')
                continue

            feature_dict = props['web_page_features']
            if set(features) - set(feature_dict.keys()):
                old_features = False if feature_dict else True
                feature_dict = get_web_page_features(
                    url, full_text, full_html, feature_dict, features, old_features=old_features)
                props['web_page_features'].update(feature_dict)
                open('make_training_files_temp.txt', 'a',
                     encoding='utf-8').write(f'{url}\t{props}' + '\n')

    for line in open('make_training_files_temp.txt', encoding='utf-8').read().strip().split('\n'):
        path, sample = line.split('\t')
        sample = eval(sample)
        ref_dict.update({path: sample})
    open('train_reference.json', 'w',
         encoding='utf-8').write(json.dumps(ref_dict))
    os.remove('make_training_files_temp.txt')


def make_csv(json_path, features, output_path, type_='post_set'):
    examples = json.load(open(json_path, encoding='utf-8'))
    csv = open(output_path, 'w', encoding='utf-8')
    if type_ == 'post_set':
        csv.write('valid_post_set,' + ','.join(features) + '\n')
    elif type_ == 'web_page':
        csv.write('page_with_posts,' + ','.join(features) + '\n')
    for url, props in examples.items():
        if type_ == 'web_page':
            if 'web_page_features' not in props:
                continue
            feature_dict = props['web_page_features']
            feature_types = [type(x) for x in feature_dict.values()]
            if str in feature_types or not feature_types:
                continue
            page_with_posts = 1 if props['page_with_posts'] else 0
            csv.write(f'{page_with_posts},' + ','.join(str(feature_dict[feature])
                                                       for feature in features) + '\n')
        elif type_ == 'post_set':
            for k in ('post_set', 'non_post_set'):
                if k in props and props[k]:
                    sample = props[k]
                    feature_dict = sample['features']
                    feature_types = [type(x) for x in feature_dict.values()]
                    if str in feature_types or not feature_types:
                        continue
                    valid_post_set = 1 if sample['valid_post_set'] else 0
                    csv.write(f'{valid_post_set},' + ','.join(str(feature_dict[feature])
                                                              for feature in features) + '\n')


def delete_web_page_features_from_train_ref(features):
    json_ = json.load(open('train_reference.json', encoding='utf-8'))
    for url, dict_ in json_.items():
        if 'web_page_features' in dict_:
            for feature in features:
                dict_['web_page_features'].pop(feature)
    open('train_reference.json', 'w', encoding='utf-8').write(json.dumps(json_))


def clear_features(ref_json):
    train_ref = json.load(open(ref_json, encoding='utf-8'))
    for url, props in train_ref.items():
        for k in ('post_set', 'non_post_set'):
            if k in props:
                props[k]['features'] = {}
    open('./train_reference.json', 'w',
         encoding='utf-8').write(json.dumps(train_ref))


def move_data_to_test(count):
    web_app_json = json.load(
        open('web_app_results_train.json', encoding='utf-8'))
    to_move = []
    processed = 0
    for url, dict_ in web_app_json.items():
        if dict_['page_with_posts'] is None:
            processed += 1
            to_move.append(url)
            if processed == count:
                break
    new_dict = {}
    for url in to_move:
        dict_ = web_app_json.pop(url)
        new_dict[url] = dict_
        name = ''.join([x for x in url if x not in FORBIDDEN_CHARS])
        os.rename(f'training_data/html/{name}.html',
                  f'test_data/html/{name}.html')
        os.rename(f'training_data/text/{name}.txt',
                  f'test_data/text/{name}.txt')
    open('web_app_results_test.json', 'w',
         encoding='utf-8').write(json.dumps(new_dict))
    open('web_app_results_train.json', 'w',
         encoding='utf-8').write(json.dumps(web_app_json))


post_set_features = [
    'post_text_proportion',
    'avg_post_word_count',
    'prop_posts_with_date',
    'dates_per_post',
    'prop_posts_with_post_term',
    'post_terms_per_post',
    'avg_sent_length',
    'cv_post_word_count',
    'avg_post_similarity',
    'lexical_diversity',
    'words_per_line',
    'mean_element_count',
    'post_count'
]

web_page_features = [
    'word_count',
    'date_count',
    'post_term_count',
    'lexical_diversity',
    'article_count',
    'div_count',
    'by_count',
    'element_count',
    'post_term_count_url',
    'top_class_count',
    'top_3_class_count',
    'top_class_prop_total',
    'top_class_prop_unique_words',
    'mean_descendant_count'
]


if __name__ == '__main__':

    # delete_web_page_features_from_train_ref(
    #     ['top_class_prop_unique_words'])

    # add_samples_to_json()

    # add_features_to_samples(web_page_features, type_='web_page')

    make_csv('train_reference.json', web_page_features,
             'training_web_pages_new.csv', type_='web_page')
