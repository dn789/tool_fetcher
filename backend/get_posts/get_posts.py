"""
Auomatically extracts post/article previews from a url.

get_posts: Tries various methods (including element method) until the 
    classifier finds a valid post set. 

get_posts_element_method_only: Tries to get posts from elements containing
    dates or terms related to posts until the classifier finds a valid post 
    set. 

"""
import re
import requests
from statistics import multimode
import urllib.parse

from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from dateutil.parser._parser import ParserError
from func_timeout import func_timeout, FunctionTimedOut
import newspaper
from trafilatura import feeds as t_feeds, extract as t_extract

from get_posts.utils import date_time_pattern, post_term_pattern

BLOG_LINK_TERMS = set([
    'recent',
    'latest',
    'updates',
    'posts',
    'blog',
    'news'
])

HEADING_TAGS = ['h1', 'h2', 'h3']


def normalize_url(url, root_to_join=None):
    """
    Removes query string and scheme from url and joins it with root_to_join if 
    given.
    """
    url = urllib.parse.urlunsplit(urllib.parse.urlsplit(
        url)._replace(query="", fragment=""))
    if root_to_join:
        url = urllib.parse.urljoin(root_to_join, url)
    if '//' in url:
        url = url.split('//', maxsplit=1)[1]
    url = url.strip('/')
    url = url.lstrip('www.')
    return url


def clean_post(post_dict, trim):
    """Gets rid of extraneous spaces and newline characters."""
    heading_ele = post_dict['element'].find(HEADING_TAGS)
    if not heading_ele:
        heading_ele = post_dict['element'].find(
            lambda tag: tag.has_attr('class') and 'title' in ' '.join(tag['class']))
    if not heading_ele:
        if post_dict['element'].name == 'a':
            heading_ele = post_dict['element']
    if heading_ele:
        post_dict['title'] = heading_ele.text
        heading_ele.decompose()
    prelim_post = list(post_dict['element'].stripped_strings)
    # post = post[:trim] if trim else post
    word_count = 0
    if trim:
        post = []
        for line in prelim_post:
            words = line.split()
            word_count += len(words)
            if word_count > trim:
                post.append(' '.join(words[:word_count - trim]))
                break
            else:
                post.append(line)
    else:
        post = prelim_post
    if not any(post) and 'title' not in post_dict:
        post = ['No post text.']
    post_dict['post'] = post


def _get_posts_from_anchors(anchor_dict):
    """
    Uses anchors to find posts, first by looking for non-uniform text in the 
    anchors, then travelling up the tree until parents with non-uniform text 
    are found, then returns the parents' text and anchor urls.

    Parameters
    ----------
    anchor_dict : dict
        dictionary from get_urls_from_post_feeds

    Returns
    -------
    list of dictionaries (posts): 
        {
            'post': post text (str), 
            'url': post url (str), 
            'element': element corresponding to post (bs4.element.Tag)
            'dates': date_time_pattern matches in post text (list)
            }
    """
    # If no unique text is found in anchors, goes up the parent tree.
    if len(set([anchor_dict[anchor]['parents_text'] for anchor in anchor_dict])) <= 1:
        while True:
            parent_text_set = set()
            try:
                for anchor in anchor_dict:
                    # If there's only one anchor, stops as soon as any text is found.
                    # NOTE: Maybe require each post to have unique text.
                    if len(anchor_dict) == 1 and anchor_dict[anchor]['parents_text']:
                        raise StopIteration
                    next_parent = next(
                        anchor_dict[anchor]['parents'])
                    next_parent_text = next_parent.text.strip()
                    parent_text_set.add(next_parent_text)
                    anchor_dict[anchor]['parents_text'] = next_parent_text
                    anchor_dict[anchor]['element'] = next_parent
            except StopIteration:
                # If StopIteration is raised when there's more than one anchor,
                # the page probably has very few elements and would be
                # difficult to extract posts from using any of these methods.
                # NOTE: Handle overlapping posts.
                if len(anchor_dict) > 1:
                    return []
                break
            # Stops when the posts don't all have the same text.
            if len(parent_text_set) > 1:
                break

    post_dict_list = []
    for anchor, props in anchor_dict.items():
        post_dict = {}
        post_dict['post_text'] = props['parents_text']
        post_dict['url'] = props['normalized_url']
        post_dict['element'] = props['element']
        post_dict['dates'] = re.findall(
            date_time_pattern, post_dict['post_text'])
        post_dict_list.append(post_dict)
    return post_dict_list


