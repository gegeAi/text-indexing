from sortedcontainers import SortedDict as sd


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
          return :
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
    """

    score_len = 4
    id_len = 6
    list_len_len = 4

    def __init__(self, score_function):
        self.__map = sd()
        self.__score_function = score_function

    def add_document(self, document):
        """
        Add an article in the data structure.
        parameters :
            - document : dictionary, an element of the list <FormattedDocument.matches>, of shape (id, title, date, length, text) :
                  - id : integer, the id of an article
                  - title : list of string, the title of the article tokenized
                  - date : string, when the article is written
                  - length : integer, how many words are in the article
                  - text : 2D list of string, where each list is paragraph, represented by a list of tokens
        return : None
        """
        paragraph_tokens = document["text"]
        paragraph_tokens.append(document["title"])
        seen_list = []
        for paragraph in paragraph_tokens:
            for token in paragraph:
                if token not in seen_list:
                    seen_list.append(token)
                    score = self.__score_function(token, document)
                    if token not in self.__map:
                        self.__map[token] = []
                    self.__map[token].append((document['id'], score))

    def save(self, filename):
        """
        TODO : Complete this method
        """
        return self.__encode_posting_list(self.__map.keys()[0], self.__map[self.__map.keys()[0]])
    
    def display_map(self):
        print(self.__map)

    @classmethod
    def __encode_key(cls, key):
        """
        Encode a string in binary, in the format : <key_size(1 byte)><key(key_size bytes)>
        parameters :
            - key : string, the key to encode
        return :
            - bytearray, the string encoded
        """
        output = bytearray(key, 'utf-8')
        len_part = bytearray(chr(len(output)), 'utf-8')
        if len(len_part) > 1:
            raise OutOfBoundError('Word <{}> is too long ({} characters > 255)'.format(key, len(key)))
        output = len_part + output
        return output

    @classmethod
    def __encode_score(cls, score):
        """
        Encode an integer in binary, in the format : <score(score_len bytes)>
        parameters :
            - score : integer, the number to encode
        return :
            - bytearray, the number encoded
        """
        output = bytearray(chr(score), 'utf-8')
        if len(output) > cls.score_len:
            raise OutOfBoundError('Score is too high ({} > {}'.format(score, 256*cls.score_len - 1))
        else:
            while len(output) < cls.score_len:
                output = b'\x00' + output

        return output

    @classmethod
    def __encode_doc_id(cls, doc_id):
        """
        Encode an integer in binary, in the format : <id(id_len bytes)>
        parameters :
            - doc_id : integer, the number to encode
        return :
            - bytearray, the number encoded
        """
        output = bytearray(chr(doc_id), 'utf-8')
        if len(output) > cls.id_len:
            raise OutOfBoundError('Id is too high ({} > {}'.format(doc_id, 256 * cls.id_len - 1))
        else:
            while len(output) < cls.id_len:
                output = b'\x00' + output

        return output

    @classmethod
    def __encode_list(cls, map_content):
        """
        Encode a list of (integer docid, integer score) in binary, in the format : 
        <list_len(list_len_len bytes)>( (<doc_id(id_len bytes)><score(score_len bytes)>)*N )
        parameters :
            - map_content : list, list of tuples (docid, score) where:
                - docid : integer, id of an article
                - score : integer, score of an article relative to some word
        return :
            - bytearray, the list encoded
        """
        output = bytearray()
        for (doc_id, score) in map_content:
            output += cls.__encode_doc_id(doc_id)
            output += cls.__encode_score(score)
        list_len = bytearray(chr(len(output)), 'utf-8')
        if len(list_len) > cls.list_len_len:
            raise OutOfBoundError('Posting list too long. Encoding takes {} bytes, '.format(len(output)) +\
                                  'maximum allowed is {}'.format(256*cls.list_len_len-1))
        else:
            while len(list_len) < cls.list_len_len:
                list_len = b'\x00' + list_len
        output = list_len + output
        return output

    @classmethod
    def __encode_posting_list(cls, key, map_content):
        """
        Encode a pair (key, value) in binary, in the format : 
        <key_size(1 byte)><key(key_size bytes)> <list_len(list_len_len bytes)>( (<doc_id(id_len bytes)><score(score_len bytes)>)*N )
        parameters :
            - key : string, a word, key of the map representing the index
            - map_content : list, list of tuples (docid, score) where:
                - docid : integer, id of an article
                - score : integer, score of an article relative to some word
        return :
            - bytearray, the pair encoded
        """
        return cls.__encode_key(key) + cls.__encode_list(map_content)
