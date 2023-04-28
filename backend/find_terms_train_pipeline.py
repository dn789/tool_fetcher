import argparse
import json
import os

from find_terms.make_corpus import make_corpus
from find_terms.roster_ner import train

description = """Training Pipeline for Named Entity Recognition Model

Use --make_corpus to make the training corpus sets (see find_terms/make_corpus.py for 
    full documentation).

Use --train_model to train the RoSTER NER model on the corpus sets (see 
    find_terms/roster_ner/README.md and the article: https://arxiv.org/abs/2109.05003).
    
Use --config to pass a JSON config file with arguments. Args in file will override those
    passed on the command line.

The default args should result in a reasonably good model. 
"""

parser = argparse.ArgumentParser(
    description=description, formatter_class=argparse.RawDescriptionHelpFormatter)

parser.add_argument('--config',
                    type=str,
                    default=None,
                    help='Path to config file. Settings in file will override those passed on the command line.'
                    )
parser.add_argument('--make_corpus',
                    action=argparse.BooleanOptionalAction,
                    help='Makes a training corpus from provided files and terms.'
                    )
parser.add_argument('--train_model',
                    action=argparse.BooleanOptionalAction,
                    help='Trains an NER model on corpus from make_corpus'
                    )
# make_corpus args
parser.add_argument('--corpus_input',
                    type=str,
                    default='find_terms/corpus_input/',
                    help='Path to PDF, HTM/L and .txt files to make corpus.'
                    )
parser.add_argument('--corpus_output',
                    type=str,
                    default='find_terms/corpus/',
                    help='Path to contain intermediate corpus files and training/test sets.'
                    )
parser.add_argument('--train_test_dir',
                    type=str,
                    default='set_1',
                    help='Folder to contain training/test set. Relative to --corpus_output path.'
                    )
parser.add_argument('--train_test_split',
                    type=float,
                    default=(85, 15),
                    nargs='+',
                    help='Train/dev/test split.'
                    )
parser.add_argument('--dont_filter_sents',
                    action=argparse.BooleanOptionalAction,
                    help='Don\'t filter sentences that are too long/don\'t have enough letters from the corpus.'
                    )
parser.add_argument('--neg_sent_proportion_pdf',
                    type=float,
                    default=.75,
                    help='Percentage of sentences without entities for PDFs.'
                    )
parser.add_argument('--neg_sent_proportion_web',
                    type=float,
                    default=.75,
                    help='Percentage of sentences without entities for web documents or text files.'
                    )
parser.add_argument('--replace_test_terms_with_oov',
                    default=False,
                    help='Replaces entities in test set(s) with ones that don\'t occur in training set.'
                    )
parser.add_argument('--sent_tokenize_method',
                    type=str,
                    default='nltk',
                    choices=['nltk', 'spacy'],
                    help='Method for tokenizing sentences.'
                    )
parser.add_argument('--use_line_ends_for_pdf_tokenization',
                    type=bool,
                    default=True,
                    help='Uses the presence or absence of spaces before newlines in text extracted from PDFs to aid tokenization.'
                    )
parser.add_argument('--terms_ignore_case_path',
                    type=str,
                    default='data/find_terms/training/tool_names_ignore_case_for_training.txt',
                    help='Path to file with terms to match ignoring case (don\'t have common word aliases).'
                    )
parser.add_argument('--terms_keep_case_path',
                    type=str,
                    default='data/find_terms/training/tool_names_keep_case.txt',
                    help='Path to file with terms to match case-sensitively.')

# train_model args
parser.add_argument("--train_model_input",
                    default="find_terms/corpus/train_test_sets/set_1/",
                    type=str,
                    help="Folder containing training/test set."
                    )
parser.add_argument("--pretrained_model",
                    default='roberta-base',
                    type=str,
                    help="(from RoSTER) pre-trained language model, default to roberta base."
                    )
parser.add_argument("--train_model_output",
                    default='find_terms/models/model_1',
                    type=str,
                    help="Folder containing the final model checkpoint."
                    )
parser.add_argument("--max_seq_length",
                    default=128,
                    type=int,
                    help="(from RoSTER) the maximum input sequence length."
                    )
parser.add_argument("--eval_only",
                    action=argparse.BooleanOptionalAction,
                    help="Only run evaluation on eval set (no training)."
                    )
parser.add_argument("--do_eval",
                    type=bool,
                    default=True,
                    help="(from RoSTER) whether to run eval on eval set or not."
                    )