def _get_posts_from_feed_urls(feed_urls, body, root_url, root_scheme):
    """
    Gets posts from first [n-posts] urls from feed_urls found in html, excluding ones that
    aren't/probably aren't posts (root_url, urls found in headers, etc.)

    Parameters
    ----------
    feed_urls : list
    body : bs4.element.Tag
    n_posts: int
    root_url : str
    root_scheme: str

    Returns
    -------
    list of dictionaries (posts): 
        {
            'post': post text (str), 
            'url': post url (str), 
            'element': element corresponding to post (bs4.element.Tag)
            'dates': date_time_pattern matches in post text (list)
            }
    """
    norm_root_url = normalize_url(root_url)
    feed_urls = [normalize_url(
        url) for url in feed_urls if url != norm_root_url and not url.endswith('.xml')]
    excluded_elements = ()
    post_urls = set()
    anchor_dict = {}
    body_anchors = body.find_all('a', href=True)
    for anchor in body_anchors:
        url = normalize_url(anchor['href'], root_to_join=root_url)
        if url != root_url:
            for parent in anchor.parents:
                if parent.name in excluded_elements:
                    break
            else:
                if url in feed_urls and url not in post_urls:
                    # Create dictionary for each anchor containing parent elements (to
                    # find parent text) and a normalized url that will be returned with
                    # each post.
                    post_urls.add(url)
                    anchor_dict[anchor] = {
                        'normalized_url': root_scheme + '://' + url,
                        'parents': anchor.parents,
                        'parents_text': anchor.text.strip(),
                        'element': anchor}
    if anchor_dict:
        post_dict_list = _get_posts_from_anchors(
            anchor_dict)
    else:
        post_dict_list = None
    return post_dict_list


def _get_posts_from_elements(elements, root_url):
    """
        Parameters
    ----------
    elements : list of bs4.element.Tag
    trim : int
    root_url : str
    clean_posts: bool

    Returns
    -------
    list of dictionaries (posts): 
        {
            'post': post text (str), 
            'url': post url (str), 
            'element': element corresponding to post (bs4.element.Tag)
            'dates': date_time_pattern matches in post text (list)
            }
    """

    element_dict = {}
    for element in elements:
        anchors = element.find_all('a', href=True)
        if anchors:
            urls = set([urllib.parse.urljoin(root_url, anchor['href'])
                       for anchor in anchors])
        else:
            urls = set()
        if anchor_parent := element.find_parent('a', href=True):
            urls = set([urllib.parse.urljoin(root_url, anchor_parent['href'])])

        # element_dict[element] = {'parents': element.parents,
        #                          'text': element.text if not anchor_parent else anchor_parent.text,
        #                          'urls': urls,
        #                          'return_element': element
        #                          }

        element_dict[element] = {'parents': element.parents,
                                 'text': element.text if not anchor_parent else anchor_parent.text,
                                 'urls': urls,
                                 'return_element': element
                                 }

    while True:
        post_text_set = set([element_dict[element]['text']
                             for element in element_dict])
        url_set = set()
        for element, dict in element_dict.items():
            url_set.update(dict['urls'])
        all_have_url = all([element_dict[element]['urls']
                           for element in element_dict])
        # NOTE: Use better criteria here for getting all post content.
        if len(post_text_set) > 1 and len(url_set) > 1 and all_have_url:
            break
        elif len(elements) == 1 and url_set and post_text_set:
            break
        try:
            for element, props in element_dict.items():
                next_parent = next(props['parents'])
                props['return_element'] = next_parent
                props['text'] = next_parent.text.strip()
                anchors = next_parent.find_all('a', href=True)
                if anchors:
                    props['urls'].update([urllib.parse.urljoin(
                        root_url, anchor['href']) for anchor in anchors])
        except StopIteration:
            return []

    mode_urls = multimode(url_set)
    if len(mode_urls) == len(url_set):
        mode_urls = ()

    post_dict_list = []
    for element, props in element_dict.items():
        overlap = None
        descendents = [x for x in props['return_element'].descendants]
        for other_ele, other_props in element_dict.items():
            if other_props['return_element'] in descendents:
                overlap = True
                break
        if overlap:
            continue
        post_dict = {}
        # Picks the longest url in the element that's not in mode_urls.
        post_dict['url'] = max(
            [url for url in props['urls'] if url not in mode_urls], key=len)
        post_dict['post_text'] = props['text']
        post_dict['element'] = props['return_element']
        post_dict['dates'] = re.findall(
            date_time_pattern, post_dict['post_text'])
        post_dict_list.append(post_dict)
    return post_dict_list


