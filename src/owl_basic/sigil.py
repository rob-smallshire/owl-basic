from owl_basic.owltyping.type_system import (StringOwlType, IntegerOwlType, LongIntegerOwlType,
                                ByteOwlType, ObjectOwlType,
                                StringArrayOwlType, IntegerArrayOwlType, LongIntegerArrayOwlType,
                                ByteArrayOwlType, ObjectArrayOwlType, FloatArrayOwlType, FloatOwlType)

def identifierToType(identifier):
    """
    Convert an variable name identifier to a type
    """
    # The double-percent (64-bit) sigil must be tested before the single '%'.
    if identifier.endswith('%%'):
        return LongIntegerOwlType()
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
        if identifier[-3:-1] == '%%':
            return LongIntegerArrayOwlType()
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