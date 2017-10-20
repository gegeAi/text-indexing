from sortedcontainers import SortedDict as sd
from sortedcontainers import SortedList
from pyscripts.naive_disc_interfacer import NaiveDiscInterfacer as ndi
import time
from pyscripts.inverted_file import InvertedFile
from pyscripts.formatted_document import FormattedDocument
from pyscripts.tokenizer import Tokenizer
import glob
import time
import os
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError


def read_files(paths, n=-1):
    """
    Read n files from a list of paths and convert them as xml trees. A root node <RAC> is added to every file to
    avoid some ParseError
    parameters :
        - paths : enumeration of strings, a list of absolute paths where data have to be read (data must be xml files)
        - n : number of files needed to be read, if -1, every possible files will be read
    return :
        - a list of len=(min(n, number of files) if n != -1, else number of files) of xml trees representations
          of the documents
    """
    output = []
    for path in paths:
        try:
            txt = open(path, 'r').read()
            output.append(ET.fromstring('<RAC>' + txt + '</RAC>'))
            n -= 1
            print('Successfully parsed document <{}>'.format(path))
        except ParseError:
            print('Can\'t parse document <{}>. Doesn\'t matter, skip'.format(path))
        except IsADirectoryError:
            print('Can\'t parse directory <{}>. Doesn\'t matter, skip'.format(path))
        if n == 0:
            return output
    return output


def score(token, document):
    paragraph_tokens = document['text'].copy()
    paragraph_tokens.append(document['title'])
    token_count = 0
    for paragraph in paragraph_tokens:
        for word in paragraph:
            if word == token:
                token_count += 1
    return token_count


LATIMES_PATH = './latimes'
files = glob.iglob(LATIMES_PATH + '/*')

start_time = time.time()

FILE_MERGE_PREFIX = "mergedfile"
FILE_NON_MERGE_PREFIX = "docfile"
merged_file_index = 0
old_merge_file_name = None
old_merge_time = 0.0

logfilename = "benchmerge.log"
with open(logfilename, "w") as logfile:
    for file in files:
        start_time = time.time()
        # create an inverted file for the current doc
        inverted_file = InvertedFile(score)
        file_name = os.path.basename(file)
        out_file_name = FILE_NON_MERGE_PREFIX + file_name
        xml_file = read_files([file])
        fd = FormattedDocument(xml_file, tokenizer=Tokenizer())
        for doc in fd.matches:
            inverted_file.add_document(doc)
        inverted_file.save(out_file_name)
        if_save_time = time.time()
        # merge it into the old merge file
        if old_merge_file_name is not None:
            new_merge_file_name = FILE_MERGE_PREFIX + str(merged_file_index)
            InvertedFile.merge_inverted_files(new_merge_file_name, old_merge_file_name, out_file_name)
            old_merge_file_name = new_merge_file_name
            merged_file_index += 1
        else:
            old_merge_file_name = out_file_name
        merge_time = time.time()
        old_merge_time += merge_time - start_time
        logfile.write(str(if_save_time - start_time) + "," + str(merge_time - if_save_time) +
                      "," + str(merge_time - start_time) + "," + str(old_merge_time))