def _element_method(html, text, soup, root_url, classifier=None, print_status=False, force_return=False, backup=True):
    """
    Parameters
    ----------
    html: str
    soup : bs4.BeautifulSoup
    root_url: str

    Returns
    -------
    list of dictionaries (posts): 
        {
            'post': post text (str), 
            'url': post url (str), 
            'element': element corresponding to post (bs4.element.Tag)
            'dates': date_time_pattern matches in post text (list)
            }
    """
    elements = [ele for ele in soup.find_all() if ele.has_attr('class')]
    classes = {}
    for element in elements:
        class_str = ' '.join(element['class'])
        classes.setdefault(
            class_str, {
                'count': 0,
                'word_count': 0,
                'has_date': [],
                'has_post_term': [],
                'class_has_post_term': bool(re.findall(post_term_pattern, class_str))
            })
        classes[class_str]['count'] += 1
        element_str = str(element)

        # Date match
        # Exclude date matches in anchors
        element_str = re.sub(r'<a.+href=".+?>', '', element_str)
        element_str = re.sub(r'<svg.+?</svg>', '', element_str)
        date_match = re.findall(date_time_pattern, element_str)
        if date_match:
            date = date_match[0]
            classes[class_str]['word_count'] += len(
                element.text.replace(date, '').split())
        else:
            classes[class_str]['word_count'] += len(element.text.split())
        classes[class_str]['has_date'].append(bool(date_match))

        # Post term match (looks for a matching pattern in all descendants' classes)
        if not classes[class_str]['class_has_post_term']:
            if re.findall(post_term_pattern, class_str):
                post_term_match = True
            else:
                post_term_match = False
                for descendant in element.find_all():
                    if descendant.has_attr('class') and re.findall(post_term_pattern, ' '.join(descendant['class'])):
                        post_term_match = True
                        break
            classes[class_str]['has_post_term'].append(post_term_match)

    for class_str, properties in classes.items():
        properties.update(
            {
                'all_have_date': all(properties['has_date']),
                'all_have_post_term': properties['class_has_post_term'] or all(properties['has_post_term']),
                'avg_word_count': properties['word_count'] / properties['count']
            })

    top_date_class, top_post_term_class = {
        'class': None, 'count': None}, {'class': None, 'count': None}

    # Gets classes with dates in each member and sorts by frequency,
    # then average word count.
    ranked_by_date = sorted(
        [x for x in classes.items() if x[1]['all_have_date']],
        key=lambda x: (x[1]['all_have_date'], x[1]['count'], x[1]['avg_word_count']), reverse=True)

    if ranked_by_date:
        top_date_class = {
            'class': ranked_by_date[0][0].split(), 'count': ranked_by_date[0][1]['count']}

    # Gets class with post terms in its class or descendants in each member and
    # sorts by frequency, then average word count.
    ranked_by_post_term = sorted(
        [x for x in classes.items() if x[1]['all_have_post_term']],
        key=lambda x: (x[1]['all_have_post_term'], x[1]['count'], x[1]['avg_word_count']), reverse=True)
    if ranked_by_post_term:
        top_post_term_class = {
            'class': ranked_by_post_term[0][0].split(), 'count': ranked_by_post_term[0][1]['count']}

    # If the top frequency for any of the ranked class lists is 1, selects the
    # class whose word count (equal to the average word count since there's
    # only one member) is# closest to half the total word count of the page
    # (Might need to tweak this).
    if top_date_class['count'] == 1:
        target_word_count = len(text.split()) / 2
        distance_to_target = {}
        for class_str, props in ranked_by_date:
            distance_to_target[class_str] = abs(
                props['avg_word_count'] - target_word_count)
        class_str = sorted(
            distance_to_target.items(), key=lambda x: x[1])[0][0]
        top_date_class = {'class': class_str.split(
        ), 'count': 1}

    if top_post_term_class['count'] == 1:
        target_word_count = len(text.split()) / 2
        distance_to_target = {}
        for class_str, props in ranked_by_post_term:
            distance_to_target[class_str] = abs(
                props['avg_word_count'] - target_word_count)
        class_str = sorted(
            distance_to_target.items(), key=lambda x: x[1])[0][0]
        top_post_term_class = {'class': class_str.split(
        ), 'count': 1}

    if print_status:
        print(
            f'top date class: {top_date_class["class"]}, count: {top_date_class["count"]}')
        print(
            f'top post term class: {top_post_term_class["class"]}, count: {top_post_term_class["count"]}')

    # Tries each of the two target classes (if they exist). Tries the date
    # class first, unless its frequency is 1 and the post term class' frequency
    # is > 1.
    classes_to_try = list(filter(lambda x: x['count'], [
                          top_date_class, top_post_term_class]))
    if not classes_to_try:
        return
    if top_date_class['class'] == top_post_term_class['class']:
        class_to_try = [classes_to_try[0]]
    if top_date_class['count'] == 1 and top_date_class['count'] > 1:
        classes_to_try = reversed(classes_to_try)

    posts, pred = None, None
    for class_to_try in classes_to_try:
        if print_status:
            print(f'Trying class {class_to_try["class"]} ...')
        class_elements = [
            ele for ele in elements if ele['class'] == class_to_try['class']]
        post_elements = []
        for element in class_elements:
            descendents = [x for x in element.descendants]
            for other_ele in class_elements:
                if other_ele in descendents:
                    break
            else:
                post_elements.append(element)
        posts = _get_posts_from_elements(
            post_elements, root_url)
        if posts and all(x['post_text'] for x in posts):
            pred = rate_posts(None, html, text, posts, classifier)
            if pred:
                if force_return:
                    return posts, pred
                return posts

    if not backup:
        return
    # Backup method. Tries elements without classes.
    element_dict = {}
    elements = [ele for ele in soup.find_all() if ele.name not in (
        'body', 'html', 'header')]
    for index, element in enumerate(elements):
        element_dict.setdefault(element.parent, {})
        element_dict[element.parent].setdefault(element.name, [])
        element_dict[element.parent][element.name].append(index)

    candidate_elements = []
    for parent, names in element_dict.items():
        for name in names:
            date_matches = 0
            if len(names[name]) < 5:
                continue
            soup_indices = [x for x in names[name]]
            for soup_index in soup_indices:
                date_matches += (1 if re.findall(date_time_pattern,
                                 elements[soup_index].text) else 0)
            if date_matches == len(soup_indices):
                candidate_elements.append(soup_indices)
    if candidate_elements:
        candidate_elements.sort(key=len, reverse=True)
        post_elements = [elements[index] for index in candidate_elements[0]]
        posts = _get_posts_from_elements(
            post_elements, root_url)
        if posts and all(x['post_text'] for x in posts):
            pred = rate_posts(None, html, text, posts, classifier)
            if pred:
                if force_return:
                    return posts, pred
                return posts
    if force_return:
        return posts, pred


