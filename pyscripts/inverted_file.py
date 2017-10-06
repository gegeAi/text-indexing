from sortedcontainers import SortedDict as sd


class InvertedFile(object):

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
                        self.map[token] = [0, []]
                    self.map[token][1].append((document['id'], score))
                    self.map[token][0] += 1