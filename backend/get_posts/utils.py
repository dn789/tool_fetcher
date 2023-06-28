from difflib import SequenceMatcher
import itertools
import re
from statistics import StatisticsError, mean, stdev

from bs4 import BeautifulSoup
from nltk import sent_tokenize, word_tokenize as nltk_word_tokenize
import pandas as pd
from uniseg import wordbreak


def similarity_calc(a, b):
    seq = SequenceMatcher(a=a, b=b)
    return seq.ratio()


def get_web_page_features(url, full_text, full_html, feature_dict, features, old_features=True):
    """Returns feature vector for given web page in order of [features] list."""
    if get_ascii_prop(full_text) < .75:
        word_tokenize = uniseg_word_tokenize
    else:
        word_tokenize = nltk_word_tokenize
    if old_features:
        full_text_tokenized = word_tokenize(full_text)
        soup = BeautifulSoup(full_html, 'lxml')
        elements = soup.find_all()
        feature_dict['word_count'] = len(full_text_tokenized)
        date_match = re.findall(date_time_pattern, full_text)
        feature_dict['date_count'] = len(date_match)
        feature_dict['lexical_diversity'] = round(
            len(set(full_text_tokenized)) / len(full_text_tokenized), 2)
        feature_dict['article_count'] = len(
            [x for x in elements if x.name == 'article'])
        feature_dict['div_count'] = len(
            [x for x in elements if x.name == 'div'])
        lower_full_text_words = [x.lower() for x in full_text_tokenized]
        feature_dict['by_count'] = lower_full_text_words.count('by')
        feature_dict['element_count'] = len(elements)

        post_term_matches_for_url = len(re.findall(
            post_terms_for_url_pattern, url.lower()))
        feature_dict['post_term_count_url'] = post_term_matches_for_url
        feature_dict['post_term_count'] = len(
            re.findall(post_term_pattern, full_html.lower()))

        class_elements = [x for x in elements if x.has_attr('class')]
        class_dict = {}
        for element in class_elements:
            class_str = ' '.join(element['class'])
            class_dict.setdefault(class_str, {'count': 0, 'word_count': 0})
            class_dict[class_str]['count'] += 1
            class_dict[class_str]['word_count'] += len(element.text.split())
        classes_by_count = sorted(
            [(class_str, dict_) for class_str, dict_ in class_dict.items()], key=lambda x: (x[1]['count'], x[1]['word_count']), reverse=True)
        if classes_by_count:
            top_class_list = classes_by_count[0][0].split()
            ele_text_sets = [len(x.text.split())
                             for x in class_elements if x['class'] == top_class_list]
            prop_unique_words_list = []
            for index, text_set in enumerate(ele_text_sets):
                other_text_sets = ele_text_sets[:index] + \
                    ele_text_sets[index + 1:]
                other_text_combined = set().union(*other_text_sets)
                try:
                    prop_unique_words_list.append(
                        len(text_set - other_text_combined) / len(text_set))
                except ZeroDivisionError:
                    pass
            feature_dict['top_class_count'] = classes_by_count[0][1]['count']
            top_3_classes = classes_by_count[:3]
            feature_dict['top_3_class_count'] = round(
                mean(x[1]['count'] for x in top_3_classes), 2)
            feature_dict['top_class_prop_total'] = round(
                classes_by_count[0][1]['word_count'] / len(full_text.split()), 2)
            try:
                feature_dict['top_class_prop_unique_words'] = round(
                    mean(prop_unique_words_list), 2)
            except StatisticsError:
                feature_dict['top_class_prop_unique_words'] = 0
        else:
            feature_dict['top_class_prop_total'] = 0
            feature_dict['top_class_count'] = 0
            feature_dict['top_class_prop_unique_words'] = 0
            feature_dict['top_3_class_count'] = 0
        descendant_counts = []
        for element in elements:
            descendant_counts.append(len([x for x in element.descendants]))
        try:
            feature_dict['mean_descendant_count'] = round(
                mean(descendant_counts), 2)
        except StatisticsError:
            feature_dict['mean_descendant_count'] = 0
    feature_dict = {feature: feature_dict[feature] for feature in features}
    return feature_dict