def rate_posts(url, html, text, posts, classifier):
    pred = classifier.predict(url, html, text, posts)
    pred = True if pred == 1 else False
    return pred


def get_pages(start_url, look_for_blog=True):
    # Handle redirect
    try:
        r = requests.get(start_url)
    except Exception as ex:
        r = None
    if not r or r.status_code != 200:
        try:
            html = newspaper.build(start_url).html
        except Exception as ex:
            return
    else:
        html = r.text
    start_domain = urllib.parse.urlparse(start_url).netloc
    if html:
        start_page = {'html': html, 'url': start_url}
        if look_for_blog:
            soup = BeautifulSoup(html, 'lxml')
            links = soup.find_all('a', href=True)
            collected_urls, same_domain_pages, diff_domain_pages = [], [], []
            for link in links:
                url = link['href']
                link_words = set([x.lower() for x in link.text.split()])
                if link_words.intersection(BLOG_LINK_TERMS):
                    url = urllib.parse.urljoin(start_url, url)
                    if url not in collected_urls:
                        domain = urllib.parse.urlparse(url).netloc
                        if domain != start_domain:
                            if len(diff_domain_pages) == 3:
                                continue
                            to_add = diff_domain_pages
                        else:
                            to_add = same_domain_pages
                        try:
                            r = requests.get(url)
                        except Exception as ex:
                            r = None
                        if not r or r.status_code != 200:
                            try:
                                html = newspaper.build(url).html
                            except Exception as ex:
                                continue
                        else:
                            html = r.text
                        collected_urls.append(url)
                        page_to_try = {'html': html, 'url': url}
                        to_add.append(page_to_try)

                if len(same_domain_pages) == 3:
                    break
        same_domain_pages.reverse()
        diff_domain_pages.reverse()
        num_to_add = 3 - len(same_domain_pages)
        pages_to_try = same_domain_pages + \
            diff_domain_pages[:num_to_add] + [start_page]
        print('Pages to try for get_posts:')
        for x in pages_to_try:
            print(x['url'])
        return pages_to_try


