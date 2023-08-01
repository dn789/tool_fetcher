# Tool Fetcher

Chrome extension and Python backend for finding **(1)** software names in web pages/PDFs, and **(2)** associated resources from GitHub/the web.

## Overview

### Find software mentions on the web

- Trains a RoSTER named entity recognition model (https://arxiv.org/abs/2109.05003) using an auto-labeled corpus generated from relevant texts (articles, web pages, textbooks) and a list of software names to match in them.

- Also uses the "product" tag in a Flair NER model fine-tuned on the Ontonotes dataset (https://huggingface.co/flair/ner-english-ontonotes-large) to find software names.

  <em>See full documentation in find_terms_train_pipeline.py.</em>

### Get repos, follow GitHub accounts

- Uses GitHub API to search each found software name for repositories.

- Enables following GitHub accounts of found repositories. Scrapes blogs of accounts you're following and displays their latest blog posts/articles.

  <em>See full documentation search_github.py and get_posts/get_posts.py.</em>

**Directory tree**

```
.
├── backend
│   ├── data
│   ├── find_terms
│   ├── get_posts
│   ├── find_terms_train_pipeline.py (train RoSTER model)
│   ├── search_github.py
│   └── server.py (backend for chrome extension)
└── frontend
    └── chrome extension
```

## Setup

### Backend

(requires Python 3.9+)

1. **Install required packages**
   ```
   pip install -r requirements.txt
   ```
2. **Add files (PDF, HTML and .txt files) to the input folder** to make a corpus (default is <em>find_terms/corpus_input</em>).

3. **Run <em>find_terms_train_pipeline.py</em>** with or without any arguments, or with -<em>-config</em> and the path to a config file. Default parameters (in python file and <em>find_terms_pipeline_config.json</em>) should result in a good model.

   ```
   python find_terms_train_pipline.py --<arg>
   python find_terms_train_pipline.py --config <config path>
   ```

   Directories don't need to be specified unless default locations are being overriden (ie. when creating multiple training/test sets from a single corpus or training multiple models) See <em>find_terms_train_pipeline.py </em> for full documentation.

   **Pipeline**:

   **corpus_input** (PDFs, HTML and text files to tag. Default: <em>find_terms/corpus_input</em>) \
    ↓ \
   <em>auto label with terms from lists </em>\
    ↓ \
   **corpus_output** (Default: <em>find_terms/corpus</em>) \
   └─ **train_test_dir** (Tagged training/test sets. Default: <em>find_terms/corpus/train_test_dir/set_1</em>)\
    ↓ \
   <em>train RoSTER on corpus training set</em> \
    ↓ \
   **roster_model_dir** (Trained RoSTER model. Default: <em>find_terms/models/model_1</em>) \
    ↓ \
   <em>use with **Flair Ontonotes model** to find software mentions in text</em>

4. **Get a GitHub token** (https://github.com/settings/tokens/new) and add it to <em>server_config.jsonc</em> (<em>token</em> in <em>github_args</em>) to access the GitHub API.

### Frontend

1. **Activate developer mode** in Chrome
2. **Load <em>chrome_extension/build</em>** as an unpacked extension.

## Usage

1. **Run <em>server.py</em>** with arguments specified in <em>server_config.jsonc</em>. Only the GitHub token needs to be specified if using defaults. See <em>server_config.jsonc</em> for documentation of arguments.

2. **Run extension** on a web page or uploaded PDF.

### Notes

- To switch to a different RoSTER model run, set <em>roster_model_path</em> in <em>server_config.jsonc</em> to the path to the desired model's .pt file.
