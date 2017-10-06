import nltk

class Tokenizer:
    def __init__(self, punctuation=['!', '?', '.', ',', ';', ':', '"', "'", '(', ')', '-', "''", '``'], stemming=True):
        self.__punctuation = punctuation
        if stemming:
            self.__stemmer = nltk.stem.porter.PorterStemmer()
            
        nltk.download('punkt')
    
    def word_tokenize(self, paragraph):
        tokens = nltk.word_tokenize(paragraph)
        tokens = [token for token in tokens if token not in self.__punctuation]
        
        try:
            tokens = [self.__stemmer.stem(token) for token in tokens]
        except AttributeError:
            pass

        return tokens