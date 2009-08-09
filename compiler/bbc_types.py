from visitor import Visitable

# TODO: Need to be able to build type expressions
# TODO: Need support for Constant Types

class Type(Visitable):
    "Type"
    
    @classmethod
    def isA(cls, base_type):
        """
        True if other_type is compatible with the self type 
        """
        return issubclass(cls, base_type)

    @classmethod
    def isConvertibleTo(cls, other_type):
        return cls.isA(other_type)

# Used for types which will unknown at any given point
# TODO: These PendingTypes need to be detected and removed
# when sufficient information is available
class PendingType(Type):
    "Unknown"
    pass

    @classmethod
    def isConvertibleTo(cls, other_type):
        return True

class VoidType(Type):
    "Void"
    pass

class ScalarType(Type):
    "Scalar"
    pass

class ObjectType(ScalarType):
    "Reference"
    # OWL BASIC only - object reference
    # TODO: Rename to ObjectType
    pass

class NumericType(ScalarType):
    "Numeric"
    pass
    
class IntegerType(NumericType):
    "Integer"
    
    @classmethod
    def isConvertibleTo(cls, other_type):
        return cls.isA(other_type) or (other_type is FloatType)

class PtrType(NumericType):
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
    
    @classmethod
    def isConvertibleTo(cls, other_type):
        return cls.isA(other_type) or (other_type is IntegerType) or (other_type is PtrType) or (other_type is ByteType)

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
    _element_type = None
    
    @classmethod
    def _getElementType(cls):
        return cls._element_type
        
    # TODO: Can't call this property on a class!    
    elementType = property(_getElementType)

class ByteArrayType(ArrayType):
    "Array[Byte]"
    _element_type = ByteType

class IntegerArrayType(ArrayType):
    "Array[Integer]"
    _element_type = IntegerType

class FloatArrayType(ArrayType):
    "Array[Float]"
    _element_type = FloatType

class StringArrayType(ArrayType):
    "Array[String]"
    _element_type = StringType
   
