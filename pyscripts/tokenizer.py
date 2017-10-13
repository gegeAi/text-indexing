import nltk
nltk.download('punkt')

class Tokenizer:
    """
    Class made to provide better tokenization features than nltk only.
    It can remove punctuation and stem tokens.
    Initialize :
            punctuation : A list of symbols you want to remove from the tokens if they are found alone.
                Default is ['!', '?', '.', ',', ';', ':', '"', "'", '(', ')', '-', "''", '``']
            stemming : Whether you want to perform stemming on tokens or not. The method used is Porter's algorithm.
    Attributes :
        - __punctuation : A list of lone symbols to filter from tokens.
        - __stemmer : A chosen stemmer to use.
    """
    def __init__(self, punctuation=['!', '?', '.', ',', ';', ':', '"', "'", '(', ')', '-', "''", '``'], stemming=True):
        self.__punctuation = punctuation
        if stemming:
            self.__stemmer = nltk.stem.porter.PorterStemmer()
    
    def word_tokenize(self, paragraph):
        """
        - Tokenizes the input string to a token list using nltk.world_tokenize
        - Removes single punctuation symbols found in self.__punctuation
        - Tries to stem using self.__stemmer. If there is none does nothing instead.
        Parameters :
            - paragraph : The text to process
        Return :
            - a list of tokens
        """
        tokens = nltk.word_tokenize(paragraph)
        tokens = [token for token in tokens if token not in self.__punctuation]
        
        try:
            tokens = [self.__stemmer.stem(token) for token in tokens]
        except AttributeError:
            pass

        return tokens