from .NLP import Stemmer, SnowballStemmer
import re
import pandas as pd
from abc import ABCMeta, abstractmethod

#Attribute values that show no ground truth
OVERIGES = {
    'Kleur': ['Overige kleuren'],
    'Materiaal': ['Overige materialen', 'Overige metalen', 'Overige houtsoorten', 'Overig'],
    'Vorm': ['Overige vormen'],
    'Lengte': ['Overige'],
    'Breedte': ['Overige'],
    'Hoogte': ['Overige']
}

#direction of a numeric attribute value. e.g. 12cm tot 15cm has a direction of tot, 
DIRECTIONS = ['minder', 'tot', 'meer', 'exact']

#units of the numeric values
UNITS = ['meter', 'dm', 'cm', 'mm']

#for conversting between different units
UNIT_BASE = {
            'meter': 1000,
            'dm': 100,
            'cm': 10,
            'mm': 1
        }

class RangeValue:
    """A RangeValue represents a numeric attribute value, e.g. 100cm tot 200cm
    """
    def __init__(self, left, right, direction, unit, value):
        self.left = left
        self.right = right
        self.direction = direction
        self.unit = unit
        self.value = value
        
    def isin(self, num, unit):
        num = self.convert_unit(num, unit)
        if self.direction == 'exact':
            return num == self.left
        if self.left <= num and self.right > num:
            return True
        return False
    
    def convert_unit(self, num, unit):
        if unit == self.unit:
            return num
        num = num * UNITS[unit]/UNITS[self.unit]
        return num  

class Attribute:
    """Base class of an attribute
    """
    def __init__(self, name, values):
        self.name = name
        self.values = values
        self.stemmer = Stemmer()
        self.mapping = None

    @abstractmethod
    def map_value(self, ):
        """map the extracted value to a Marktplaats attribute value, e.g. 100 -> 50 tot 150 
        """
        raise NotImplementedError()

    @abstractmethod
    def extract(self, ):
        """extract the attribute value given a string
        """
        raise NotImplementedError()

class MatchAttribute(Attribute):
    """A MatchAttribute is an attribute whose value can be directly matched from a list of 
    allowed values, e.g. colors
    """
    def __init__(self, name, values):
        super().__init__(name, values)
        self.stemmed_values = [self.stemmer.stem(s.lower()) for s in self.values]
        self.re_pattern = self.create_re_pattern()
        self.mapping = self.create_mapping()

    def create_mapping(self, ):
        return dict(zip(self.stemmed_values, self.values))  

    def create_re_pattern(self, ):
        return r'\b(?:' + '|'.join([re.escape(value) for value in self.stemmed_values]) + r')\b'

    def map_value(self, token, allowed_values):
        return self.mapping[token]
    
    def extract(self, s, allowed_values):
        s = self.stemmer.stem_sentence(s)
        extracted = re.findall(self.re_pattern, s)
        mapped = [self.map_value(token, allowed_values) for token in extracted]
        return pd.Series(mapped).drop_duplicates().tolist()
        
class NumericAttribute(Attribute): 
    """A NumericAttribute is an attribute whose value is numeric, e.g. lengte
    """
    def __init__(self, name, values, re_pattern):
        super().__init__(name, values)
        self.re_pattern = re_pattern
        self.mapping = self.create_mapping()

    def create_mapping(self, ):
        """create the mapping between numeric value and Marktplaats numeric attribute values
        """
        range_mapping = {}
        for value in self.values:
            s = value.lower()
            numeric_match = re.findall(r'\d+', s)
            if numeric_match:
                unit_match = re.search('|'.join(UNITS), s)
                if unit_match:
                    unit = unit_match.group()
                else:
                    unit = None
                direction_match = re.search('|'.join(DIRECTIONS), s)
                if direction_match:
                    direction = direction_match.group()
                else:
                    direction = 'exact'
                if direction == 'minder':
                    left = 0
                    right = numeric_match[0]
                elif direction == 'tot':
                    if len(numeric_match) == 1:
                        left = 0
                        right = numeric_match[0]
                    else:
                        left = numeric_match[0]
                        right = numeric_match[1]
                elif direction == 'meer':
                    left = numeric_match[0]
                    right = float('inf')
                elif direction == 'exact':
                    left = numeric_match[0]
                    right = left
                range_mapping[value] = RangeValue(float(left), float(right), direction, unit, value)
            else:
                range_mapping[value] = RangeValue(float('inf'), float('inf'), 'exact', None, value)
        return range_mapping
        
    def map_value(self, matches, allowed_values):
        matches = list(filter(None, matches))
        if self.name == ['Breedte']:
            matches = min([float(v) for v in matches])
        else:
            matches = max([float(v) for v in matches])
        for value in allowed_values:
            range_value = self.mapping[value]
            if range_value.isin(matches, range_value.unit):
                return range_value.value
            
    def extract(self, s, allowed_values):
        s = self.stemmer.stem_sentence(s)
        extracted = re.findall(self.re_pattern, s)
        mapped = [self.map_value(token, allowed_values) for token in extracted]
        return pd.Series(mapped).drop_duplicates().tolist()