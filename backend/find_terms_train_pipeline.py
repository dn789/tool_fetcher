import argparse
import shutil

from find_terms.make_corpus import make_corpus
from find_terms.roster_ner.src import train

parser = argparse.ArgumentParser(description='Find terms training pipeline')

parser.add_argument('--make_corpus', type=str, default=False,
                    help='Makes a training corpus from provided files and terms.')
parser.add_argument('--train_model', type=str,
                    default=False, help='Trains an NER model on corpus from make_corpus')
# make_corpus args
parser.add_argument('--corpus_input', type=str, default='find_terms/corpus_input/',
                    help='Folder containing PDF, HTM/L and .txt files to make corpus.')
parser.add_argument('--corpus_output', type=str, default='find_terms/corpus/',
                    help='Folder to contain intermediate corpus files and training/test sets.')
parser.add_argument('--train_test_dir', type=str, default='set_1',
                    help='Folder to contain training/test set.')
parser.add_argument('--train_test_split', type=float, default=(85, 15), nargs='+',
                    help='Train/dev/test split.')
parser.add_argument('--dont_filter_sents', default=False,
                    help='Don\'t filter sentences that are too long/don\'t have enough letters from the corpus.')
parser.add_argument('--neg_sent_proportion_pdf', type=float, default=0,
                    help='% of sentences without entities for PDFs.')
parser.add_argument('--neg_sent_proportion_web', type=float, default=0,
                    help='% of sentences without entities for web documents or text files.')
parser.add_argument('--replace_test_terms_with_oov', default=False,
                    help='Replaces entities in test set(s) with ones that don\'t occur in training set.')
# train_model args
parser.add_argument("--corpus_dir",
                    default="find_terms/corpus/train_test_sets/set_1/",
                    type=str,
                    help="Folder containing training/test set.")
parser.add_argument("--pretrained_model",
                    default='roberta-base',
                    type=str,
                    help="(from RoSTER) pre-trained language model, default to roberta base.")
parser.add_argument('--temp_dir',
                    type=str,
                    default="find_terms/roster_ner/tmp",
                    help="(from RoSTER) temporary directory for saved models")
parser.add_argument("--output_dir",
                    default='find_terms/models/model_1',
                    type=str,
                    help="Folder containing the final model checkpoint.")
parser.add_argument("--max_seq_length",
                    default=128,
                    type=int,
                    help="(from RoSTER) the maximum input sequence length.")
parser.add_argument("--tag_scheme",
                    default='iob',
                    type=str,
                    choices=['iob', 'io'],
                    help="(from RoSTER) the tagging scheme used.")

# training settting parameters
parser.add_argument("--do_train",
                    default=True,
                    help="(from RoSTER) whether to run training.")
parser.add_argument("--do_eval",
                    default=True,
                    help="(from RoSTER) whether to run eval on eval set or not.")
parser.add_argument("--eval_on",
                    default="dev",
                    choices=['dev', 'test'],
                    help="(from RoSTER) run eval on dev/test set.")
parser.add_argument("--train_batch_size",
                    default=32,
                    type=int,
                    help="(from RoSTER) effective batch size for training.")
parser.add_argument('--gradient_accumulation_steps',
                    type=int,
                    default=8,
                    help="(from RoSTER) number of updates steps to accumulate before performing a backward/update pass.")
parser.add_argument("--eval_batch_size",
                    default=32,
                    type=int,
                    help="(from RoSTER) batch size for eval.")
parser.add_argument("--noise_train_update_interval",
                    default=200,
                    type=int,
                    help="(from RoSTER) number of batches to periodically perform noisy label removal for noise robust training.")
parser.add_argument("--self_train_update_interval",
                    default=100,
                    type=int,
                    help="(from RoSTER) number of batches to periodically compute new soft labels for self-training.")
parser.add_argument("--noise_train_lr",
                    default=3e-5,
                    type=float,
                    help="(from RoSTER) the peak learning rate for noise robust training.")
parser.add_argument("--ensemble_train_lr",
                    default=1e-5,
                    type=float,
                    help="(from RoSTER) the peak learning rate for ensemble model training.")
parser.add_argument("--self_train_lr",
                    default=5e-7,
                    type=float,
                    help="(from RoSTER) the peak learning rate for self-training.")
parser.add_argument("--noise_train_epochs",
                    default=2,
                    type=int,
                    help="(from RoSTER) total number of training epochs for noise robust training.")
parser.add_argument("--ensemble_train_epochs",
                    default=2,
                    type=int,
                    help="(from RoSTER) total number of training epochs for ensemble model training.")
parser.add_argument("--self_train_epochs",
                    default=2,
                    type=int,
                    help="(from RoSTER) total number of training epochs for self-training.")
parser.add_argument("--q",
                    default=0.7,
                    type=float,
                    help="(from RoSTER) the hyperparameter of GCE loss. Larger value means higher tolerance to noise (for noisy data). Smaller value means better convergence (for clean data).")
parser.add_argument("--tau",
                    default=0.7,
                    type=float,
                    help="(from RoSTER) the threshold for noisy label removal.")
parser.add_argument("--num_models",
                    default=2,
                    type=int,
                    help="(from RoSTER) total number of models to ensemble.")
parser.add_argument("--warmup_proportion",
                    default=0.1,
                    type=float,
                    help="(from RoSTER) proportion of learning rate warmup.")
parser.add_argument("--weight_decay",
                    default=0.01,
                    type=float,
                    help="(from RoSTER) weight decay for model training.")
parser.add_argument("--dropout",
                    default=0.1,
                    type=float,
                    help="(from RoSTER) dropout ratio")
parser.add_argument('--seed',
                    type=int,
                    default=42,
                    help="(from RoSTER) random seed for training")

args = parser.parse_args()
args = vars(args)
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
) if k not in make_corpus_args + ('make_corpus', 'find_terms')}


if args['make_corpus']:
    make_corpus_args = {k: args[k] for k in make_corpus_args}
    for x in ('input', 'output'):
        make_corpus_args[x] = make_corpus_args[f'corpus_{x}']
        make_corpus_args.pop(f'corpus_{x}')
    make_corpus(**make_corpus_args)

if args['train_model']:
    train_model_args = argparse.Namespace(**train_model_args)
    train.train(train_model_args)
