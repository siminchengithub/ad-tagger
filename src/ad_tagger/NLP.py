from nltk.stem import SnowballStemmer
from nltk.tokenize import RegexpTokenizer

class Stemmer:
    EXCEPTIONS = {
        'paars': 'paars',
        'glazen': 'glas'
    }
    def __init__(self, stemmer = None, exceptions = None):
        self.stemmer = stemmer or SnowballStemmer('dutch')
        self.tokenizer = RegexpTokenizer(r'\w+|[\d\. \n]+|\W+')
        self.exceptions = exceptions or Stemmer.EXCEPTIONS
        
    def stem(self, token):
        if token in self.exceptions:
            return self.exceptions[token]
        return self.stemmer.stem(token)
    
    def stem_sentence(self, sentence):
        doc = self.tokenizer.tokenize(sentence.lower())
        stemmed = ''.join([self.stem(token) for token in doc])
        return stemmed
