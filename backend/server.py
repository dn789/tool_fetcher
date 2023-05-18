"""
Server for Tool Fetcher Web App/Extension
"""

import base64
import json
import requests

from bs4 import BeautifulSoup
from flask import Flask, jsonify, json, Response, request
from flask_cors import CORS
from func_timeout import func_timeout, FunctionTimedOut
import newspaper

from find_terms.find_terms import FindTerms
from find_terms.pdf_utils import pdf_highlight
from find_terms.utils import read_lines
from get_posts.classifier import Classifier
from search_github import GithubAPI


CONFIG = json.load(open('data/server_config.json'))

AUTHOR_WATCHLIST = json.load(
    open(CONFIG['author_watchlist_file'], encoding='utf-8'))

FIND_TERMS = FindTerms(**CONFIG['find_terms_args'])
EXCLUDED_BY_USER_FILE = CONFIG['find_terms_args']['excluded_words_by_user_file']
EXCLUDED_BY_USER = set(read_lines(EXCLUDED_BY_USER_FILE))


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


@app.route('/home', methods=['GET', 'POST'])
def main():
    if request.method == 'POST':
        if request.headers['type'] == 'HTML':
            paragraphs = request.get_json()
            doc = '\n'.join(paragraphs)
            found_terms = FIND_TERMS.find_terms_in_doc(doc)
            term_dicts = GITHUB.search_repos(
                found_terms)
            results = {'termResults': term_dicts}
            response = jsonify(results)
            return response

        elif request.headers['type'] == 'PDF':
            pdf = request.get_data()
            found_terms = FIND_TERMS.find_terms_in_doc(pdf, pdf=True)
            highlighted_pdf = pdf_highlight(pdf, found_terms)
            encoded_pdf = base64.b64encode(highlighted_pdf)
            encoded_pdf = encoded_pdf.decode()
            term_dicts = GITHUB.search_repos(found_terms)
            results = {'encodedPDF': encoded_pdf,
                       'termResults': term_dicts}
            return Response(json.dumps(results), mimetype='text/plain')

        elif request.headers['type'] == 'findResultsForTerms':
            terms = request.get_json()
            results = GITHUB.search_repos(terms)
            term_dict = {term_dict['term']: term_dict for term_dict in results}
            return jsonify(term_dict)

        elif request.headers['type'] == 'updateWatchlist':
            request_obj = request.get_json()
            action = request_obj['action']
            if action == 'add':
                author_info = request_obj['author']
                author_name = author_info['name']
                new_author = GITHUB.get_user_recent(
                    author_name,
                    get_posts_args=GET_POSTS_ARGS
                )
                author_info.update(new_author)
                AUTHOR_WATCHLIST.setdefault(author_name, {})
                AUTHOR_WATCHLIST[author_name].update(author_info)
                recent = GITHUB.get_recent_from_watchlist(
                    AUTHOR_WATCHLIST, author_to_match=author_name)
                response = jsonify({
                    'newAuthor': author_info,
                    'recentPostIndices': recent['recentPostIndices'],
                    'recentRepoIndices': recent['recentRepoIndices']
                })
            else:
                author_name = request_obj['authorName']
                if author_name:
                    AUTHOR_WATCHLIST.pop(author_name)
                else:
                    AUTHOR_WATCHLIST.clear()
                response = jsonify('success')

            with open(CONFIG['author_watchlist_file'], 'w') as w:
                w.write(json.dumps(AUTHOR_WATCHLIST))
            return response

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
            rating_dict = request.get_json()
            term, rating = rating_dict['term'], rating_dict['rating']
            if rating:
                EXCLUDED_BY_USER.difference_update([term])
                with open(EXCLUDED_BY_USER_FILE, 'w') as w:
                    w.write('\n'.join(EXCLUDED_BY_USER))
            else:
                EXCLUDED_BY_USER.update([term])
                with open(EXCLUDED_BY_USER_FILE, 'w') as w:
                    w.write('\n'.join(EXCLUDED_BY_USER))
            FIND_TERMS.update_excluded()

            return jsonify('success')

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
