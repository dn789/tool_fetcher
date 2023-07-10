# Tool Fetcher

Chrome extension and Python backend for finding software names in web pages/PDFs, and associated resources from GitHub using the GitHub API.

### Finding sofware terms:

- Uses RoSTER NER model (https://arxiv.org/abs/2109.05003) Flair Ontonotes NER model (https://huggingface.co/flair/ner-english-ontonotes-large) to find sofware names in text.

- Trains RoSTER model using an auto-labeled corpus generated from 1) relevant text (articles, web pages, textbooks) and 2) a list of software names to match in text.

- Uses the "product" tag in the Flair Ontonotes model to find possible software terms.

- See full documentation in find_terms_train_pipeline.py.

### Getting repos, account info from GitHub, web:

- Uses GitHub API to search each found software term for matching repositories.

- Enables following GitHub accounts of found repositories. Automatically scrapes blogs of accounts you're following and displays their latest blog posts/articles.

- See full documentation search_github.py and get_posts/get_posts.py.

```
.
├── backend/
│   ├── data
│   ├── find_terms (find software names in text)/
│   │   ├── corpus_input (files to train corpus)
│   │   ├── roster_models (trained NER models)
│   │   └── roster_ner (NER model code)
│   ├── get_posts  (get posts/articles from web pages)
│   ├── search_github.py (GitHub API)
│   └── server.py
└── frontend/
    └── chrome extension
```

## Setup

#

### Backend

(requires Python 3.9+)

1. Install required packages
   ```
   pip install -r requirements.txt
   ```
2. Add files (PDF, HTML and .txt files) to input folder to make corpus (default is find_terms/corpus_input).

3. Run find_terms_train_pipeline.py with desired arguments to override the defaults, or with --config and the path to a config file. Defaults in the file (and in find_terms_pipeline_config.json) should result in a good model.
   ```
   python find_terms_train_pipline.py --<arg>
   python find_terms_train_pipline.py --config <config path>
   ```
4. Get a GitHub token (https://github.com/settings/tokens/new) for access to the GitHub API.

### Frontend

1. Activate developer mode in Chrome and load chrome_extension/build as an unpacked extension.

## Usage

#

1. Run server.py in backend folder with arguments specified in data/server_config.json. For the path to the NER model (roster_model_path in find_terms_args), specify the path to the final_model.pt file. See config file for documentation of arguments.

2. Run extension on a page or selected PDF to find terms and related repos.