def get_post_set_features(full_text, full_html, posts_list, feature_dict, features, old_features=True):
    """Returns feature vector for given set of posts in order of [features] list."""
    if get_ascii_prop(full_text) < .75:
        word_tokenize = uniseg_word_tokenize
    else:
        word_tokenize = nltk_word_tokenize
    full_text_tokenized = word_tokenize(full_text)
    posts_tokenized = []
    post_word_counts = []
    post_count = len(posts_list)
    sentence_count = 0
    date_matches = []
    post_term_matches = []
    element_counts = []

    if old_features:
        feature_dict['post_count'] = post_count
        for post_dict in posts_list:
            post = post_dict['post_text']
            element = post_dict['element']
            element_count = len(element.find_all())
            element_counts.append(element_count)
            post_tokenized = word_tokenize(post)
            posts_tokenized.append(post_tokenized)
            post_word_counts.append(len(post_tokenized))

            date_match = set(re.findall(date_time_pattern, post))
            date_matches.append(len(date_match))
            post_term_match = set(re.findall(post_term_pattern, str(element)))
            post_term_matches.append(len(post_term_match))
            sents = sent_tokenize(post)
            sentence_count += len(sents)

        posts_total_word_count = sum(post_word_counts)
        feature_dict['post_text_proportion'] = round(
            posts_total_word_count / len(full_text_tokenized), 2)
        feature_dict['avg_post_word_count'] = round(
            posts_total_word_count / post_count, 2)
        feature_dict['mean_element_count'] = round(
            sum(element_counts) / post_count, 2)

        feature_dict['prop_posts_with_date'] = round(
            len(list(filter(None, date_matches))) / post_count, 2)
        feature_dict['dates_per_post'] = round(
            sum(date_matches) / post_count, 2)
        feature_dict['prop_posts_with_post_term'] = round(
            len(list(filter(None, date_matches))) / post_count, 2)
        feature_dict['post_terms_per_post'] = round(
            sum(date_matches) / post_count, 2)
        feature_dict['avg_sent_length'] = round(
            posts_total_word_count / sentence_count, 2)

        try:
            stdv_word_count = stdev(post_word_counts)
            cv = stdv_word_count / feature_dict['avg_post_word_count']
            feature_dict['cv_post_word_count'] = round(cv, 2)
        except StatisticsError:
            # feature_dict['cv_post_word_count'] = 'n/a'
            feature_dict['cv_post_word_count'] = 0
        # feature_dict['avg_post_similarity'] = avg_p_similarity
        if post_count > 1:

            combinations = itertools.combinations(
                [x['post_text'] for x in posts_list], 2)
            df = pd.DataFrame(list(combinations))
            df['similarity'] = df.apply(
                lambda x: similarity_calc(x[0], x[1]), axis=1)
            feature_dict['avg_post_similarity'] = round(
                df.similarity.mean(), 2)
        else:
            # feature_dict['avg_post_similarity'] = 'n/a'
            feature_dict['avg_post_similarity'] = 1

        all_posts_tokenized = [
            word for post in posts_tokenized for word in post]
        all_posts_word_count = len(all_posts_tokenized)
        feature_dict['lexical_diversity'] = round(len(
            set(all_posts_tokenized)) / all_posts_word_count, 2)

        line_count = sum([len(post['post_text'].split('\n'))
                         for post in posts_list])
        feature_dict['words_per_line'] = round(
            all_posts_word_count / line_count, 2)

    feature_dict = {feature: feature_dict[feature] for feature in features}
    return feature_dict


def uniseg_word_tokenize(text):
    words = list(wordbreak.words(text))
    words = [x for x in words if x.strip()]
    return words


def get_ascii_prop(text):
    ascii_count = len(list(filter(lambda x: 0 <= ord(x) <= 127, text)))
    return ascii_count / len(text)


# Date pattern
alpha_months = [
    'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
    'september', 'october', 'november', 'december'
]
alpha_months.extend([month[:3] for month in alpha_months])
alpha_months.append('sept')
num_months = [str(x) for x in range(1, 13)]
num_months.extend([f'0{str(x)}' for x in range(1, 10)])
month = r'|'.join(sorted(alpha_months + num_months, key=len, reverse=True))
month = rf'(?:{month})'

days = [str(x) for x in range(0, 32)]
days.extend([f'0{str(x)}' for x in range(1, 10)])
days.extend([f'{x}th' for x in days if x[-1]
            not in ('1', '2', '3') or x in ('12', '13')])
days.extend([f'{x}st' for x in days if x.endswith('1')])
days.extend([f'{x}nd' for x in days if x.endswith('2')])
days.extend([f'{x}rd' for x in days if x.endswith('3')])
day = r'|'.join(sorted(days, key=len, reverse=True))
day = rf'(?:{day})'

years = [str(x) for x in range(1900, 2100)]
years.extend([f'0{x}' for x in range(1, 10)])
years.extend([f"{x}" for x in range(10, 100)])
years.extend([f"'0{x}" for x in range(1, 10)])
years.extend([f"'{x}" for x in range(10, 100)])
year = r'|'.join(sorted(years, key=len, reverse=True))
year = rf'(?:{year})'

