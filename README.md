# First launch
`git clone https://github.com/gegeAi/text-indexing.git`
`cd text-indexing`
`pip3 install -r requirements.txt`
`jupyter notebook`
Then open 'text index creating.ipynb' and execute the example.
Make sure to have a folder with latimes files, and check the path to this folder in the notebooks (variable LATIMES_PATH).

# Folder description
## Root
The root of the project comprises files with the extension '.ipynb'. They should be read with jupyter, as it allows to launch code snippet directly. Here is a short description of each notebook:
* Inverted File Benchmark.ipynb : This notebook contains different code snippet that allow a benchmarking of the functionnality of the inverted file.
* Inverted File Test.ipynb : This notebook contains some basic test of the functionnalies of the inverted file.
* Query Benchmark.ipynb : This notebook contains a benchmark of the queries over several parameters.
* Text index creating.ipynb : This notebook shows how to index an xml document, in order to build an inverted file.

## pyscripts
This folder comprises the python modules call by the notebooks. Here is a short descriptions of the roles of each module:
* inverted_file.py : This module is responsible of creating, saving and loading the inverted file.
* tokenizer.py : This module is responsible of the tokenization. It is based on nltk, with some more actions performed.
* formated_document.py : This module handles the parsing of xml document, and transform them in a format easier to read for other modules.
* query.py : This module handles the execution of queries, through two differents algrorithms.
* naive\_disc\_interfacer.py / smart\_disc\_interfacer.py : These modules handle the encoding and decoding of inverted file on the disc, with binary format.

## benchmark
This folder contains all benchmarks output, with several differents formats (csv, txt or png). 

## presentation
This folder contains the presentation used, with formated benchmark raw data.

## inverted_file
This folder contains some example inverted file, that can be used for testing the query functionnality. 

