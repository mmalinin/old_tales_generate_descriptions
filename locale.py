import re
from typing import Dict
from xml.etree import ElementTree

# Extract [k:v]
# [TERM_ETHER:Spectral]. [TERM_UNPLAYABLE:Unplayable]. Lose 1 [ICON_ENERGY] when this card appears in your hand. 
_inline_re = re.compile(r"\[(.+):(.+)]")

class Locale:
    def __init__(self):
        self.strings: Dict[str, str] = {}
        self.rules: list[tuple[str, str]] = []
        
    def __setitem__(self, key, value):
        self.strings[key] = value

    def __getitem__(self, key):
        if key is None:
            return ''
        
        return self.strings.get(key, key)
    
    def __len__(self):
        return len(self.strings)
    
    def get(self, key, default=''):
        if key is None:
            return default
        
        return self.strings.get(key, key)
    
    def process(self, key: str):
        if key is None:
            return ''
        
        if key not in self.strings:
            return key
        
        value = self.strings[key]
        
        for rule in self.rules:
            value = value.replace(rule[0], rule[1])

        # replace [k:v] with <v>
        value = _inline_re.sub(lambda m: f"<{m.group(2)}>", value)
        return value
    
    def append_locale(self, other: 'Locale'):
        self.strings.update(other.strings)
        
    def append_dict(self, other: Dict[str, str]):
        self.strings.update(other)
        
    def append_xml(self, root: ElementTree):
        for child in root.getroot():
            self.strings[child.attrib["key"]] = child.text
            
    def add_rule(self, old:str, new: str):
        self.rules.append((old, new))


if __name__ == '__main__':
    pass