from sortedcontainers import SortedDict as sd
from sortedcontainers import SortedList
from pyscripts.naive_disc_interfacer import NaiveDiscInterfacer as ndi


class OutOfBoundError(Exception):
    """
    Exception whose vocation is to be thrown when someone try to encode something
    over more bytes than allowed
    """
    pass


class InvertedFile(object):
    """
    Class made to represent an index in memory, with the final purpose of saving and reloading it chunk-by-chunk.
    Initialize :
        - score_function : function of prototype [integer function(token, document)], which will be used to 
          compute the part of the score relative to a unique word in a document that will be saved on disc.
          parameters :
              - token : string, a tokenized word expected to be found in a document
              - document : dictionary, an element of the list <FormattedDocument.matches>, of shape (id, title, date, length, text) :
                  - id : integer, the id of an article
                  - title : list of string, the title of the article tokenized
                  - date : string, when the article is written
                  - length : integer, how many words are in the article
                  - text : 2D list of string, where each list is paragraph, represented by a list of tokens
          - return:
              - integer, a score relative to a word and an article. Please note that the score is expected to be relative 
                to a specific "word", not to "the word XXX at the position XXX". For example, in the article "The black hound ate the 
                black bear.", there is a single, unique score relative to the word "black". 

    Attributes :
        - __map : SortedDict, the structure used to store the index in memory. Shape (key: string, value: List)
            - key : string, words found in various documents
            - value : list, list of pairs (docid, score) :
                - docid : integer, the id of a document to identify it in the index
                - score : integer, the score computed by __score_function for the association (key, doc)
       - __score_function : the score_function sent in parameter for __init__, memorized by the index (see Initialize/score_function for 
         more infos)
    """

    def __init__(self, score_function, disc_interfacer=ndi):
        self.__map = sd()
        self.__score_function = score_function
        self.di = disc_interfacer

    @property
    def map(self):
        """
        Getter for the attribute __map
        :return: SortedDict, a reference to the __map attribute
        """
        return self.__map
    
    @map.setter
    def map(self, value):
        """
        Setter for the attribute __map, forbidding outside modifications
        """
        pass
    
    def add_document(self, document):
        """
        Add an article in the data structure.
        :param document : dictionary, an element of the list <FormattedDocument.matches>, of shape (id, title, date, length, text) :
                  - id : integer, the id of an article
                  - title : list of string, the title of the article tokenized
                  - date : string, when the article is written
                  - length : integer, how many words are in the article
                  - text : 2D list of string, where each list is paragraph, represented by a list of tokens
        :return: None
        """
        paragraph_tokens = document["text"].copy()
        paragraph_tokens.append(document["title"])
        seen_list = []
        for paragraph in paragraph_tokens:
            for token in paragraph:
                if token not in seen_list:
                    seen_list.append(token)
                    score = self.__score_function(token, document)
                    if token not in self.__map:
                        self.__map[token] = SortedList()
                    self.__map[token].add((document['id'], score))
                    
