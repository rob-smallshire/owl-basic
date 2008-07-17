# TODO: Need to be able to build type expressions
# TODO: Need support for Constant Types

class Type(object):
    "Type"
    
    @classmethod
    def isA(cls, other_type):
        """
        True if other_type is compatible with the self type 
        """
        return issubclass(other_type, cls)

class VoidType(Type):
    "Void"
    pass

class ScalarType(Type):
    "Scalar"
    pass

class ReferenceType(ScalarType):
    "Reference"
    # OWL BASIC only - object reference
    pass

class NumericType(ScalarType):
    "Numeric"
    pass
    
class IntegerType(NumericType):
    "Integer"
    pass

# TODO: Could have a Channel type which is subclass of the Integer type
#       We could then have a warning mode which warned about Integers
#       rather than channels being used in file operations.

class ChannelType(IntegerType):
    "Channel"
    pass

class FloatType(NumericType):
    "Float"
    pass

class StringType(ScalarType):
    "String"
    pass

class ByteType(NumericType):
    "Byte"
    pass

class BoxType(ScalarType):
    "Box"
    pass

class ArrayType(Type):
    "Array"
    pass

class ByteArrayType(ArrayType):
    "Array[Byte]"
    pass

class IntegerArrayType(ArrayType):
    "Array[Integer]"
    pass

class FloatArrayType(ArrayType):
    "Array[Float]"
    pass

class StringArrayType(ArrayType):
    "Array[String]"
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


    