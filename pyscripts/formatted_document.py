import json
import re
import nltk
import test

class FormattedDocument(object):
    """
    Class made to handle specific xml parsing of a document and converting it to a json file tokenized, 
    which is easier to interpret
    Initialize :
        - choose one of :
            - xml_root_doc : initialize from an xml.etree.ElementTree of architecture 
              .//RAC//DOC//{DOCID, HEADLINE//P, DATE//P, LENGTH//P, TEXT//P}
            - json_doc : initialize from a json string of shape {'document': self.matches} 
        - tokenizer : object which must implements a method "word_tokenize", which is then used to 
          tokenize the title and text. Default is nltk
          
    Attributes :
        - matches : a list of elements, where an element represents an article and :
              element : dictionnary (id, title, date, length, text) :
                - id : integer, the id of an article
                - title : list of string, the title of the article tokenized
                - date : string, when the article is written
                - length : integer, how many words are in the article
                - text : 2D list of string, where each list is paragraph, represented by a list of tokens
        - __tokenizer : the object implementing word_tokenize. Default is nltk
    """

    def __init__(self, xml_root_doc=None, json_doc=None, tokenizer=nltk):
        if tokenizer == nltk:
            nltk.download('punkt')
        
        self.__tokenizer = tokenizer
        if xml_root_doc is not None:
            self.matches = self.__format(xml_root_doc)
        elif json_doc is not None:
            self.matches = json.loads(json_doc)['document']
        else:
            self.matches = []
        
        
    def __format(self, xml_root_doc):
        """
        convert the xml file into lists and dictionnaries,
        with the advantages of getting rid of useless informations and loading
        it in python containers
        parameters :
            - xml_root_doc : xml.etree.ElementTree, root of an xml document
        return :
            - a list of elements, where an element represents an article and :
              element : dictionnary (id, title, date, length, text) :
                - id : string, the id of an article
                - title : string, the title of the article
                - date : string, when the article is written
                - length : integer, how many words are in the article
                - text : list, a list of string, where each string is a paragraph
        """
        output = []
        
        for doc in xml_root_doc.findall('.//DOC'):
            # TODO : convert dictionnary into object 
            element = {}
            
            # parts that are necessary
            element['id'] = doc.find(".//DOCID").text + '-' + doc.find(".//DOCNO").text
            element['text'] = []
            for paragraph in doc.findall(".//TEXT//P"):
                element['text'].append(self.__tokenizer.word_tokenize(paragraph.text))
            
            # parts that are bonuses
            title = doc.find(".//HEADLINE//P")
            element['title'] = self.__tokenizer.word_tokenize(title.text if title is not None else '')
            
            date = doc.find(".//DATE//P")
            element['date'] = date.text if date is not None else None
            
            length = doc.find(".//LENGTH//P")
            length = re.findall(r'\d+', length.text if length is not None else '0')
            element['length'] = int(length[0] if len(length) > 0 else 0)
            
            output.append(element)
            
        return output
        
        
    def to_json(self):
        """
        Convert the object into a json string
        parameters : None
        return :
            - a string, which is of shape {'document': self.matches}
        """
        return json.dumps({'document': self.matches})
        
        
    @staticmethod
    def sum(doc1, doc2):
        """
        append doc1 and doc2 to return a condensed document
        parameters:
            - doc1, doc2: two FormattedDocument to be concatenated
        return :
            - a FormattedDocument, where its attribute self.matches is the concatenation 
              of the two first attributes self.matches
        """
        doc3 = FormattedDocument()
        doc3.matches = doc1.matches + doc2.matches
        return doc3
