'''
Created on 28 Mar 2010

@author: rjs
'''

from visitor import Visitable

class OwlTypeSingleton(type):
    def __init__(cls, name, bases, dict):
        super(OwlTypeSingleton, cls).__init__(name, bases, dict)
        cls.instance = None
 
    def __call__(cls, *args, **kw):
        if cls.instance is None:
            cls.instance = super(OwlTypeSingleton, cls).__call__(*args, **kw)
 
        return cls.instance

class OwlType(Visitable):
    "OwlType"
    __metaclass__ = OwlTypeSingleton
    
    def isArray(self):
        return False
    
    def arrayRank(self):
        return None
    
    def makeArrayType(self, rank=1):
        '''
        Returns a OwlType object that represents an array
        of the current type.
        '''
        return ArrayOwlType(self, rank)
    
    def elementType(self):
        return None
    
    def isA(self, other):
        #assert not isinstance(other, type)
        return isinstance(self, type(other))
    
    def isConvertibleTo(self, other):
        '''
        Determines whether an instance of the current OwlType
        can be converted to an instance of the specified OwlType.
        '''
        assert not isinstance(other, type)
        return other.isAssignableFrom(self)
        
    def isAssignableFrom(self, other):
        '''
        Determines whether an instance of the current OwlType
        can be assigned from an instance of the specified OwlType.
        '''
        assert not isinstance(other, type)
        return type(other) == type(self)
    
    def bitsIntegerPrecision(self):
        return 0
    
    def isDefined(self):
        return False
    
    def __str__(self):
        return self.__doc__
    
    def __repr__(self):
        return self.__doc__

class PendingOwlType(OwlType):
    "Pending"
    __metaclass__ = OwlTypeSingleton
    
    def isAssignableFrom(self, other):
        # TODO: Is this correct?
        assert not isinstance(other, type)
        return True

class VoidOwlType(OwlType):
    "Void"
    __metaclass__ = OwlTypeSingleton
    
    def isDefined(self):
        return True
    
class ScalarOwlType(OwlType):
    "Scalar"
    __metaclass__ = OwlTypeSingleton
    
class ObjectOwlType(ScalarOwlType):
    "Object"
    __metaclass__ = OwlTypeSingleton
    # OWL BASIC only - object reference
    
    def isConvertibleTo(self, other):
        assert not isinstance(other, type)
        return True
    
    def isAssignableFrom(self, other):
        assert not isinstance(other, type)
        return True
    
    def isDefined(self):
        return True

class NumericOwlType(ScalarOwlType):
    "Numeric"
    __metaclass__ = OwlTypeSingleton
    
    def isConvertibleTo(self, other):
        assert not isinstance(other, type)
        return other.isAssignableFrom(self)
    
    def isAssignableFrom(self, other):
        assert not isinstance(other, type)
        return isinstance(other, NumericOwlType) 
    
class IntegerOwlType(NumericOwlType):
    "Integer"
    __metaclass__ = OwlTypeSingleton
    
    def bitsIntegerPrecision(self):
        return 32
    
    def isDefined(self):
        return True
    
class AddressOwlType(NumericOwlType):
    "Address"
    __metaclass__ = OwlTypeSingleton
    
    def bitsIntegerPrecision(self):
        return 32 # What about this 32/64?
    
    def isDefined(self):
        return True

class ChannelOwlType(IntegerOwlType):
    "Channel"
    
class FloatOwlType(NumericOwlType):
    "Float"
    __metaclass__ = OwlTypeSingleton
    def bitsIntegerPrecision(self):
        "Representing a double precision float with 52 (+ 1 implied) bits in the mantissa."
        return 53
    
    def isDefined(self):
        return True
    
class StringOwlType(ObjectOwlType):
    "String"
    __metaclass__ = OwlTypeSingleton
    # TODO: Assigning StringOwlType to ObjectOwlType should be possible
    
class ByteOwlType(NumericOwlType):
    "Byte"
    __metaclass__ = OwlTypeSingleton
    
    def bitsIntegerPrecision(self):
        return 8
    
    def isDefined(self):
        return True
    
class ArrayOwlType(ObjectOwlType):
    
    def __init__(self, element_type=None, rank=None):
        self.element_type = element_type # None = Unknown or unspecified
        self.rank = rank # None = Unknown or unspecified
        
    def isArray(self):
        return True
          
    def elementType(self):
        return self.element_type
    
    def arrayRank(self):
        return self.rank
    
    def __eq__(self, rhs):
        if (hasattr(rhs, "elementType") and hasattr(rhs, "arrayRank")):
            return ((self.elementType() == rhs.elementType())
                    and (self.arrayRank() == rhs.arrayRank()))
        else:
            return False
        
    def __ne__(self, rhs):
        return not (self == rhs)
    
    def isDefined(self):
        return self.element_type is not None and self.rank is not None
        
    def __repr__(self):
        rank_desc = ""
        if rank is not None:
            rank_desc = ";" + str(self.arrayRank())
        return "Array[" + str(self.elementType()) + rank_desc + "]" 
        
class ByteArrayOwlType(ArrayOwlType):
    "Array[Byte]"
    
    def __init__(self, rank=None):
        super(ByteArrayOwlType, self).__init__(ByteOwlType(), rank)
        
class IntegerArrayOwlType(ArrayOwlType):
    "Array[Integer]"
    
    def __init__(self, rank=None):
        super(IntegerArrayOwlType, self).__init__(IntegerOwlType(), rank)
   
class FloatArrayOwlType(ArrayOwlType):
    "Array[Integer]"
    
    def __init__(self, rank=None):
        super(FloatArrayOwlType, self).__init__(FloatOwlType(), rank)

class StringArrayOwlType(ArrayOwlType):
    "Array[String]"
    
    def __init__(self, rank=None):
        super(StringArrayOwlType, self).__init__(StringOwlType(), rank)

class ObjectArrayOwlType(ArrayOwlType):
    "Array[Object]"
    
    def __init__(self, rank=None):
        super(ObjectArrayOwlType, self).__init__(ObjectOwlType(), rank)
   
