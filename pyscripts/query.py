import nltk


class Query:
    def __init__(self, query, tokenizer=nltk, filename="inverted_file.if", conjunctive=True):
        self._query_token_list = list(set(tokenizer.word_tokenize(query)))  # remove duplicate
        if not self._query_token_list:
            raise ValueError("A query must be non-empty")
        if not conjunctive:
            raise NotImplementedError("Disjunctive query not yet supported")
        self._conjunctive = conjunctive
        self._filename = filename

    @staticmethod
    def _score_function(score_1, score_2):
        return score_1 + score_2


class NaiveQuery(Query):
    def __init__(self, query, tokenizer=nltk, filename="inverted_file.if", conjunctive=True):
        super().__init__(query, tokenizer, filename, conjunctive)

    def execute(self, inverted_file, top_k=5):
        # TODO: return a wrong result for the query "house divorce" on the document la123189
        if not self._query_token_list:
            return []

        inverted_file.read_posting_lists(self._query_token_list, self._filename)
        result = inverted_file.map[self._query_token_list[0]]
        for token in self._query_token_list[1:]:
            result = self.__merge_posting_list(result, inverted_file.map[token])

        return sorted(result, key=lambda x: x[1], reverse=True)[:top_k]

    @classmethod
    def __merge_posting_list(cls, list1, list2):
        result = []

        index_list1 = 0
        index_list2 = 0
        list1_length = len(list1)
        list2_length = len(list2)

        while index_list1 < list1_length and index_list2 < list2_length:
            document1, score_1 = list1[index_list1]
            document2, score_2 = list2[index_list2]

            if document1 == document2:
                result.append((document1, cls._score_function(score_1, score_2)))
                index_list1 += 1
                index_list2 += 1
            elif document1 < document2:
                index_list1 += 1
            else:
                index_list2 += 1

        return result


class FaginQuery(Query):
    def __init__(self, query, tokenizer=nltk, filename="inverted_file.if", conjunctive=True):
        super().__init__(query, tokenizer, filename, conjunctive)

    def execute(self, inverted_file, top_k=5):
        # In this method, pl stands for "posting_list"

        inverted_file.read_posting_lists(self._query_token_list, self._filename)

        # The ith element of used_pl_sorted_by_score and used_pl_sorted_by_doc_id
        # correspond to the same document
        used_pl_sorted_by_score = []
        used_pl_sorted_by_doc_id = []
        for token in self._query_token_list:
            used_pl_sorted_by_doc_id.append(inverted_file.map[token])
            used_pl_sorted_by_score.append(self.__sort_by_score(used_pl_sorted_by_doc_id[-1]))
        tau = float("inf")
        score_min = 1e9 # not initialize to infinity in order to go through the first step of the while loop
        current_best = []
        index_table = [0 for _ in range(0, len(used_pl_sorted_by_score))]
        sorted_access_count = 0
        seen_documents = set()

        while len(current_best) < top_k or score_min < tau:
            for current_pl_index, index_in_current_pl in enumerate(index_table):
                # Search for the first unseen document from the current posting list, and increment the
                # current posting list's index in the index_table
                while True:
                    current_pl_sorted_by_score = used_pl_sorted_by_score[current_pl_index]
                    try:
                        document, current_document_score = (current_pl_sorted_by_score[index_in_current_pl])
                    except IndexError:  # All relevant documents have been seen
                        return current_best
                    index_in_current_pl += 1
                    if document not in seen_documents:
                        seen_documents.add(document)
                        sorted_access_count += 1
                        index_table[current_pl_index] = index_in_current_pl
                        break

                # Search other posting list to compute the score of the current document
                for other_pl_index, index_in_other_pl in enumerate(index_table):
                    if current_pl_index != other_pl_index:
                        other_pl = used_pl_sorted_by_doc_id[other_pl_index]
                        other_document_score = self.__find_score_by_doc_id(other_pl, document)
                        current_document_score = self._score_function(current_document_score, other_document_score)

                # If a word is not in the document, a negative score will be affected
                if current_document_score < 0:
                    continue

                if len(current_best) < top_k:
                    self.__reverse_insert(current_best, [document, current_document_score])
                    score_min = current_best[-1][1]
                elif score_min < current_document_score:
                    current_best.pop()
                    self.__reverse_insert(current_best, [document, current_document_score])
                    score_min = current_best[-1][1]
                if sorted_access_count >= len(index_table):
                    tau = 0
                    for tau_pl_index, index_in_tau_pl in enumerate(index_table):
                        _, tau_i = used_pl_sorted_by_score[tau_pl_index][index_in_tau_pl - 1]
                        tau += tau_i
        return current_best

    @staticmethod
    def __find_score_by_doc_id(posting_list, doc_id, default_value=-1000):
        for document, score in posting_list:
            if doc_id == document:
                return score
        return default_value  # If a document is not in a posting list, return the default value

    @staticmethod
    def __sort_by_score(posting_list):
        return sorted(posting_list, key=lambda x: x[1], reverse=True)

    @staticmethod
    def __reverse_insert(list_, x, min_index=0, high_index=None):
        """Insert item x in list list_, and keep it reverse-sorted assuming a
        is reverse-sorted. list_ is a list of tuple, reverse-sorted according
        to the second item of the tuple

        If x is already in list_, insert it to the right of the rightmost x.

        Optional args min_index (default 0) and high_index (default len(list_)) bound the
        slice of list_ to be searched.

        /!\ Adapted to use second element of tuple x as key /!\
        """
        if min_index < 0:
            raise ValueError('min_index must be non-negative')
        if high_index is None:
            high_index = len(list_)
        while min_index < high_index:
            mid = (min_index + high_index) // 2
            if x[1] > list_[mid][1]:
                high_index = mid
            else:
                min_index = mid + 1
        list_.insert(min_index, x)


if __name__ == "__main__":
    from pyscripts.inverted_file import InvertedFile
    from pyscripts.tokenizer import Tokenizer

    top_k = 8
    inverted_file = InvertedFile(None)
    print("Create and execute fagin query")
    query = FaginQuery("the horse in the field", Tokenizer())
    print(query.execute(inverted_file, top_k))

    print("Create and execute naive query")
    naive_query = NaiveQuery("the, it", Tokenizer())
    print(naive_query.execute(inverted_file, top_k))
