import nltk


class Query:

    def __init__(self, query, tokenizer=nltk, conjunctive=True):
        self.__query_token_list = tokenizer.word_tokenize(query)
        print(self.__query_token_list)
        if not conjunctive:
            raise NotImplementedError("Disjunctive query not yet supported")
        self._conjunctive = conjunctive

    def execute(self, inverted_file):
        if not self.__query_token_list:
            return []

        result = inverted_file.map[self.__query_token_list[0]]
        for token in self.__query_token_list[1:]:
            result = self.__merge_posting_list(result, inverted_file.map[token])
        return result

    @staticmethod
    def __merge_posting_list(list1, list2):
        result = []

        index_list1 = 0
        index_list2 = 0
        list1_length = len(list1)
        list2_length = len(list2)

        while index_list1 < list1_length and index_list2 < list2_length:
            document1, score1 = list1[index_list1]
            document2, score2 = list2[index_list2]

            if document1 == document2:
                result.append((document1, score1 + score2))
                index_list1 += 1
                index_list2 += 1
            elif document1 < document2:
                index_list1 += 1
            else:
                index_list2 += 1

        return result
