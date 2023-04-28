"""
Gets repo, user information from Github.
"""

import json
import requests

from func_timeout import func_timeout, FunctionTimedOut
from github import Github
from github import RateLimitExceededException

from get_posts.get_posts import get_posts


class GithubAPI():
    def __init__(self,
                 token,
                 n_recent_activity=100,
                 n_recent_repos=3,
                 n_repo_results=5,
                 dummy_results=False,
                 filter_no_links=False):

        self.api = Github(token)
        self.dummy_results = dummy_results
        self.filter_no_links = filter_no_links
        self.n_recent_activity = n_recent_activity
        self.n_recent_repos = n_recent_repos
        self.n_repo_results = n_repo_results

    def search_repos(self, terms):
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
            for term in terms:
                results.append(
                    {
                        'term': term,
                        'url': f'www.{term}.com',
                        'author': f'{term}_author',
                        'author_page': f'www.author_of_{term}.com',
                        'author_twitter': f'{term}_author'
                    }
                )
            return results

        terms = list(terms)
        for index, term in enumerate(terms):
            results_dict = {'term': term, 'repos': []}
            try:
                repos = self.api.search_repositories(query=f'{term} in:name')

                if repos.totalCount:
                    for repo in repos[:self.n_repo_results]:
                        results_dict['repos'].append(
                            {
                                'url': repo.html_url,
                                'name': repo.name,
                                'description': repo.description,
                                'author': {
                                    'name': repo.owner.login,
                                    'blogURL': repo.owner.blog,
                                    'bio': repo.owner.bio,
                                    'url': repo.owner.html_url,
                                    'twitter': repo.owner.twitter_username
                                }
                            }
                        )
                elif not self.filter_no_links:
                    results_dict['error'] = 'No repos found'

                results.append(results_dict)

            except RateLimitExceededException:
                for term in terms[index:]:
                    results.append(
                        {'term': term, 'error': 'Rate limit exceeded'})
                    break
        return results

    def get_user_recent(self, user_login, get_posts_args):
        try:
            user = self.api.search_users(f'{user_login} in:login')[0]
            if user.blog and 'classifier' in get_posts_args:
                if not user.blog.startswith('http://') and not user.blog.startswith('https://'):
                    blog_url = 'http://' + user.blog
                else:
                    blog_url = user.blog
                # recent_blog = post_extract.post_extract(
                #     blog_url, **post_extract_args)
                try:
                    recent_blog = func_timeout(100, get_posts, args=(
                        blog_url,), kwargs=get_posts_args)
                except FunctionTimedOut:
                    recent_blog = {'error': 'Extracting posts timed out.'}

            else:
                recent_blog = {'error': 'No blog page listed on Github.'}
            r = requests.get(user.repos_url)
            repos = r.json()
            if repos:
                repos = sorted(repos, key=lambda x: x['updated_at'], reverse=True)[
                    :self.n_recent_repos]
                recent_repos = []
                for repo in repos:
                    if type(repo) == dict:
                        recent_repos.append({
                            'name': repo['name'],
                            'url': repo['html_url'],
                            'description': repo['description'],
                            'topics': repo['topics'],
                            'updated_at': repo['updated_at'],
                        })
            else:
                recent_repos = {'error': 'No repos found.'}

            return {'recentBlog': recent_blog, 'recentRepos': recent_repos}
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
                                'date': repo['updated_at'],
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
            'recentPostIndices': post_dates_index_dicts if return_recent_posts else False,
            'recentRepoIndices': repo_index_dicts if return_recent_repos else False
        }