def prepare_posts(posts, max_posts, trim, clean_posts, root_url, method, valid=True, full_text=False):
    """
    Finds a date for each post by finding a common date format in all posts, 
    standardized dates (str representation of datetime.datetime object), and 
    cleans post text.

    Parameters
    ----------
    posts : list of dictionaries
    max_posts : None or int
    trim : None or int
    clean_posts : bool
    root_url : str
    method : str
    valid : bool, optional
    full_text : bool, optional

    Returns
    -------
    dict
        See return of get_posts or get_posts_element_method_only.
    """
    if max_posts:
        posts = posts[:max_posts]

    date_dict = {}
    for index, post_dict in enumerate(posts):
        for date in post_dict['dates']:
            pattern = ''.join([x for x in date if not x.isalnum()])
            date_dict.setdefault(pattern, {})
            date_dict[pattern].setdefault(index, [])
            try:
                date_dict[pattern][index].append(
                    {'original': date, 'parsed': date_parser.parse(date)})
            except ParserError:
                # Need to handle relative dates here
                continue
    top_date_patterns = [pattern for pattern in date_dict if all(
        [index in date_dict[pattern] and date_dict[pattern][index] for index in range(len(posts))])]
    if top_date_patterns:
        target_date_pattern = sorted(top_date_patterns)[-1]
    else:
        target_date_pattern = None

    for index, post_dict in enumerate(posts):
        if clean_posts:
            clean_post(post_dict, trim)
            # heading_ele = post_dict['element'].find(heading_tags)
            # if not heading_ele:
            #     heading_ele = post_dict['element'].find(
            #         lambda tag: tag.has_attr('class') and 'title' in ' '.join(tag['class']))
            # if not heading_ele:
            #     if post_dict['element'].name == 'a':
            #         heading_ele = post_dict['element']
            # if heading_ele:
            #     post_dict['title'] = heading_ele.text
            #     heading_ele.decompose()
            # post = '\n'.join(
            #     post_dict['element'].stripped_strings).replace('\r', '\n')
            # post = post[:trim] if trim else post
            # post_dict['post'] = post
        if target_date_pattern:
            post_dict['date'] = str(sorted(
                date_dict[target_date_pattern][index], key=lambda x: len(x['original']))[-1]['parsed'])
        else:
            post_dict['date'] = None
        post_dict.pop('element')
        post_dict.pop('dates')
        post_dict.pop('post_text')

    return_dict = {'method': method, 'valid_post_set': valid,
                   'posts': posts, 'url': root_url}
    if full_text:
        return_dict.update({'full_text': full_text})
    return return_dict


def get_posts_element_method_only(url, html=None, max_posts=5, trim=30, clean_posts=True, full_text=False, classifier=None):
    """
    Gets posts by searching for elements with dates or post-related terms. 
    Tries various candidate post sets until the classifier finds a valid one.

    Parameters
    ----------
    url : str
    html: str
    max_posts : int
        Number of posts to extract.
    trim : int, optional
        Number of words to trim each post to (only works if clean_posts is True), 
        by default 30
    full_text: bool, optional
        Includes extracted text of url in return.

    Returns
    -------
    dict
         - If 'error' is in return, there will be no other keys. 

        {  
            'error': description of error type (str),
            'method' : 'class-based',
            'valid_post_set': classifier prediction (bool),
            'posts': list of posts (dict):
                {
                'post': post text (str), 
                'url': post url (str), 
                'date': post date, in str representation of datetime.datetime 
                    object (str)
                }
            'full_text': extracted text of url (str)
        }
    """
    if not html:
        error_type = 'Page not found.'
        pages_to_try = None
        try:
            pages_to_try = func_timeout(20, get_pages, args=(url, False))
        except FunctionTimedOut:
            error_type = 'Page timed out.'
        if not pages_to_try:
            return {'error': error_type}
    else:
        pages_to_try = [{'html': html, 'url': url}]

    for page in pages_to_try:
        root_url = page['url']
        html = page['html']
        soup = BeautifulSoup(html, 'lxml')
        text = soup.text
        post_args = (max_posts, trim, clean_posts, root_url)

        if soup:
            results = _element_method(html, text,
                                      soup, root_url, classifier, force_return=True)
            if results:
                posts, pred = results
                if posts:
                    full_text = text if full_text else None
                    return prepare_posts(posts, *post_args, method='class-based', valid=pred, full_text=full_text)


