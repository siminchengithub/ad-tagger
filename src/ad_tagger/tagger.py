from .attribute import NumericAttribute, MatchAttribute, RangeValue

RE_PATTERNS = {
    'Lengte': [r'(\d+)(?:m|cm| )*(?:x|bij)[ ]*(\d+)(?:m|cm)*',
               r'(?:lengt|lang|l)[: ]*(\d+)',
               r'(\d+)(?:m|cm| )*[ ]*(?:lengt|lang|l)'],
    'Breedte': [r'(\d+)(?:m|cm| )*(?:x|bij)[ ]*(\d+)(?:m|cm)*',
                r'(?:breedt|bred|b)[: ]*(\d+)',
                r'(\d+)(?:m|cm| )*[ ]*(?:breedt|bred|b)'],
    'Hoogte': [r'\d+(?:m|cm| )*(?:x|bij)[ ]*\d+(?:m|cm)*(?:x|bij)[ ]*(\d+)(?:m|cm)*',
               r'(?:hoogt|hog|h)[: ]*(\d+)',
               r'(\d+)(?:m|cm| )*[ ]*(?:hoogt|hog|h)']
}

class RegexTagger:
    def __init__(self, attributes, l2_attributes):
        self.attributes = attributes
        self.l2_attributes = l2_attributes
    
    def tag(self, s, l2):
        if not s:
            return None
        allowed_attributes = list(set(self.attributes).intersection(set(self.l2_attributes[l2])))
        tags = {}
        for attr_name in allowed_attributes:
            allowed_values = self.l2_attributes[l2][attr_name]
            tags[attr_name] = self.attributes[attr_name].extract(s, allowed_values)
        return tags

    @classmethod
    def from_pandas(cls, df_attrs_map):
        attributes = {}
        for attribute_name in df_attrs_map['attribute'].unique():
            values = df_attrs_map[df_attrs_map['attribute'] == attribute_name]['value'].unique().tolist()
            if attribute_name in ['Lengte', 'Breedte', 'Hoogte']:
                pattern = '|'.join(RE_PATTERNS[attribute_name])
                attributes[attribute_name] = NumericAttribute(name=attribute_name, values=values, re_pattern=pattern)
            else:
                attributes[attribute_name] = MatchAttribute(name=attribute_name, values=values)
        l2_attributes = {k: f.groupby('attribute')['value'].apply(list).to_dict()
                                        for k, f in df_attrs_map.groupby('l2')}
        return cls(attributes, l2_attributes)