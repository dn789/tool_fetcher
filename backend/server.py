"""
Server for Tool Fetcher Web App/Extension
"""

import base64
import importlib
import json
import requests

from bs4 import BeautifulSoup
from flask import Flask, jsonify, json, Response, request
from flask_cors import CORS
from func_timeout import func_timeout, FunctionTimedOut
import newspaper

from find_terms.find_terms import FindTerms
from find_terms.pdf_utils import pdf_highlight
from get_posts.classifier import Classifier
from search_github import GithubAPI


CONFIG = json.load(open('data/server_config.json'))

AUTHOR_WATCHLIST = json.load(
    open(CONFIG['author_watchlist_file'], encoding='utf-8'))

GET_POSTS_ARGS = CONFIG.get('get_posts_args', {})
POST_SET_CLASSIFIER = Classifier(
    GET_POSTS_ARGS.pop('post-set-classifier-csv'), type_='post_set')
GET_POSTS_ARGS.update({'classifier': POST_SET_CLASSIFIER})

GITHUB = GithubAPI(**CONFIG['github_args'])

app = Flask(__name__)
CORS(app)
app.config.update(SECRET_KEY=CONFIG['flask_key'])


def get_html(url):
    try:
        r = requests.get(url)
    except Exception:
        r = None
    if not r or r.status_code != 200:
        html = newspaper.build(url).html
    else:
        html = r.text
    return html


FIND_TERMS = FindTerms(**CONFIG['find_terms_args'])


@app.route('/home', methods=['GET', 'POST'])
def main():

    if request.method == 'POST':

        if request.headers['type'] == 'HTML':
            paragraphs = request.get_json()
            doc = '\n'.join(paragraphs)
            found_terms = FIND_TERMS.find_terms_in_doc(doc)
            term_dicts = GITHUB.search_repos(
                found_terms)
            results = {'terms_and_links': term_dicts}
            response = jsonify(results)
            return response

        elif request.headers['type'] == 'PDF':
            pdf = request.get_data()
            found_terms = FIND_TERMS.find_terms_in_doc(doc, pdf=True)
            highlighted_pdf = pdf_highlight(pdf)
            encoded_pdf = base64.b64encode(highlighted_pdf)
            encoded_pdf = encoded_pdf.decode()
            term_dicts = GITHUB.search_repos(found_terms)
            results = {'encoded_pdf': encoded_pdf,
                       'terms_and_links': term_dicts}
            return Response(json.dumps(results), mimetype='text/plain')

        elif request.headers['type'] == 'exclude':
            # author_info = request.get_json()
            # EXCLUDED.update(author_info)
            # with open(CONFIG['exclude_file'], 'w') as w:
            #     w.write('\n'.join(EXCLUDED))
            return 'success'

        elif request.headers['type'] == 'undoExclude':
            # author_info = request.get_json()
            # EXCLUDED.difference_update(author_info)
            # with open(CONFIG['excludeFile'], 'w') as w:
            #     w.write('\n'.join(EXCLUDED))
            return 'success'

        elif request.headers['type'] == 'findResultsForTerms':
            terms = request.get_json()
            results = GITHUB.search_repos(terms)
            term_dict = {term_dict['term']: term_dict for term_dict in results}
            return jsonify(term_dict)

        elif request.headers['type'] == 'authorWatchlistAdd':
            author_info = request.get_json()
            author_name = author_info.pop('name')
            new_author = GITHUB.get_user_recent(
                author_name,
                get_posts_args=GET_POSTS_ARGS
            )
            author_info.update(new_author)
            AUTHOR_WATCHLIST.setdefault(author_name, {})
            AUTHOR_WATCHLIST[author_name].update(author_info)
            recent = GITHUB.get_recent_from_watchlist(
                AUTHOR_WATCHLIST, author_to_match=author_name)
            with open(CONFIG['author_watchlist_file'], 'w') as w:
                w.write(json.dumps(AUTHOR_WATCHLIST))
            return jsonify({'newAuthor': new_author,
                            'recentPostIndices': recent['recentPostIndices'],
                            'recentRepoIndices': recent['recentRepoIndices']
                            })

        elif request.headers['type'] == 'authorWatchlistRemove':
            author_info = request.get_json()
            if author_info:
                for author_name in author_info:
                    AUTHOR_WATCHLIST.pop(author_name)
            else:
                AUTHOR_WATCHLIST.clear()
            with open(CONFIG['author_watchlist_file'], 'w') as w:
                w.write(json.dumps(AUTHOR_WATCHLIST))
            return 'success'

        elif request.headers['type'] == 'findTermsInURL':
            url = request.get_json()
            try:
                doc = func_timeout(30, get_html, args=(url,))
            except FunctionTimedOut:
                return jsonify({'error': 'Timeout.'})
            if not doc:
                return jsonify({'error': 'No content found on page.'})
            soup = BeautifulSoup(doc, 'lxml')
            text = soup.get_text()
            found_terms = FIND_TERMS.find_terms_in_doc(text)
            term_dicts = GITHUB.search_repos(found_terms)
            results = {'termResults': term_dicts,
                       'webPageText': text}
            response = jsonify(results)
            return response

        elif request.headers['type'] == 'rateResults':
            RATE_RESULTS = json.load(
                open('data/rate_results.json', encoding='utf-8'))
            rating_dict = request.get_json()
            if rating_dict['rating']:
                RATE_RESULTS[rating_dict['source']].pop(rating_dict['term'])
            else:
                RATE_RESULTS.setdefault(rating_dict['source'], {})
                RATE_RESULTS[rating_dict['source']
                             ][rating_dict['term']] = False
            with open('data/rate_results.json', 'w', encoding='utf-8') as f:
                f.write(json.dumps(RATE_RESULTS))
            return 'success'

    elif request.method == 'GET':
        if request.headers['type'] == 'recentActivityGet':
            recent = GITHUB.get_recent_from_watchlist(
                AUTHOR_WATCHLIST)
            response = jsonify({
                'watchlist': AUTHOR_WATCHLIST,
                'recentPostIndices': recent['recentPostIndices'],
                'recentRepoIndices': recent['recentRepoIndices']
            })
            return response


app.run(debug=True)