sep = r'\s*[.\s,/-]\s*'

# Relative pattern
rel_minutes = [rf'{str(x)}{sep}(?:minutes?|mins?.?)' for x in range(1, 60)]
rel_alpha_minutes = [rf'{x}{sep}(?:minutes?|mins?.?)' for x in ['one', 'two', 'three', 'four', 'five',
                                                                'six', 'seven', 'eight', 'nine', 'ten',
                                                                'eleven', 'twelve', 'thirteen', 'fourteen',
                                                                'fifteen', 'sixteen', 'seventeen', 'eighteen',
                                                                'nineteen', 'twenty', 'thirty', 'forty', 'fifty', 'sixty']]
rel_minutes = r'|'.join(rel_minutes + rel_alpha_minutes)

rel_hours = [
    rf'{str(x)}{sep}(?:hours?|hrs?.?)(?:{sep}(?:{rel_minutes}))?' for x in range(1, 24)]
rel_alpha_hours = [rf'{x}{sep}(?:hours?|hrs?.?)(?:{sep}(?:{rel_minutes}))?' for x in ['one', 'two', 'three', 'four', 'five',
                                                                                      'six', 'seven', 'eight', 'nine', 'ten',
                                                                                      'eleven', 'twelve', 'thirteen', 'fourteen',
                                                                                      'fifteen', 'sixteen', 'seventeen', 'eighteen',
                                                                                      'nineteen', 'twenty']]
rel_hours = r'|'.join(rel_hours + rel_alpha_hours)


rel_months = [rf'{str(x)}{sep}months*' for x in range(1, 13)]
rel_alpha_months = [rf'{x}{sep}months*' for x in ['one', 'two', 'three', 'four', 'five',
                                                  'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve']]
rel_months = r'|'.join(rel_months + rel_alpha_months)

rel_days = [rf'{str(x)}{sep}days*' for x in range(1, 32)]
rel_alpha_days = [rf'{x}{sep}days*' for x in ['one', 'two', 'three', 'four', 'five',
                                              'six', 'seven', 'eight', 'nine', 'ten',
                                              'eleven', 'twelve', 'thirteen', 'fourteen',
                                              'fifteen', 'sixteen', 'seventeen', 'eighteen',
                                              'nineteen', 'twenty', 'thirty']]
rel_days = r'|'.join(rel_days + rel_alpha_days)

rel_years = [rf'{str(x)}{sep}years*' for x in range(1, 100)]
rel_alpha_years = [rf'{x}{sep}years*' for x in ['one', 'two', 'three', 'four', 'five',
                                                'six', 'seven', 'eight', 'nine', 'ten',
                                                'eleven', 'twelve', 'thirteen', 'fourteen',
                                                'fifteen', 'sixteen', 'seventeen', 'eighteen',
                                                'nineteen', 'twenty', 'thirty']]
rel_years = r'|'.join(rel_years + rel_alpha_years)

relative_date_pattern = rf'(?:[{rel_days}{rel_months}{rel_years}{rel_hours}{rel_minutes}]){sep}ago'

hours = [str(x) for x in range(1, 24)]
hours.extend([f'0{str(x)}' for x in range(1, 10)])
hour = rf'(?:{"|".join(hours)})'
minutes = [str(x) for x in range(10, 59)]
minutes.extend([f'0{str(x)}' for x in range(1, 10)])
minute = rf'(?:{"|".join(minutes)})'
time_pattern = rf'(?:at(?:{sep})+)?{hour}:{minute}'


date_time_pattern = re.compile(
    rf'(?:{month}{sep}{day}(?:{sep}{year})?(?:{sep}{time_pattern})?)|(?:{day}{sep}{month}(?:{sep}{year})?(?:{sep}{time_pattern})?)|(?:{year}{sep}{month}{sep}{day}(?:{sep}{time_pattern})?)|{relative_date_pattern}|{time_pattern}', re.IGNORECASE)


# Post term pattern
post_terms = '|'.join(['post', 'entry', 'blog', 'article',
                      'story', 'update', 'tags', 'keywords', 'title', 'share', 'twitter', 'whatsapp', 'reddit'])
post_term_pattern = re.compile(rf'{post_terms}', re.IGNORECASE)

post_terms_for_url = '|'.join(
    ['post', 'entry', 'blog', 'article', 'news', 'updates', 'recent', 'stories', 'latest', 'journal'])
post_terms_for_url_pattern = re.compile(
    rf'{post_terms_for_url}', re.IGNORECASE)

if __name__ == '__main__':
    text = '01/25/1997'
    print(re.findall(date_time_pattern, text))
    print(day)
