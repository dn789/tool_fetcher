import json

from transformers import pipeline
from statistics import mean, StatisticsError

from find_terms.utils import get_alpha_prop, get_terms_from_tagged_sents, normalize_term, prepare_sent_NER, sent_filter, sent_tokenize_web_doc
from nltk import sent_tokenize

TEST_SENTS_DIR = 'c:/Users/nassr/Desktop/NER results/test_pages_tokenized_sents/'
TEST_WORDS_ACTUAL = 'c:/Users/nassr/Desktop/NER results/test_words_actual/'
TEST_WORDS_ACTUAL_FILTERED = 'c:/Users/nassr/Desktop/NER results/test_words_actual_filtered/'

TEST_REF = json.load(
    open('testing/test_find_terms/test_ref.json', encoding='utf-8'))

# If decide to load tokenizer separatetely:
# from transformers import RobertaTokenizer
# tokenizer = RobertaTokenizer.from_pretrained("roberta-base")
# pass tokenizer argument to pipeline


def extract_entities(model_output, sent):
    """Combines token output from a transformer NER model and returns a list of
    complete entities with corresponding probability scores. 

    Parameters
    ----------
    model_output : list 
        Output of transformers.pipeline on a sentence. 
    sent : _type_
        The corresponding sentence.

    Returns
    -------
    list of dicts
        List of entities of the form: {'text': [entity text], 'score': 
        [probability score]}.

    Raises
    ------
    Exception
        _description_
    """
    raw_entities = []
    current_entity = {}
    for token in model_output:
        if not current_entity or (
            current_entity['last_type'] == 'I-Term' and token['entity'] == 'B-Term') or (
                token['entity'] == 'B-Term' and sent[token['start'] - 1] == ' '):
            if current_entity:
                raw_entities.append(current_entity)
            current_entity = {
                'start': token['start'],
                'end': token['end'],
                'score': [token['score']],
                'last_type': token['entity']
            }
        elif current_entity:
            current_entity['end'] = token['end']
            current_entity['last_type'] = token['entity']
            current_entity['score'].append(token['score'])
    if current_entity:
        raw_entities.append(current_entity)
    merged_entities = []
    for entity in raw_entities:
        merged_entity = {
            'text': sent[entity['start']:entity['end']],
            'score': mean(entity['score'])
        }
        merged_entities.append(merged_entity)
    return merged_entities


def update_entities_dict(entities_dict, entity_results):
    for entity in entity_results:
        if entities_dict.get(entity['text']):
            if entities_dict[entity['text']] < entity['score']:
                entities_dict[entity['text']] = entity['score']
        else:
            entities_dict[entity['text']] = entity['score']
    for entity, score in entities_dict.items():
        entities_dict[entity] = float(score)


model_checkpoint = 'c:/Users/nassr/Desktop/remote_log/checkpoint-18500/'
model_name = 'test'


def test_model(model_name, model_checkpoint):
    nlp = pipeline('ner', model=model_checkpoint)
    model_results = {}
    for filename, v in TEST_REF.items():
        print(filename)
        model_results[filename] = {}
        for sent_set_label in ('sents_passed_filter', 'sents_failed_filter'):
            model_results[filename][sent_set_label] = {}
            sent_set = v[sent_set_label]
            entities, entities_from_sents_with_train_terms = {}, {}
            if not sent_set:
                continue
            results = nlp(sent_set)
            for result, sent in zip(results, sent_set):
                entities_from_sent = extract_entities(result, sent)
                for term in v['actual_entities_in_training']:
                    if term in sent:
                        update_entities_dict(
                            entities_from_sents_with_train_terms, entities_from_sent)
                        break
                else:
                    update_entities_dict(entities, entities_from_sent)
            model_results[filename][sent_set_label]['entities'] = entities
            model_results[filename][sent_set_label]['entities_from_sents_with_train_terms'] = entities_from_sents_with_train_terms
    with open(f'{model_name}_results.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(model_results))


# test_model(model_name, model)

def make_test_ref():
    new_ref = {}
    for filename, v in TEST_REF.items():
        new_ref[filename] = {
            'main_test': {
                "entities": v['actual_entities'],
                'sentences': []
            },
            "training_words_test": {
                "entities": v['actual_entities_in_training'],
                'sentences': []
            },
            "discarded_sents": v['sents_failed_filter']
        }
        words = v['actual_entities_in_training']
        words = [x.lower() for x in words]
        if not words:
            new_ref[filename]['main_test']['sentences'] = v['sents_passed_filter']
            continue
        for sent in v['sents_passed_filter']:
            sent_lower = sent.lower()
            for word in words:
                if word in sent_lower:
                    new_ref[filename]['training_words_test']['sentences'].append(
                        sent)
                    break
            else:
                new_ref[filename]['main_test']['sentences'].append(sent)

    open('new_test_ref.json', 'w', encoding='utf-8').write(json.dumps(new_ref))
