from bbc_types import *

def identifierToType(identifier):
    """
    Convert an variable name identifier to a type
    """
    sigil = identifier[-1]
    if sigil == '$':
        return StringType
    elif sigil == '%':
        return IntegerType
    elif sigil == '&':
        return ByteType
    elif sigil == '~':
        return ObjectType
    elif sigil == '(':
        sigil = identifier[-2:-1]
        if sigil == '$':
            return StringArrayType
        elif sigil == '%':
            return IntegerArrayType
        elif sigil == '&':
            return ByteArrayType
        elif sigil == '~':
            return ReferenceArrayType
        else:
            return FloatArrayType
    return FloatType 