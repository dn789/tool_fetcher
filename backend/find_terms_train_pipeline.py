import argparse
from find_terms.make_corpus import make_corpus

parser = argparse.ArgumentParser(description='Find terms training pipeline')
parser.add_argument('--make_corpus', type=str,
                    default=True, help='Input folder')
parser.add_argument('--input_folder', type=str, default='find_terms/input/',
                    help='Input folder')
parser.add_argument('--output_folder', type=str, default='find_terms/corpus/',
                    help='Output folder')
parser.add_argument('--train_test_split', type=float, default=(85, 15), nargs='+',
                    help='Train/dev/test split')
parser.add_argument('--dont_filter_sents', action=argparse.BooleanOptionalAction,
                    help='Don\'t sentences that are too long/don\'t have enough letters.')
parser.add_argument('--neg_sents_proportion_pdf', type=float, default=0,
                    help='Percentage of sentences without entities for pdfs')
parser.add_argument('--neg_sents_proportion_web', type=float, default=0,
                    help='Percentage of sentences without entities for web documents or text files')

args = parser.parse_args()
# print(args.dont_filter_sents)
if args.make_corpus:
    make_corpus(**vars(args))
