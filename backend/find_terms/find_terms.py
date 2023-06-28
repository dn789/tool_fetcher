"""
Finds terms in documents using NER models and regex matching. 
"""
import re

from bs4 import BeautifulSoup
from flair.data import Sentence
from flair.models import SequenceTagger

from .utils import (
    get_terms_from_tagged_sents,
    make_term_patterns,
    match_terms_in_sents,
    read_lines,
    sent_filter,
    sent_tokenize_web_doc,
)
from .pdf_utils import pdf_to_txt, sent_tokenize_pdf
from find_terms.roster_ner.predict import RoSTerPredictor


class FindTerms():
    def __init__(self,
                 excluded_words_file=None,
                 excluded_words_by_user_file=None,
                 terms_ignore_case_file=None,
                 terms_keep_case_file=None,
                 use_roster=False,
                 roster_model_path=None,
                 roster_args={},
                 use_flair=False,
                 flair_model=None,
                 sent_tokenize_method='nltk',
                 use_line_ends_for_pdf_tokenization=True,
                 combine_re_and_ner_terms=True):

        if terms_ignore_case_file or terms_keep_case_file:
            terms_ignore_case = read_lines(
                terms_ignore_case_file) if terms_ignore_case_file else None
            terms_keep_case = read_lines(
                terms_keep_case_file) if terms_keep_case_file else None
            self.term_patterns = make_term_patterns(
                terms_ignore_case, terms_keep_case)
        else:
            self.term_patterns = None
        self.excluded_words_file = excluded_words_file
        self.excluded_words_by_user_file = excluded_words_by_user_file
        self.excluded_words = set([x.lower()
                                  for x in read_lines(excluded_words_file)])
        if excluded_words_by_user_file:
            self.excluded_words = self.excluded_words | set([x.lower()
                                                             for x in read_lines(excluded_words_by_user_file)])

        self.use_roster = use_roster
        self.roster = None
        if self.use_roster:
            self.init_roster(**roster_args)
            self.roster.load_model(roster_model_path)

        self.use_flair = use_flair
        self.flair = None
        if self.use_flair:
            self.load_flair(flair_model)

        if sent_tokenize_method == 'nltk':
            from nltk import sent_tokenize
            self.sent_tokenize = sent_tokenize

        self.combine_re_and_ner_terms = combine_re_and_ner_terms
        self.use_line_ends_for_pdf_tokenization = use_line_ends_for_pdf_tokenization

    def init_roster(self,
                    model_type='roberta-base',
                    entity_types=['Term'],
                    dropout=.1,
                    max_seq_length=120,
                    eval_batch_size=64):

        self.roster = RoSTerPredictor(model_type=model_type,
                                      entity_types=entity_types,
                                      dropout=dropout,
                                      max_seq_length=max_seq_length,
                                      eval_batch_size=eval_batch_size)

    def load_roster_model(self, roster_model_path):
        if not self.roster:
            self.init_roster()
        self.roster.load_model(roster_model_path)

    def load_flair(self, flair_model="flair/ner-english-ontonotes-large"):
        flair_model = flair_model or "flair/ner-english-ontonotes-large"
        self.flair = SequenceTagger.load(flair_model)

    def predict_roster(self, sents, return_sents=True):
        return self.roster.predict(sents, return_sents=return_sents)

    def predict_flair(self, sents):
        terms = set()
        for sent in sents:
            sent = Sentence(sent)
            predicted = False
            mini_batch_size = 32
            while not predicted and mini_batch_size >= 1:
                try:
                    self.flair.predict(sent, mini_batch_size=mini_batch_size)
                    predicted = True
                except RuntimeError as e:
                    if 'out of memory' in str(e):
                        mini_batch_size = int(mini_batch_size / 2)
                    else:
                        raise RuntimeError(e)
            for entity in sent.get_spans('ner'):
                if entity.tag in ('PRODUCT'):
                    terms.add(entity.text)

            # sent = Sentence(sent)
            # self.flair.predict(sent)
            # for entity in sent.get_spans('ner'):
            #     if entity.tag in ('PRODUCT'):
            #         terms.add(entity.text)

        return terms

    def filter_terms(self, terms):
        filtered_terms = set()
        for term in terms:
            term = re.sub(r'^[^a-z0-9]*|[^a-z0-9]*$|\'s$',
                          '', term, flags=re.IGNORECASE)
            if term.lower() in self.excluded_words:
                continue
            if term.replace('-', ' ') in self.excluded_words or \
                    term.replace(' ', '-') in self.excluded_words:
                continue
            if term.strip():
                filtered_terms.add(term.strip())
        return filtered_terms

    def find_terms_in_doc(self,
                          doc,
                          pdf=False,
                          html=False,
                          filter_sents=True):
        if pdf:
            text = pdf_to_txt(doc)
            sents = sent_tokenize_pdf(text,
                                      self.sent_tokenize,
                                      use_line_ends=self.use_line_ends_for_pdf_tokenization)
        else:
            if html:
                doc = BeautifulSoup(doc, 'lxml').text
            sents = sent_tokenize_web_doc(doc, self.sent_tokenize)
        terms_dict = self.find_terms_in_sents(sents, filter_sents=filter_sents)
        if self.combine_re_and_ner_terms:
            return set().union(*terms_dict.values())
        return terms_dict

    def find_terms_in_sents(self, sents, filter_sents=True):
        if filter_sents:
            sents = [sent for sent in sents if sent_filter(sent)]
        terms_from_regex, terms_from_roster, terms_from_flair = set(), set(), set()
        if self.term_patterns:
            terms_from_regex = match_terms_in_sents(
                self.term_patterns, sents, return_terms_only=True)
        if self.use_roster:
            tagged_sents = self.predict_roster(sents)
            terms_from_roster = set(get_terms_from_tagged_sents(tagged_sents))
        if self.use_flair:
            terms_from_flair = self.predict_flair(sents)

        terms_from_roster = self.filter_terms(terms_from_roster)
        terms_from_flair = self.filter_terms(terms_from_flair)

        terms = {
            'from_re': terms_from_regex,
            'from_roster': terms_from_roster,
            'from_flair': terms_from_flair
        }
        return terms

    def update_excluded(self):
        self.excluded_words = set([x.lower() for x in read_lines(self.excluded_words_file)]) | set([x.lower()
                                                                                                    for x in read_lines(self.excluded_words_by_user_file)])
