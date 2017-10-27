from pyscripts.naive_disc_interfacer import NaiveDiscInterfacer

class SmartDiscInterfacer(NaiveDiscInterfacer):
    """
    Empty class to implement a smarter way to encode and decode an inverted file.
    Below is found another way to encode the doc_id in a posting list as :
    <doc_id (variable length)><score (score_len bytes)> <delta_doc_id (variable_length)><score (score_len bytes)> ...
    """
    
    last_id_decoded = 0
    def __init__(self):
        super().__init__()
    
#----------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------SMART ENCODING-----------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------------------------#

    @classmethod
    def __encode_number_variable_size(cls, number):
        """
        Encode an number in binary over a variable number of bytes.
        It encodes the number byte per byte over 7 bits per bytes. The strongest bit
        of each byte indicate if the newt byte still belongs to the number (yes=1, no=0)
        :param number: integer, the number to be binary encoded
        :return: bytearray, a representation of the number encoded
        """
        
        n_list = []
        while number > 127:
            to_encode_now = [(number %128) + 128]
            number >>= 7
            n_list = to_encode_now + n_list
        
        to_encode_now = [(number %128)]
        n_list = to_encode_now + n_list
        output = bytearray(n_list)
        return output

    @classmethod
    def __encode_doc_id(cls, doc_id):
        """
        Encode an a doc_id in binary, over a variable length
        :param doc_id : integer, the number to encode
        :return: bytearray, the number encoded
        """
        return cls.__encode_number_variable_size(doc_id)

    @classmethod
    def __encode_list(cls, map_content):
        """
        Encode a list of (integer docid, integer score) in binary, in the format : 
        <list_len(list_len_len bytes)>( <doc_id (variable length)><score (score_len bytes)> 
                                            <delta_doc_id (variable_length)><score (score_len bytes)> ...)
        :param map_content : list, list of tuples (docid, score) where:
                - docid : integer, id of an article
                - score : integer, score of an article relative to some word
        :return: bytearray, the list encoded
        """
        output = bytearray()
        last_id_encoded = 0
        for (doc_id, score) in map_content:
            id_to_encode = doc_id - last_id_encoded
            output += cls.__encode_doc_id(id_to_encode)
            last_id_encoded = doc_id
            output += super()._encode_score(score)
        list_len = super()._encode_number(len(output), super().list_len_len)
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
        return super()._encode_key(key) + cls.__encode_list(map_content)

#----------------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------------------------SMART DECODING-----------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------------------------#
    
    @classmethod
    def decode_number_variable_size(cls, file):
        """
        Convert a binary number of an unknown size into an integer
        Precondition : the number has been encoded following the method <encode_number_variable_size>
        :param file: bytearray, a binary representation of at least the number in which to read the number byte per byte
        :return: 
            - integer, unsigned decimal representation of the input number
            - bytearray, the array privated from the byte read
        """
        int_val = 0
        it = 0
        while True:
            bin_part = file[it]
            it += 1
            to_be_decoded = bin_part & 0x01111111
            keep_on = bin_part & 0x10000000
            int_val += to_be_decoded
            if keep_on > 0:
                int_val <<= 7
            else:
                break
        
        file = file[it:]
        return int_val, file
    
    @classmethod
    def __decode_article(cls, bin_list):
        """
        Decode the binary representation of an element of a posting list of shape (doc_id, score)
        :param bin_list: bytearray, the binary representation of a posting list, from which the next article is extracted
        :return: a tuple (doc_id, score, bin_list) where :
            - doc_id : integer, the unique id of an paper article
            - score : integer, the score of this article relative to the keyword of this posting list
            - bin_list : bytearray, the array privated from the read bytes
        """
        doc_id, bin_list = cls.decode_number_variable_size(bin_list)
        doc_id += cls.last_id_decoded
        cls.last_id_decoded = doc_id
        
        bin_score = bin_list[:super().id_len]
        score = cls.decode_number(bin_score)
        
        bin_list = bin_list[super().id_len:]
        return doc_id, score, bin_list
    
    @classmethod
    def decode_list(cls, bin_list):
        """
        Decode an entire binary posting list of shape : 
        <doc_id (variable length)><score (score_len bytes)> <delta_doc_id (variable_length)><score (score_len bytes)> ...
        :param bin_list: bytearray, the binary representation of a posting list
        :return: list, a list of tuples (doc_id, score) where each :
            - doc_id : integer, the unique id of an paper article
            - score : integer, the score of this article relative to the keyword of this posting list
        """
        output = []
        while len(bin_list) > 0:
            doc_id, score, bin_list = cls.__decode_article(bin_list)
            output.append((doc_id, score))

        cls.last_id_decoded = 0
        return output