parser.add_argument("--eval_on",
                    type=str,
                    default="dev",
                    choices=['dev', 'test'],
                    help="(from RoSTER) run eval on dev/test set."
                    )
parser.add_argument("--train_batch_size",
                    default=32,
                    type=int,
                    help="(from RoSTER) effective batch size for training."
                    )
parser.add_argument('--gradient_accumulation_steps',
                    type=int,
                    default=8,
                    help="(from RoSTER) number of updates steps to accumulate before performing a backward/update pass."
                    )
parser.add_argument("--eval_batch_size",
                    default=32,
                    type=int,
                    help="(from RoSTER) batch size for eval."
                    )
parser.add_argument("--noise_train_update_interval",
                    default=200,
                    type=int,
                    help="(from RoSTER) number of batches to periodically perform noisy label removal for noise robust training."
                    )
parser.add_argument("--self_train_update_interval",
                    default=100,
                    type=int,
                    help="(from RoSTER) number of batches to periodically compute new soft labels for self-training."
                    )
parser.add_argument("--noise_train_lr",
                    default=3e-5,
                    type=float,
                    help="(from RoSTER) the peak learning rate for noise robust training."
                    )
parser.add_argument("--ensemble_train_lr",
                    default=1e-5,
                    type=float,
                    help="(from RoSTER) the peak learning rate for ensemble model training."
                    )
parser.add_argument("--self_train_lr",
                    default=5e-7,
                    type=float,
                    help="(from RoSTER) the peak learning rate for self-training."
                    )
parser.add_argument("--noise_train_epochs",
                    default=2,
                    type=int,
                    help="(from RoSTER) total number of training epochs for noise robust training."
                    )
parser.add_argument("--ensemble_train_epochs",
                    default=2,
                    type=int,
                    help="(from RoSTER) total number of training epochs for ensemble model training."
                    )
parser.add_argument("--self_train_epochs",
                    default=3,
                    type=int,
                    help="(from RoSTER) total number of training epochs for self-training."
                    )
parser.add_argument("--q",
                    default=0.7,
                    type=float,
                    help="(from RoSTER) the hyperparameter of GCE loss. Larger value means higher tolerance to noise (for noisy data). Smaller value means better convergence (for clean data)."
                    )
parser.add_argument("--tau",
                    default=0.7,
                    type=float,
                    help="(from RoSTER) the threshold for noisy label removal."
                    )
parser.add_argument("--num_models",
                    default=5,
                    type=int,
                    help="(from RoSTER) total number of models to ensemble."
                    )
parser.add_argument("--warmup_proportion",
                    default=0.1,
                    type=float,
                    help="(from RoSTER) proportion of learning rate warmup."
                    )
parser.add_argument("--weight_decay",
                    default=0.01,
                    type=float,
                    help="(from RoSTER) weight decay for model training."
                    )
parser.add_argument("--dropout",
                    default=0.1,
                    type=float,
                    help="(from RoSTER) dropout ratio"
                    )
parser.add_argument('--seed',
                    type=int,
                    default=42,
                    help="(from RoSTER) random seed for training"
                    )


args = parser.parse_args()
args = vars(args)

if args['config']:
    config = json.load(open(args['config'], encoding='utf-8'))
    args.update(config)


print('Arguments: ', args)

make_corpus_args = ('corpus_input',
                    'corpus_output',
                    'train_test_dir',
                    'train_test_split',
                    'dont_filter_sents',
                    'neg_sent_proportion_pdf',
                    'neg_sent_proportion_web',
                    'replace_test_terms_with_oov'
                    )
train_model_args = {k: v for k, v in args.items(
) if k not in make_corpus_args + ('make_corpus', 'find_terms', 'config')}


if args['make_corpus']:
    make_corpus_args = {k: args[k] for k in make_corpus_args}
    for x in ('input', 'output'):
        make_corpus_args[x] = make_corpus_args[f'corpus_{x}']
        make_corpus_args.pop(f'corpus_{x}')
    make_corpus(**make_corpus_args)

if args['train_model']:
    train_model_args['corpus_dir'] = train_model_args['train_model_input']
    train_model_args.pop('train_model_input')
    train_model_args['output_dir'] = train_model_args['train_model_output']
    train_model_args.pop('train_model_output')
    train_model_args['temp_dir'] = 'find_terms/roster_ner/temp/' + \
        os.path.basename(train_model_args['output_dir'])
    train_model_args = argparse.Namespace(**train_model_args)
    train.train(train_model_args)
