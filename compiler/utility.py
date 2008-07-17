# Miscellaneous utility functions

import re

def underscoresToCamelCase(s):
    "Converts 'text_separated_like_this' to 'textSeparatedLikeThis'"
    t = s.replace('_', ' ').title().replace(' ', '')
    u = t[0].lower() + t[1:]
    return u

def camelCaseToUnderscores(s):
    "Converts 'textSeparatedLikeThis' to 'text_separated_like_this'"
    return re.sub(r'([a-z])([A-Z])', r'\1_\2', s).lower()

def hasprop(cls, name):
    "Determines whether the supplied object has a property called 'name'"
    (name in cls.__dict__ and isinstance(cls.__dict__[name], property))
    
    if name in cls.__dict__:
        return isinstance(cls.__dict__[name], property)
    for base in cls.__bases__:
        if hasprop(base, name):
            return True
    return False
    
        