#----------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------SAVE AND LOAD------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------------------------#

    def get_object_as_array(self):
        """
        Used for testing purposes, only encode the object without saving it
        :return: bytearray, a binary representation of the full object
        """
        output = bytearray()
        for (key, value) in self.__map.iteritems():
            output += self.di.encode_posting_list(key, value)
        return output
    
    def save(self, filename):
        """
        Save the InvertedFile to the disc
        :param filename: string, the path of the inverted file to be saved on disc
        :return: None
        """
        output = bytearray()
        for (key, value) in self.__map.iteritems():
            output += self.di.encode_posting_list(key, value)
        with open(filename, 'wb+')as f:
            f.write(output)
            
    def read_posting_lists(self, keys, filename):
        """
        Read and decode the posting lists correspoself.ding to their associated keys given in parameters, from a given file.
        Load them into the current object.
        :param keys: list of string, represents the posting lists that need to be decoded
        :param filename: string, the name of the file to read on disc
        :return: None
        """
        with open(filename, 'rb') as f:

            while True:
                key, list_len = self.__read_key_and_list_len(f)
                if key is None:
                    break
                # if key is one of the wanted keys
                if keys is None or key in keys:
                    posting_list = self.di.decode_list(f.read(list_len))
                    self.__map[key] = posting_list
                else:
                    f.seek(list_len, 1)
    
    @classmethod
    def read_only_keys(cls, filename):
        """
        Read a binary file and extract only the keys, skipping the reading of their associated posting lists
        :param filename: string, the path of the inverted file to be read on disc
        :return: list of string, where each element is the representation of a keyword
        """
        output = []
        with open(filename, 'rb') as f:

            while True:
                position = f.tell()
                key, list_len = cls.__read_key_and_list_len(f)
                if key is None:
                    break
                output.append((key, position))
                f.seek(list_len, 1)

        return output
                    
    @classmethod
    def __read_key_and_list_len(cls, file):
        """
        Read the next few bytes of a binary file and decode them.
        Precoself.dition : The next bytes must represent a key and the length of an associated posting list shaped as :
        <key_size(1 byte)><key(key_size bytes)><list_len(list_len_len bytes)>
        :param file: File, the binary file to read the next bytes in
        :return: a tuple (key, list_len) where :
            - key : string, the key word associated with the next posting list
            - list_len : integer, the length (in bytes) of the next posting list
        """
        # get key
        bin_key_len = file.read(self.di.key_len_len)
        if len(bin_key_len) != self.di.key_len_len:
            return None, None
        key_len = self.di.decode_number(bin_key_len)

        bin_key = file.read(key_len)
        key = bin_key.decode('utf-8')

        # get list len
        bin_list_len = file.read(self.di.list_len_len)
        list_len = self.di.decode_number(bin_list_len)

        return key, list_len
    
    @classmethod
    def __read_key_and_posting_list(cls, file):
        """
        Read the next few bytes of a binary file and decode them.
        Precondition : The next bytes must represent posting list and its associated key shaped as :
        <key_size(1 byte)><key(key_size bytes)><list_len(list_len_len bytes)>( (<doc_id(id_len bytes)><score(score_len bytes)>)*N )
        :param file: File, the binary file to read the next bytes in
        :return: a tuple (key, posting_list) where :
            - key : string, the key word associated with the next posting list
            - posting_list : list, a list of tuples (doc_id, score) where each :
                - doc_id : integer, the unique id of an paper article
                - score : integer, the score of this article relative to the keyword of this posting list
        """
        key, list_len = cls.__read_key_and_list_len(file)
        posting_list = self.di.decode_list(file.read(list_len))
        return key, posting_list

#----------------------------------------------------------------------------------------------------------------------------------------#
#--------------------------------------------------MERGE INVERTED FILES------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------------------------#

    @classmethod
    def merge_inverted_files(cls, filename_merge, filename_if1, filename_if2):
        """
        Merge two inverted files saved on disc into one.
        :param filename_merge: string, the path to the newly created inverted file
        :param filename_if1: string, the path to the first inverted file to merge
        :param filename_if2: string, the path to the second inverted file to merge
        :return: None
        """

        with open(filename_merge, 'wb+') as output:
            with open(filename_if1, 'rb') as if1:
                with open(filename_if2, 'rb') as if2:
                    key_if1, pl_if1 = cls.__read_key_and_posting_list(if1)
                    key_if2, pl_if2 = cls.__read_key_and_posting_list(if2)
                    while True:

                        if key_if1 is None and key_if2 is None:
                            break
                        elif key_if1 is not None and (key_if2 is None or key_if1 < key_if2):
                            posting_list = pl_if1
                            key = key_if1
                            key_if1, pl_if1 = cls.__read_key_and_posting_list(if1)
                        elif key_if1 is None or key_if1 > key_if2:
                            posting_list = pl_if2
                            key = key_if2
                            key_if2, pl_if2 = cls.__read_key_and_posting_list(if2)
                        else:
                            posting_list = pl_if1 + pl_if2
                            key = key_if1
                            key_if1, pl_if1 = cls.__read_key_and_posting_list(if1)
                            key_if2, pl_if2 = cls.__read_key_and_posting_list(if2)
                        output.write(self.di.encode_posting_list(key, posting_list))


if __name__ == "__main__":
    from pyscripts.formatted_document import FormattedDocument
    from pyscripts.tokenizer import Tokenizer
    import glob
    import time
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
    xml_files = read_files(files)

    number_of_files = len(xml_files)
    time_output_filename = "inverted_file/time.txt"
    with open(time_output_filename, "a") as time_output:
        time_output.write("\n\n========== Run beginning at " + str(time.time()) + "===========\n")
        while number_of_files > 0:
            inverted_file = InvertedFile(score)
            print("Begin to create inverted file with {} files".format(number_of_files))
            current_xml_files = xml_files[0:number_of_files]
            start_time = time.time()
            for xml_file in current_xml_files:
                fd = FormattedDocument(xml_file, tokenizer=Tokenizer())
                for doc in fd.matches:
                    inverted_file.add_document(doc)
            end_time = time.time()

            time_output.write("number_of_files : " + str(number_of_files) + " time : " + str(end_time - start_time) +
                              "\n")
            inverted_file.save("inverted_file/inverted_file_{}.if".format(number_of_files))
            number_of_files -= 50


