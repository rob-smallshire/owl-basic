class Type(object):
    pass

class VoidType(Type):
    pass

class ScalarType(Type):
    pass

class NumericType(ScalarType):
    pass
    
class IntegerType(NumericType):
    pass

# TODO: Could have a Channel type which is subclass of the Integer type
#       We could then have a warning mode which warned about Integers
#       rather than channels being used in file operations.

class ChannelType(IntegerType):
    pass

class FloatType(NumericType):
    pass

class StringType(ScalarType):
    pass

class ByteType(ScalarType):
    pass

class BoxType(ScalarType):
    pass

class ArrayType(Type):
    pass

class ByteArrayType(ArrayType):
    pass

class IntegerArrayType(ArrayType):
    pass

class FloatArrayType(ArrayType):
    pass

class StringArrayType(ArrayType):
    pass

def nameToScalarType(name):
    sigil = name[-1:]
    if sigil == '$':
        return StringType
    elif sigil == '%':
        return IntegerType
    return Float

def nameToArrayType(name):
    sigil = name[-1]
    if sigil == '$':
        return StringArrayType
    elif sigil == '%':
        return IntegerArrayType
    return FloatArray
    # TODO: What about ByteArray ?
    
def checkType(actual, required, strict):
    actual_type = actual.type()
    if not issubclass(actual_type, strict):
       sys.stderr.write("Warning: Implicit conversion. %s used where %s expected" % (actual_type, strict))
    if not issubclass(actual_type, required):
       sys.stderr.write("Error: Type mismatch. %s used where %s required" % (actual_type, required))
       sys.exit(1)


    