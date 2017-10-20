from sortedcontainers import SortedDict as sd
from sortedcontainers import SortedList


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
    
    Class Attributes :

        - score_len : integer, the max number of bytes allowed for the encoding of a score
        - id_len : integer, the max number of bytes allowed for the encoding of a docid
        - list_len_len : integer, the max number of bytes allowed for the encoding of the size of a value associated in __map (in bytes)
          Example : if list_len_len = 4, then the maximum size of a list is pow(2, 8*4) -1 bytes
        - key_len_len : integer, the max number of bytes allowed for the encoding of the size of the key (in bytes)

    """

    score_len = 4
    id_len = 6
    list_len_len = 4
    key_len_len = 1

    def __init__(self, score_function):
        self.__map = sd()
        self.__score_function = score_function

    def add_document(self, document):
        """
        Add an article in the data structure.
        :param document : dictionary, an element of the list <FormattedDocument.matches>, of shape (id, title, date, length, text) :
                  - id : integer, the id of an article
                  - title : list of string, the title of the article tokenized
                  - date : string, when the article is written
                  - length : integer, how many words are in the article
                  - text : 2D list of string, where each list is paragraph, represented by a list of tokens
        :return:None
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
                    self.__map[token].append((document['id'], score))

    def save(self, filename):
        """
        TODO : Complete this method
        """
        output = bytearray()
        for (key, value) in self.__map.iteritems():
            output += self.__encode_posting_list(key, value)
        with open(filename, 'wb+')as f:
            f.write(output)

    @classmethod
    def __encode_number(cls, number, bin_size):
        """

        :param number:
        :return:
        """
        if number > 2 ** (bin_size*8):
            raise OutOfBoundError('Number is too long ({} > 2**({} * 8))'.format(number, bin_size))

        offset_max = (bin_size -1) * 8
        offset_actual = 0
        n_list = []
        while offset_actual <= offset_max:
            tps = [(number >> offset_actual) & 255]
            offset_actual += 8
            n_list = tps + n_list
        output = bytearray(n_list)
        return output
        
    @property
    def map(self):
        return self.__map
    
    @map.setter
    def map(self, value):
        pass

    @classmethod
    def __encode_key(cls, key):
        """
        Encode a string in binary, in the format : <key_size(1 byte)><key(key_size bytes)>
        :param key : string, the key to encode
        :return:
            - bytearray, the string encoded
        """
        output = bytearray(key, 'utf-8')
        len_part = cls.__encode_number(len(output), cls.key_len_len)
        output = len_part + output
        return output

    @classmethod
    def __encode_score(cls, score):
        """
        Encode an integer in binary, in the format : <score(score_len bytes)>
        :param score : integer, the number to encode
        :return:
            - bytearray, the number encoded
        """
        return cls.__encode_number(score, cls.score_len)

    @classmethod
    def __encode_doc_id(cls, doc_id):
        """
        Encode an integer in binary, in the format : <id(id_len bytes)>
        :param doc_id : integer, the number to encode
        :return:
            - bytearray, the number encoded
        """
        return cls.__encode_number(doc_id, cls.id_len)

    @classmethod
    def __encode_list(cls, map_content):
        """
        Encode a list of (integer docid, integer score) in binary, in the format : 
        <list_len(list_len_len bytes)>( (<doc_id(id_len bytes)><score(score_len bytes)>)*N )
        :param map_content : list, list of tuples (docid, score) where:
                - docid : integer, id of an article
                - score : integer, score of an article relative to some word
        :return:
            - bytearray, the list encoded
        """
        output = bytearray()
        for (doc_id, score) in map_content:
            output += cls.__encode_doc_id(doc_id)
            output += cls.__encode_score(score)
        list_len = cls.__encode_number(len(output), cls.list_len_len)
        output = list_len + output
        return output

    @classmethod
    def __encode_posting_list(cls, key, map_content):
        """
        Encode a pair (key, value) in binary, in the format : 
        <key_size(1 byte)><key(key_size bytes)> <list_len(list_len_len bytes)>( (<doc_id(id_len bytes)><score(score_len bytes)>)*N )
        :param key : string, a word, key of the map representing the index
        :param map_content : list, list of tuples (docid, score) where:
                - docid : integer, id of an article
                - score : integer, score of an article relative to some word
        :return:
            - bytearray, the pair encoded
        """
        return cls.__encode_key(key) + cls.__encode_list(map_content)

    @classmethod
    def __read_key(cls, file):
        """

        :param file:
        :return:
        """
        # get key
        bin_key_len = file.read(cls.key_len_len)
        if len(bin_key_len) != cls.key_len_len:
            return None, None
        key_len = cls.__decode_key_len(bin_key_len)

        bin_key = file.read(key_len)
        key = cls.__decode_key(bin_key)

        # get list len
        bin_list_len = file.read(cls.list_len_len)
        list_len = cls.__decode_list_len(bin_list_len)

        return key, list_len

    @classmethod
    def __read_key_and_posting_list(cls, file):
        """

        :param file:
        :return:
        """
        key, list_len = cls.__read_key(file)
        posting_list = cls.__decode_list(file.read(list_len))
        return key, posting_list

    @classmethod
    def decode_only_keys(cls, filename):
        """

        :param filename:
        :return:
        """
        output = []
        with open(filename, 'rb') as f:

            while True:
                position = f.tell()
                key, list_len = cls.__read_key(f)
                if key is None:
                    break
                output.append((key, position))
                f.seek(list_len, 1)

        return output

    def decode_posting_lists(self, keys, filename):
        """

        :param keys:
        :param filename:
        :return:
        """
        with open(filename, 'rb') as f:

            while True:
                key, list_len = self.__read_key(f)
                if key is None:
                    break
                # if key is one of the wanted keys
                if keys is None or key in keys:
                    posting_list = self.__decode_list(f.read(list_len))
                    self.__map[key] = posting_list
                else:
                    f.seek(list_len, 1)

    @classmethod
    def __decode_number(cls, bin_number):
        """

        :param bin_number:
        :return:
        """
        int_val = 0
        for octet in bin_number:
            int_val <<= 8
            int_val += octet
        return int_val

    @classmethod
    def __decode_key(cls, bin_key):
        """

        :param bin_key:
        :return:
        """
        return bin_key.decode('utf-8')

    @classmethod
    def __decode_key_len(cls, bin_key_len):
        """

        :param bin_key_len:
        :return:
        """
        return cls.__decode_number(bin_key_len)

    @classmethod
    def __decode_list_len(cls, bin_list_len):
        """

        :param bin_list_len:
        :return:
        """
        return cls.__decode_number(bin_list_len)

    @classmethod
    def __bin_article_regenerator(cls, bin_list, size_of_article):
        """

        :param bin_list:
        :param size_of_article:
        :return:
        """
        cur_index = 0
        while cur_index + size_of_article <= len(bin_list):
            yield bin_list[cur_index:cur_index+size_of_article]
            cur_index += size_of_article
        return

    @classmethod
    def __decode_list(cls, bin_list):
        """
        
        :param bin_list: 
        :return: 
        """
        output = []
        article_gen = cls.__bin_article_regenerator(bin_list, cls.id_len + cls.score_len)
        for bin_article in article_gen:
            output.append(cls.__decode_article(bin_article))

        return output


    @classmethod
    def __decode_article(cls, bin_article):
        """

        :param bin_article:
        :return:
        """
        bin_doc_id = bin_article[:cls.id_len]
        bin_score = bin_article[cls.id_len:]
        doc_id = cls.__decode_number(bin_doc_id)
        score = cls.__decode_number(bin_score)
        return doc_id, score

    @classmethod
    def __decode_score(cls, bin_score):
        """

        :param bin_score:
        :return:
        """
        return cls.__decode_number(bin_score)

    @classmethod
    def __decode_doc_id(cls, bin_doc_id):
        """

        :param bin_doc_id:
        :return:
        """
        return cls.__decode_number(bin_doc_id)

    @classmethod
    def merge_inverted_files(cls, filename_merge, filename_if1, filename_if2):
        """

        :param filename_merge:
        :param filename_if1:
        :param filename_if2:
        :return:
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
                        output.write(cls.__encode_posting_list(key, posting_list))