def get_posts(url, html=None, max_posts=5, trim=30, clean_posts=True, classifier=None, print_status=False, look_for_blog=True):
    """
    Tries various methods in the following order, stopping when the classifier 
    finds a valid post set. 

    1) Uses article elements as post candidates if at least 2 are on the page.
    2) Uses feeds (trafilatura, then newspaper) to find urls on the page, then
        gets post candidates from their anchor elements. 
    3) Uses the _element_method. 
    4) If above methods fail, returns 'main content' of page extracted using 
        trafilatura.

    Parameters
    ----------
    url : str
        URL to search for posts
    html : str, optional
        HTML to search for posts (will use instead of url if provided), by default None
    max_posts : int, optional
        Maximum number of posts to return, by default 5
    trim : int, optional
        Number of words to trim each post to (only works if clean_posts is True), 
        by default 30
    clean_posts : bool, optional
        Eliminates extraneous spaces/newlines from post (done before trim), by default True
    classifier : sklearn RandomForestClassifier, optional
        Clasifier for post sets. Used on each potential result until a valid post set is
        found or all methods are exhausted, by default None

    Returns
    -------
    dict
        - If 'error' is in return, there will be no other keys. 
        - 'posts' will be in return only if 'valid_post_set' is True. 
        - 'main_content' will be in return only if 'method' is 'main_content'
            ('posts' will not be in return)

        {
            'error': description of error type (str),
            'method': method used to get returned post set (str),
            'valid_post_set': classifier prediction (bool),
            'url': url of the page the posts were extracted from (str),
            'posts': list of posts (dict):
                {
                'post': post text (str), 
                'url': post url (str), 
                'date': post date, in str representation of datetime.datetime 
                    object (str)
                }
            'main_content': extracted main content of page (str)
        }
    """
    if not html:
        error_type = 'Page not found.'
        pages_to_try = None
        try:
            pages_to_try = func_timeout(
                20, get_pages, args=(url, look_for_blog))
        except FunctionTimedOut:
            error_type = 'Page timed out.'
        if not pages_to_try:
            return {'error': error_type}
    else:
        pages_to_try = [{'html': html, 'url': url}]

    for index, page in enumerate(pages_to_try):
        html, root_url = page['html'], page['url']
        if not html.strip():
            continue
        root_scheme = root_url.split('://')[0]
        soup = BeautifulSoup(html, 'lxml')
        text = soup.text
        posts = None

        post_args = (max_posts, trim, clean_posts, root_url)

        # Try article elements.
        article_elements = [x for x in soup.find_all('article')]
        if len(article_elements) >= 2:
            if print_status:
                print('Trying articles...')
            posts = _get_posts_from_elements(
                article_elements, root_url=root_url)
            if posts:
                if classifier:
                    pred = rate_posts(url, html, text, posts, classifier)
                if not classifier or pred:
                    return prepare_posts(posts, *post_args, method='article')

        # Try trafilatura feed.
        traf_urls = t_feeds.find_feed_urls(url)
        if len(traf_urls) >= 2:
            if print_status:
                print('Trying trafilatura feed...')
            posts = _get_posts_from_feed_urls(
                traf_urls, soup, root_url, root_scheme)
            if posts:
                # Not using classifier for trafilatura for now.
                # if classifier:
                #     pred = rate_posts(url, html, text, posts, classifier)
                # if not classifier or pred:
                return prepare_posts(posts, *post_args, valid=None, method='trafilatura')

        # Try newspaper.
        try:
            build = newspaper.build(url, memoize_articles=False)
            newspaper_urls = [article.url for article in build.articles]
        except Exception as ex:
            newspaper_urls = None
        if len(newspaper_urls) >= 2:
            if print_status:
                print('Trying newspaper...')
            posts = _get_posts_from_feed_urls(
                newspaper_urls, soup, root_url, root_scheme)
            if posts:
                if classifier:
                    pred = rate_posts(url, html, text, posts, classifier)
                if not classifier or pred:
                    return prepare_posts(posts, *post_args, method='newspaper')

        # Try class-based-method.
        if print_status:
            print('Trying class-based method...')
        posts = _element_method(
            html, text, soup, root_url, classifier, print_status)
        if posts:
            return prepare_posts(posts, *post_args, method='class-based')

        # If all else fails, return main content.
        if index == len(pages_to_try) - 1:
            main_content = t_extract(html, favor_recall=True)
            if main_content:
                return {'method': 'main content',
                        'valid_post_set': None,
                        'url': root_url,
                        'main_content': main_content.split('\n')}
            else:
                return {'error': 'No content found'}
