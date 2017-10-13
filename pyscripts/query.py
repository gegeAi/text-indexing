import nltk


class Query:
    def __init__(self, query, tokenizer=nltk, conjunctive=True):
        self._query_token_list = set(tokenizer.word_tokenize(query))
        if not conjunctive:
            raise NotImplementedError("Disjunctive query not yet supported")
        self._conjunctive = conjunctive


class NaiveQuery(Query):

    def __init__(self, query, tokenizer=nltk, conjunctive=True):
        super().__init__(query, tokenizer, conjunctive)

    def execute(self, inverted_file, top_k=5):
        if not self._query_token_list:
            return []

        result = inverted_file.map[self._query_token_list[0]]
        for token in self._query_token_list[1:]:
            result = self.__merge_posting_list(result, inverted_file.map[token])

        return sorted(result, key=lambda x: x[1], reverse=True)[:top_k]

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


class FaginQuery(Query):
    def __init__(self, query, tokenizer=nltk, conjunctive=True):
        super.__init__(query, tokenizer, conjunctive)

    def execute(self, inverted_file, top_k=5):
        # The ith element of used_posting_list_sorted_by_score and used_posting_list_sorted_by_doc_id
        # correspond to the same document
        used_posting_list_sorted_by_score = []
        used_posting_list_sorted_by_doc_id = []
        for token in self._query_token_list:
            used_posting_list_sorted_by_doc_id.append(inverted_file.map[token])
            used_posting_list_sorted_by_score.append(self.__sort_by_score(used_posting_list_sorted_by_doc_id[-1]))

        tau = 1e9
        score_min = 1e9
        current_best = []
        index_table = [0 for _ in range(0, len(used_posting_list_sorted_by_score))]
        while len(current_best) < top_k and score_min < tau:
            for index, i in enumerate(index_table):
                document, current_document_score = used_posting_list_sorted_by_score[i][index]
                # TODO: Rename index_bis (and j?)
                for index_bis, j in enumerate(used_posting_list_sorted_by_doc_id):
                    if i != j:
                        current_document_score += self.__find_score_by_doc_id(used_posting_list_sorted_by_doc_id[j],
                                                                              document)



    @staticmethod
    def __find_score_by_doc_id(posting_list, doc_id):
        for document, score in posting_list:
            if doc_id == document:
                return score

    @staticmethod
    def __sort_by_score(posting_list):
        return sorted(posting_list, key=lambda x: x[1], reverse=True)
