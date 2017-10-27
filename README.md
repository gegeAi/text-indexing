# First launch
`git clone https://github.com/gegeAi/text-indexing.git`
`cd text-indexing`
`pip3 install -r requirements.txt`
`jupyter notebook`
Then open 'text index creating.ipynb' and execute the example.
Make sure to have a folder with latimes files, and check the path to this folder in the notebooks (variable LATIMES_PATH).

# Folder description
## Root
The root of the project comprises files with the extension '.ipynb'. They should be read with jupyter, as it allows to launch code snippet directly.

## pyscripts
This folder comprises the python modules call by the notebooks. Here is a short descriptions of the roles of each module:
* inverted_file.py : This module is responsible of creating, saving and loading the inverted file.
* tokenizer.py : This module is responsible of the tokenization. It is based on nltk, with some more actions performed.
* formated_document.py : This module handle the parsing of xml document, and transform them in a format easier to read for other modules.
* query.py : This module handle the execution of queries, through two differents algrorithms.

## benchmark
This folder contains all benchmarks output, with several differents formats (csv, txt or png). 

## presentation
This folder contains the presentation used, with formated benchmark raw data.

