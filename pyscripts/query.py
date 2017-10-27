import nltk

from pyscripts.inverted_file import InvertedFile


class Query:
    """
    Class made to group features of both naive and fagin query processors.
    Initialize :
            - query: the string made of words to search.
            - tokenizer: the user provided tokenizer. It is advised to provide the same used to create the inverted
                file.
            - filename: the path to your stored inverted file.
            - conjunctive: whether the query is conjunctive or something else. If something else, an error is raised
    Attributes :
        - _conjunctive: whether the query is conjunctive or something else.
        - _filename: the path to the provided stored inverted file.
        - _query_token_list: the list of tokens in the query
    Error :
        - ValueError: if the query is empty.
        - NotImplementedError: if the query is not conjunctive.
    """
    def __init__(self, query, tokenizer, filename, conjunctive):
        self._query_token_list = list(set(tokenizer.word_tokenize(query)))  # remove duplicate
        if not self._query_token_list:
            raise ValueError("A query must be non-empty")
        if not conjunctive:
            raise NotImplementedError("Non-conjunctive query not yet supported")
        self._conjunctive = conjunctive
        self._filename = filename

    @staticmethod
    def _score_function(score_1, score_2):
        """
        Computes the combination of two scores
        :param score_1: a score
        :param score_2: another score
        :return: Combined scores = score1 + score2
        """
        return score_1 + score_2


class NaiveQuery(Query):
    """
    This class represents a query that will be executed with the naive algorithm.
    It has the same initialization and attributes than Query.
    """
    def __init__(self, query, tokenizer=nltk, filename="inverted_file.if", conjunctive=True):
        super().__init__(query, tokenizer, filename, conjunctive)

    def execute(self, top_k=5):
        """
        Execute the query represented by this instance, and return the result as a list of tuples.
        Each tuple has the document's id, then the score associated to this document.
        :param top_k: The maximum number of document that will be returned.
        :return: A list of length max(top_k, len(valid_document)), where valid_document is the collections of document
                that contains all documents matching all query terms.
                The result is a list of tuples, the first tuple's element is the document id, the second is the score
                of the document. The list is sorted according to the score of the documents.
                The documents in the list are the documents with the highest score according to the considered
                query in all the corpus.
        """
        if not self._query_token_list:
            return []

        inverted_file = InvertedFile(None)
        inverted_file.read_posting_lists(self._query_token_list, self._filename)
        try:
            result = inverted_file.map[self._query_token_list[0]]
        except KeyError:
            return []  # At least one token does not exist in the inverted file, the query can not return anything.

        for token in self._query_token_list[1:]:
            try:
                current_token_posting_list = inverted_file.map[token]
            except KeyError:
                return []  # At least one token does not exist in the inverted file, the query can not return anything.
            result = self.__merge_posting_list(result, current_token_posting_list)

        return sorted(result, key=lambda x: x[1], reverse=True)[:top_k]

    @classmethod
    def __merge_posting_list(cls, list1, list2):
        """
        Given two posting lists, each one being a list of tuples, with the document's id as the first element, and the
        score as the second element, returned the merged posting list.
        :param list1: A list of tuple, with the document's id as the first element, and the score as the second element.
                The list must be sorted according to the document's id.
        :param list2: Another posting list with the same structure.
        :return: A posting list with the same structure. This list contains a document iff the document was present in
                the two provided lists. The score of this document will be the score returned by the score function of
                the class Query.
        """
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
    """
    This class represents a query that will be executed with the Fagin's threshold algorithm.
    It has the same initialization and attributes than Query.
    """
    def __init__(self, query, tokenizer=nltk, filename="inverted_file.if", conjunctive=True):
        super().__init__(query, tokenizer, filename, conjunctive)

    def execute(self, top_k=5):
        """
        Execute the query represented by this instance, and return the result as a list of tuples.
        Each tuple has the document's id, then the score associated to this document.
        :param top_k: The maximum number of document that will be returned.
        :return: A list of length max(top_k, len(valid_document)), where valid_document is the collections of document
                that contains all documents matching all query terms.
                The result is a list of tuples, the first tuple's element is the document id, the second is the score
                of the document. The list is sorted according to the score of the documents.
                The documents in the list are the documents with the highest score according to the considered
                query in all the corpus.
        """
        # In this method, pl stands for "posting_list"
        inverted_file = InvertedFile(None)
        inverted_file.read_posting_lists(self._query_token_list, self._filename)

        # The ith element of used_pl_sorted_by_score and used_pl_sorted_by_doc_id
        # correspond to the same document
        used_pl_sorted_by_score = []
        used_pl_sorted_by_doc_id = []
        for token in self._query_token_list:
            try:
                used_pl_sorted_by_doc_id.append(inverted_file.map[token])
            except KeyError:
                return []  # At least one token does not exist in the inverted file, the query can not return anything.
            used_pl_sorted_by_score.append(self.__sort_by_score(used_pl_sorted_by_doc_id[-1]))

        tau = float("inf")
        score_min = 1e9  # not initialize to infinity in order to go through the first step of the while loop
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
    def __find_score_by_doc_id(posting_list, doc_id, default_value=-1000000):
        """
        Given a posting list and a document's id, returned the score associated with the document in the posting list.
        If the document is not in the provided posting list, return default_value.
        :param posting_list: The posting list that will be searched for the document.
        :param doc_id: The id of the document from which the score will be retrieved.
        :param default_value: The score returned if the document is not in the posting list. Default is -1000000.
        :return: The score associated to the document whose id is doc_id. If no such document is in the posting list,
                return the default value instead.
        """
        min_index = 0
        max_index = len(posting_list)
        while min_index < max_index:
            mid = (min_index + max_index) // 2
            if doc_id > posting_list[mid][0]:
                min_index = mid + 1
            elif doc_id < posting_list[mid][0]:
                max_index = mid
            else:
                break

        if doc_id == posting_list[mid][0]:
            return posting_list[mid][1]
        else:
            return default_value

    @staticmethod
    def __sort_by_score(posting_list):
        """
        Given a posting list, return the same posting list, but sorted according to the score of the documents.
        :param posting_list: A list of tuples, with the first element being the document's id, and the second the score.
        :return: The posting list sorted according to the score. The docuement with the highest score is the first
                element of the list.
        """
        return sorted(posting_list, key=lambda x: x[1], reverse=True)

    @staticmethod
    def __reverse_insert(list_, x, low_index=0, high_index=None):
        """Insert item x in list list_, and keep it reverse-sorted assuming a
        is reverse-sorted. list_ is a list of tuple, reverse-sorted according
        to the second item of the tuple

        If x is already in list_, insert it to the right of the rightmost x.

        Optional args min_index (default 0) and high_index (default len(list_)) bound the
        slice of list_ to be searched.

        /!\ Adapted to use second element of tuple x as key /!\
        """
        if low_index < 0:
            raise ValueError('min_index must be non-negative')
        if high_index is None:
            high_index = len(list_)
        while low_index < high_index:
            mid = (low_index + high_index) // 2
            if x[1] > list_[mid][1]:
                high_index = mid
            else:
                low_index = mid + 1
        list_.insert(low_index, x)
