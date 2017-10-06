from sortedcontainers import SortedDict as sd


class OutOfBoundError(Exception):
    pass


class InvertedFile(object):

    score_len = 4
    id_len = 6
    list_len_len = 4

    def __init__(self, score_function):
        self.map = sd()
        self.__score_function = score_function

    def add_document(self, document):
        paragraph_tokens = document["text"]
        paragraph_tokens.append(document["title"])
        seen_list = []
        for paragraph in paragraph_tokens:
            for token in paragraph:
                if token not in seen_list:
                    seen_list.append(token)
                    score = self.__score_function(token, document)
                    if token not in self.map:
                        self.map[token] = []
                    self.map[token].append((document['id'], score))

    def save(self, filename):
        return self.__encode_posting_list(self.map.keys()[0], self.map[self.map.keys()[0]])

    @classmethod
    def __encode_key(cls, key):
        output = bytearray(key, 'utf-8')
        len_part = bytearray(chr(len(output)), 'utf-8')
        if len(len_part) > 1:
            raise OutOfBoundError('Word <{}> is too long ({} characters > 255)'.format(key, len(key)))
        output = len_part + output
        return output

    @classmethod
    def __encode_score(cls, score):
        output = bytearray(chr(score), 'utf-8')
        if len(output) > cls.score_len:
            raise OutOfBoundError('Score is too high ({} > {}'.format(score, 256*cls.score_len - 1))
        else:
            while len(output) < cls.score_len:
                output = b'\x00' + output

        return output

    @classmethod
    def __encode_doc_id(cls, doc_id):
        output = bytearray(chr(doc_id), 'utf-8')
        if len(output) > cls.id_len:
            raise OutOfBoundError('Id is too high ({} > {}'.format(doc_id, 256 * cls.id_len - 1))
        else:
            while len(output) < cls.id_len:
                output = b'\x00' + output

        return output

    @classmethod
    def __encode_list(cls, map_content):
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
        return cls.__encode_key(key) + cls.__encode_list(map_content)
