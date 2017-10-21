class NaiveDiscInterfacer(object):
    """
    Empty class used as namespace for the naive implementation of saving and reading an InvertedFile in binary
    
    Class Attributes :

        - score_len : integer, the max number of bytes allowed for the encoding of a score
        - id_len : integer, the max number of bytes allowed for the encoding of a docid
        - list_len_len : integer, the max number of bytes allowed for the encoding of the size of a value associated in _map (in bytes)
          Example : if list_len_len = 4, then the maximum size of a list is pow(2, 8*4) -1 bytes
        - key_len_len : integer, the max number of bytes allowed for the encoding of the size of the key (in bytes)

    """

    score_len = 4
    id_len = 6
    list_len_len = 4
    key_len_len = 1
    
    def __init__(self):
        pass
    
#----------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------NAIVE ENCODING-----------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------------------------#

    @classmethod
    def _encode_number(cls, number, bin_size):
        """
        Encode an number in binary over an arbitrary number of bytes
        :param number: integer, the number to be binary encoded
        :param bin_size: integer, the number of bytes to encode the number over
        :return: bytearray, a representation of the number encoded
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

    @classmethod
    def _encode_key(cls, key):
        """
        Encode a string in binary, in the format : <key_size(key_len_len byte)><key(key_size bytes)>
        :param key : string, the key to encode
        :return: bytearray, the string encoded
        """
        output = bytearray(key, 'utf-8')
        len_part = cls._encode_number(len(output), cls.key_len_len)
        output = len_part + output
        return output

    @classmethod
    def _encode_score(cls, score):
        """
        Encode an integer in binary, in the format : <score(score_len bytes)>
        :param score : integer, the number to encode
        :return: bytearray, the number encoded
        """
        return cls._encode_number(score, cls.score_len)

    @classmethod
    def _encode_doc_id(cls, doc_id):
        """
        Encode an integer in binary, in the format : <id(id_len bytes)>
        :param doc_id : integer, the number to encode
        :return: bytearray, the number encoded
        """
        return cls._encode_number(doc_id, cls.id_len)

    @classmethod
    def _encode_list(cls, map_content):
        """
        Encode a list of (integer docid, integer score) in binary, in the format : 
        <list_len(list_len_len bytes)>( (<doc_id(id_len bytes)><score(score_len bytes)>)*N )
        :param map_content : list, list of tuples (docid, score) where:
                - docid : integer, id of an article
                - score : integer, score of an article relative to some word
        :return: bytearray, the list encoded
        """
        output = bytearray()
        for (doc_id, score) in map_content:
            output += cls._encode_doc_id(doc_id)
            output += cls._encode_score(score)
        list_len = cls._encode_number(len(output), cls.list_len_len)
        output = list_len + output
        return output

    @classmethod
    def encode_posting_list(cls, key, map_content):
        """
        Encode a pair (key, value) in binary, in the format : 
        <key_size(1 byte)><key(key_size bytes)> <list_len(list_len_len bytes)>( (<doc_id(id_len bytes)><score(score_len bytes)>)*N )
        :param key : string, a word, key of the map representing the index
        :param map_content : list, list of tuples (docid, score) where:
                - docid : integer, id of an article
                - score : integer, score of an article relative to some word
        :return: bytearray, the pair encoded
        """
        return cls._encode_key(key) + cls._encode_list(map_content)

#----------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------NAIVE DECODING-----------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------------------------#
    
    @classmethod
    def decode_number(cls, bin_number):
        """
        Convert a binary number into an integer
        :param bin_number: bytearray, binary representation of a number
        :return: integer, unsigned decimal representation of the input number
        """
        int_val = 0
        for octet in bin_number:
            int_val <<= 8
            int_val += octet
        return int_val
    
    @classmethod
    def _decode_article(cls, bin_article):
        """
        Decode the binary representation of an element of a posting list of shape (doc_id, score)
        :param bin_article: bytearray, the binary representation of an element of a posting list, encoded as 
                            <doc_id(id_len bytes)><score(score_len bytes)>
        :return: a tuple (doc_id, score) where :
            - doc_id : integer, the unique id of an paper article
            - score : integer, the score of this article relative to the keyword of this posting list
        """
        bin_doc_id = bin_article[:cls.id_len]
        bin_score = bin_article[cls.id_len:]
        doc_id = cls.decode_number(bin_doc_id)
        score = cls.decode_number(bin_score)
        return doc_id, score
    
    @classmethod
    def _bin_article_regenerator(cls, bin_list, size_of_article):
        """
        Generator, cut a binary posting list into separate tuples (doc_id, score) and yield them
        :param bin_list: bytearray, the binary representation of a posting list
        :param size_of_article: integer, the number of bytes it takes to represent a tuple (doc_id, score)
        :return: yield bytearray, the binary representation of an element of the posting list
        """
        cur_index = 0
        while cur_index + size_of_article <= len(bin_list):
            yield bin_list[cur_index:cur_index+size_of_article]
            cur_index += size_of_article
        return
    
    @classmethod
    def decode_list(cls, bin_list):
        """
        Decode an entire binary posting list of shape : 
        (<doc_id(id_len bytes)><score(score_len bytes)>)*N
        :param bin_list: bytearray, the binary representation of a posting list
        :return: list, a list of tuples (doc_id, score) where each :
            - doc_id : integer, the unique id of an paper article
            - score : integer, the score of this article relative to the keyword of this posting list
        """
        output = []
        article_gen = cls._bin_article_regenerator(bin_list, cls.id_len + cls.score_len)
        for bin_article in article_gen:
            output.append(cls._decode_article(bin_article))

        return output
