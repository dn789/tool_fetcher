"""
Gets repo, user information from Github.
"""
import datetime
import json
import requests
import time

from func_timeout import func_timeout, FunctionTimedOut
from github import Github
from github import RateLimitExceededException
from transformers import pipeline

from get_posts.get_posts import get_posts


class GithubAPI():
    def __init__(self,
                 token,
                 n_recent_activity=100,
                 n_recent_repos=3,
                 n_repo_results=5,
                 dummy_results=False,
                 filter_no_links=False,
                 relevance_classifier_args={},
                 sort_by_relevance=False,
                 exclude_terms_without_relevant_repo=False
                 ):

        self.api = Github(token)
        self.dummy_results = dummy_results
        self.filter_no_links = filter_no_links
        self.n_recent_activity = n_recent_activity
        self.n_recent_repos = n_recent_repos
        self.n_repo_results = n_repo_results
        self.sort_by_relevance = sort_by_relevance
        self.exclude_terms_without_relevant_repo = exclude_terms_without_relevant_repo
        if self.sort_by_relevance or self.exclude_terms_without_relevant_repo:
            self.relevance_classifier = RelevanceClassifier(
                **relevance_classifier_args)
        else:
            self.relevance_classifier = None

    def search_repos(self, terms, resume_after_rate_limiting=False):
        """
        Github Search

        Returns top n_results results for each term

        Parameters
        ----------
        terms : list
            List of strings.
        n_results: int
            Number of results to return for each term, default 5
        dummy_result : bool, default False
            Dummy results for each term.  
        filter_no_links : bool, default False
            Excludes terms without search results. 

        Returns
        -------
        list
        A list of results(dictionaries).
        """
        results = []

        if self.dummy_results:
            for term in range(5):
                results.append(
                    {
                        'term': 'agency',
                        'repos': [{
                            'url': 'https://github.com/agency-library/agency',
                            'name': 'agency',
                            'description': 'Execution primitives for C++',
                            'author': {
                                'name': 'agency-library',
                                'blogURL': '',
                                'bio': None,
                                'url': 'https://github.com/agency-library',
                                'twitter': None
                            },
                            'relevance': {
                                'label': None,
                                'score': None
                            }
                        }, {
                            'url': 'https://github.com/StartBootstrap/startbootstrap-agency',
                            'name': 'startbootstrap-agency',
                            'description': 'A one page HTML theme for agencies created by Start Bootstrap',
                            'author': {
                                'name': 'StartBootstrap',
                                'blogURL': 'https://startbootstrap.com',
                                'bio': 'Powerful UI tools built with Bootstrap',
                                'url': 'https://github.com/StartBootstrap',
                                'twitter': 'SBootstrap'
                            },
                            'relevance': {
                                'label': None,
                                'score': None
                            }
                        }, {
                            'url': 'https://github.com/y7kim/agency-jekyll-theme',
                            'name': 'agency-jekyll-theme',
                            'description': 'Agency Theme for Jekyll',
                            'author': {
                                'name': 'y7kim',
                                'blogURL': '',
                                'bio': None,
                                'url': 'https://github.com/y7kim',
                                'twitter': None
                            },
                            'relevance': {
                                'label': None,
                                'score': None
                            }
                        }, {
                            'url': 'https://github.com/benbjohnson/agency',
                            'name': 'agency',
                            'description': 'A fast user agent string parser for Go.',
                            'author': {
                                'name': 'benbjohnson',
                                'blogURL': 'https://litestream.io',
                                'bio': None,
                                'url': 'https://github.com/benbjohnson',
                                'twitter': 'benbjohnson'
                            },
                            'relevance': {
                                'label': None,
                                'score': None
                            }
                        }, {
                            'url': 'https://github.com/raviriley/agency-jekyll-theme',
                            'name': 'agency-jekyll-theme',
                            'description': 'Jekyll version of the newest Agency Bootstrap theme, plus new features: Google Analytics, Markdown support, custom pages, and more!',
                            'author': {
                                'name': 'raviriley',
                                'blogURL': 'raviriley.com',
                                'bio': None,
                                'url': 'https://github.com/raviriley',
                                'twitter': 'ravi_riley'
                            },
                            'relevance': {
                                'label': None,
                                'score': None
                            }
                        }],
                        'relevance': 0
                    }
                )
            results[1] = {'term': 'bad term', 'error': 'Rate limit exceeded'}
            return results

        terms = list(terms)
        for index, term in enumerate(terms):
            results_dict = {'term': term, 'repos': [], 'relevance': 0}
            repos = None
            while repos is None:
                try:
                    repos = self.api.search_repositories(
                        query=f'{term} in:name')
                except RateLimitExceededException:
                    if resume_after_rate_limiting:
                        print(f'rate limit exceeded getting repos for {term}')
                        limit = self.api.get_rate_limit().core
                        if not limit.remaining:
                            reset = limit.core.reset
                            current = datetime.datetime.today()
                            time_to_wait = (reset - current).seconds + 10
                            time.sleep(time_to_wait)
                    else:
                        for term in terms[index:]:
                            results.append(
                                {'term': term, 'error': 'Rate limit exceeded'})
                            break

            if repos.totalCount:
                for repo in repos[:self.n_repo_results]:
                    description = repo.description
                    if self.relevance_classifier and description:
                        relevance = self.relevance_classifier.classify_text(
                            repo.description)
                    else:
                        relevance = {'label': None, 'score': None}
                    results_dict['repos'].append(
                        {
                            'url': repo.html_url,
                            'name': repo.name,
                            'description': repo.description,
                            'downloadLink': repo.get_archive_link('zipball'),
                            'author': {
                                'name': repo.owner.login,
                                'blogURL': repo.owner.blog,
                                'bio': repo.owner.bio,
                                'url': repo.owner.html_url,
                                'twitter': repo.owner.twitter_username
                            },
                            'relevance': {
                                'label': relevance['label'],
                                'score': relevance['score']
                            }
                        }
                    )

                if self.exclude_terms_without_relevant_repo:
                    if not any([repo['relevance']['label'] for repo in results_dict['repos']]):
                        continue

                for repo in results_dict['repos']:
                    if repo['relevance']['label'] is True:
                        results_dict['relevance'] += repo['relevance']['score']

            elif not self.filter_no_links:
                results_dict['error'] = 'No repos found'
                results_dict['relevance'] = -1

            results.append(results_dict)

        if self.relevance_classifier:
            results.sort(key=lambda x: x['relevance'], reverse=True)

        return results

    def get_user_recent(self, user_login, get_posts_args, return_all_info=False):
        try:
            user = self.api.search_users(f'{user_login} in:login')[0]
            if user.blog and 'classifier' in get_posts_args:
                if not user.blog.startswith('http://') and not user.blog.startswith('https://'):
                    blog_url = 'http://' + user.blog
                else:
                    blog_url = user.blog
                try:
                    recent_blog = func_timeout(100, get_posts, args=(
                        blog_url,), kwargs=get_posts_args)
                except FunctionTimedOut:
                    recent_blog = {'error': 'Getting posts timed out.'}

            else:
                blog_url = None
                recent_blog = {'error': 'No blog page listed on Github.'}
            # Old method using requests and user.repos_url. Now using
            # user.get_repos to get archive link

            # r = requests.get(user.repos_url)
            # repos = r.json()
            # if repos:
            #     repos = sorted(repos, key=lambda x: x['updated_at'], reverse=True)[
            #         :self.n_recent_repos]
            #     recent_repos = []
            #     for repo in repos:
            #         if type(repo) == dict:
            #             recent_repos.append({
            #                 'name': repo['name'],
            #                 'url': repo['html_url'],
            #                 'downloadLink': repo.get_archive_link('zipball'),
            #                 'description': repo['description'],
            #                 'topics': repo['topics'],
            #                 'updated_at': repo['updated_at'],
            #             })
            repos = self.api.search_repositories(
                query=f'user:{user_login}', sort='updated')[:self.n_recent_repos]
            if repos:
                recent_repos = []
                for repo in repos:
                    recent_repos.append({
                        'name': repo.name,
                        'url': repo.html_url,
                        'downloadLink': repo.get_archive_link('zipball'),
                        'description': repo.description,
                        'topics': repo.topics,
                        'pushed_at': str(repo.pushed_at),
                    })
            else:
                recent_repos = {'error': 'No repos found.'}
            user_recent = {'recentBlog': recent_blog,
                           'recentRepos': recent_repos}
            if return_all_info:
                user_recent.update({
                    'name': user.login,
                    'bio': user.bio,
                    'url': user.html_url,
                    'blogURL': blog_url,
                    'twitter': user.twitter_username,
                })
            return user_recent

        except RateLimitExceededException:
            return {'recentBlog': {'error': 'Rate limit exceded.'}, 'recentRepos': {'error': 'Rate limit exceded.'}}

    def get_recent_from_watchlist(self, watchlist, author_to_match=None):
        """
        Gets n most recent posts and repos fom authors in author watchlist.

        Parameters
        ----------
        watchlist : str or dict
            Path to JSON file or dictionary. 
        n:  int
            Number of posts and repos (maybe do this client side?)
        author_name: str
            (Used when updating, not populating, the Recent panel)
            When adding an author to the watchlist, will check if the author is included in
            the most recent posts and/or repos. If not, returns None for the respective 
            value.



        Returns
        ----------
        Dictionary of lists of dictionaries:

        {'recentPosts': [
            {
            'author': author (str), 
            'index': index of post in watchlist[author]['recentBlog']['posts'] (int)
            }
            ,...],
        'recentRepos': [
            {
            'author': author (str), 
            'index': index of repo in watchlist[author]['recentRepos'] (int)
            }
            ,...]
        }
        """
        if type(watchlist) == str:
            watchlist = json.load(open(watchlist, encoding='utf-8'))

        post_index_dicts = []
        for author, props in watchlist.items():
            try:
                for index, post_dict in enumerate(props['recentBlog']['posts']):

                    post_index_dicts.append(
                        {
                            'date': post_dict['date'],
                            'author': {
                                'name': author,
                                'url': props['url'],
                                'blogURL': props['blogURL'],
                                'twitter': props['twitter']
                            },
                            'index': index
                        })

            except KeyError:
                pass

        repo_index_dicts = []
        for author, props in watchlist.items():
            try:
                for index, repo in enumerate(props['recentRepos']):
                    if type(repo) == dict:
                        repo_index_dicts.append(
                            {
                                'date': repo['pushed_at'],
                                'author': {
                                    'name': author,
                                    'url': props['url'],
                                    'blogURL': props['blogURL'],
                                    'twitter': props['twitter']
                                },
                                'index': index
                            })

            except KeyError:
                pass

        post_dates_index_dicts, post_null_dates_index_dicts = [], []
        for post_dict in post_index_dicts:
            if post_dict['date']:
                post_dates_index_dicts.append(post_dict)
            else:
                # Do something with this later
                post_null_dates_index_dicts.append(post_dict)

        post_dates_index_dicts.sort(
            key=lambda x: x['date'], reverse=True)

        repo_index_dicts.sort(
            key=lambda x: x['date'], reverse=True)

        return_recent_posts = True if not author_to_match else False
        return_recent_repos = True if not author_to_match else False

        post_dates_index_dicts = post_dates_index_dicts[:self.n_recent_activity]
        if author_to_match:
            for posts_index_dict in post_dates_index_dicts:
                if author_to_match == posts_index_dict['author']['name']:
                    return_recent_posts = True
                    break

        repo_index_dicts = repo_index_dicts[:self.n_recent_activity]
        if author_to_match:
            for repo_index_dict in repo_index_dicts:
                if author_to_match == repo_index_dict['author']['name']:
                    return_recent_repos = True
                    break

        return {
            'recentPostIndices': post_dates_index_dicts if return_recent_posts else [],
            'recentRepoIndices': repo_index_dicts if return_recent_repos else []
        }


class RelevanceClassifier():
    def __init__(self,
                 task='zero-shot-classification',
                 model="facebook/bart-large-mnli",
                 label_dict={'cybersecurity software': True,
                             'other software': False
                             },
                 ):

        self.classifier = pipeline(task, model)
        self.label_dict = label_dict
        self.labels = list(label_dict.keys())

    def classify_text(self, text, print_=False):
        result = self.classifier(text, self.labels)
        labels, scores = result['labels'], result['scores']
        if print_:
            print(labels)
            print(scores)
        max_score = max(scores)
        label = self.label_dict[labels[scores.index(max_score)]]
        return {'label': label, 'score': max_score}
