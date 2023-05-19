# Tool Fetcher

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
### Frontend
1. Activate developer mode in Chrome and load chrome_extension/build as an unpacked extension.


## Usage
#
1. Run server.py in backend folder with arguments specified in data/server_config.json.
2. Run extension on a page or selected PDF to find terms and related repos. 