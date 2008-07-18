# TODO: Need to be able to build type expressions
# TODO: Need support for Constant Types

class Type(object):
    "Type"
    
    @classmethod
    def isA(cls, base_type):
        """
        True if other_type is compatible with the self type 
        """
        return issubclass(cls, base_type)

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

class AddressType(NumericType):
    "Address"
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



    