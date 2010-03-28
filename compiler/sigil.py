from typing.type_system import (StringOwlType, IntegerOwlType, ByteOwlType, ObjectOwlType,
                                StringArrayOwlType, IntegerArrayOwlType, ByteArrayOwlType,
                                ObjectArrayOwlType, FloatArrayOwlType, FloatOwlType)

def identifierToType(identifier):
    """
    Convert an variable name identifier to a type
    """
    sigil = identifier[-1]
    if sigil == '$':
        return StringOwlType()
    elif sigil == '%':
        return IntegerOwlType()
    elif sigil == '&':
        return ByteOwlType()
    elif sigil == '~':
        return ObjectOwlType()
    elif sigil == '(':
        sigil = identifier[-2:-1]
        if sigil == '$':
            return StringArrayOwlType()
        elif sigil == '%':
            return IntegerArrayOwlType()
        elif sigil == '&':
            return ByteArrayOwlType()
        elif sigil == '~':
            return ObjectArrayOwlType()
        else:
            return FloatArrayOwlType()
    return FloatOwlType() 