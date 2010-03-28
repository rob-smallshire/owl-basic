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

class ScalarType(Type):
    "Scalar"
    pass

class ObjectType(ScalarType):
    "Object"
    # OWL BASIC only - object reference

class NumericType(ScalarType):
    "Numeric"
    
    @classmethod
    def isConvertibleTo(cls, other_type):
        return other_type.isA(NumericType)
    
    @classmethod
    def bitsIntegerPrecision(cls):
        assert 0, "bitsIntegerPrecision() not implemented for %s" % cls
        
class IntegerType(NumericType):
    "Integer"
    
    @classmethod
    def bitsIntegerPrecision(cls):
        '''
        Representing a double precision float with 52 (+ 1 implied) bits in the mantissa.
        '''
        return 32
    
class PtrType(NumericType):
    "Address"
    
    @classmethod
    def bitsIntegerPrecision(cls):
        # TODO: We use 32 for now(!)
        return 32

# TODO: Could have a Channel type which is subclass of the Integer type
#       We could then have a warning mode which warned about Integers
#       rather than channels being used in file operations.

class ChannelType(IntegerType):
    "Channel"
    pass

class FloatType(NumericType):
    "Float"
    
    @classmethod
    def bitsIntegerPrecision(cls):
        '''
        Representing a double precision float with 52 (+ 1 implied) bits in the mantissa.
        '''
        return 53

class StringType(ScalarType):
    "String"

class ByteType(NumericType):
    "Byte"
    
    @classmethod
    def bitsIntegerPrecision(cls):
        '''
        Representing a double precision float with 52 (+ 1 implied) bits in the mantissa.
        '''
        return 8
    
class BoxType(ScalarType):
    "Box"
    pass

class ArrayType(Type):
    "Array"
    pass

class ByteArrayType(ArrayType):
    "Array[Byte]"
    element_type = ByteType

class IntegerArrayType(ArrayType):
    "Array[Integer]"
    element_type = IntegerType

class FloatArrayType(ArrayType):
    "Array[Float]"
    element_type = FloatType

class StringArrayType(ArrayType):
    "Array[String]"
    element_type = StringType

   