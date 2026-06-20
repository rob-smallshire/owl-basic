'''
Created on 28 Mar 2010

@author: rjs
'''

from owl_basic.visitor import Visitable

class OwlTypeSingleton(type):
    def __init__(cls, name, bases, dict):
        super(OwlTypeSingleton, cls).__init__(name, bases, dict)
        cls.instance = None
 
    def __call__(cls, *args, **kw):
        if cls.instance is None:
            cls.instance = super(OwlTypeSingleton, cls).__call__(*args, **kw)
 
        return cls.instance

class OwlType(Visitable, metaclass=OwlTypeSingleton):
    "OwlType"
    
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

class PendingOwlType(OwlType, metaclass=OwlTypeSingleton):
    "Pending"
    
    def isAssignableFrom(self, other):
        # TODO: Is this correct?
        assert not isinstance(other, type)
        return True

class VoidOwlType(OwlType, metaclass=OwlTypeSingleton):
    "Void"
    
    def isDefined(self):
        return True
    
class ScalarOwlType(OwlType, metaclass=OwlTypeSingleton):
    "Scalar"

    def isAssignableFrom(self, other):
        # Scalar is the supertype of every concrete scalar (Integer, Float,
        # String, Object, ...), so a Scalar formal -- e.g. a DEF FN's return
        # value, which may be any scalar -- accepts any of them. Without this it
        # fell back to the base exact-type match and rejected every return value.
        assert not isinstance(other, type)
        return isinstance(other, ScalarOwlType)


class ObjectOwlType(ScalarOwlType, metaclass=OwlTypeSingleton):
    "Object"
    # OWL BASIC only - object reference
    
    def isConvertibleTo(self, other):
        assert not isinstance(other, type)
        return True
    
    def isAssignableFrom(self, other):
        assert not isinstance(other, type)
        return True
    
    def isDefined(self):
        return True

class NumericOwlType(ScalarOwlType, metaclass=OwlTypeSingleton):
    "Numeric"
    
    def isConvertibleTo(self, other):
        assert not isinstance(other, type)
        return other.isAssignableFrom(self)
    
    def isAssignableFrom(self, other):
        assert not isinstance(other, type)
        return isinstance(other, NumericOwlType) 
    
class IntegerOwlType(NumericOwlType, metaclass=OwlTypeSingleton):
    "Integer"
    
    def bitsIntegerPrecision(self):
        return 32
    
    def isDefined(self):
        return True
    
class LongIntegerOwlType(NumericOwlType, metaclass=OwlTypeSingleton):
    "LongInteger"
    # A 64-bit signed integer (the %% sigil, as in some modern BBC BASICs).

    def bitsIntegerPrecision(self):
        return 64

    def isDefined(self):
        return True

class AddressOwlType(NumericOwlType, metaclass=OwlTypeSingleton):
    "Address"
    
    def bitsIntegerPrecision(self):
        return 32 # What about this 32/64?
    
    def isDefined(self):
        return True

class ChannelOwlType(IntegerOwlType):
    "Channel"
    
class FloatOwlType(NumericOwlType, metaclass=OwlTypeSingleton):
    "Float"
    def bitsIntegerPrecision(self):
        "Representing a double precision float with 52 (+ 1 implied) bits in the mantissa."
        return 53
    
    def isDefined(self):
        return True
    
class StringOwlType(ObjectOwlType, metaclass=OwlTypeSingleton):
    "String"

    # String is a reference type, so it sits under Object in the hierarchy -- but
    # unlike a bare Object it must NOT silently interconvert with numbers. A
    # string is assignable only from another string, and (overriding Object's
    # permissive "convertible to anything") convertible only to the types that
    # genuinely accept it: itself and its supertypes Object/Scalar. That keeps
    # A$="x" and string-to-object boxing legal while making A$=5 and A=B$ the
    # Type mismatches BBC BASIC reports.
    def isAssignableFrom(self, other):
        assert not isinstance(other, type)
        return isinstance(other, StringOwlType)

    def isConvertibleTo(self, other):
        assert not isinstance(other, type)
        return other.isAssignableFrom(self)
    
class ByteOwlType(NumericOwlType, metaclass=OwlTypeSingleton):
    "Byte"
    
    def bitsIntegerPrecision(self):
        return 8
    
    def isDefined(self):
        return True


class _SumInterningMeta(OwlTypeSingleton):
    """Metaclass for SumOwlType: intern by member set instead of one singleton.

    OwlTypeSingleton caches a single instance per class (every other OwlType is a
    singleton). A sum carries data -- its member set -- so it needs one canonical
    instance *per distinct set* (and identity-equal so the inference fixpoint,
    which compares estimates with ``is``, converges).
    """
    def __call__(cls, members):
        key = frozenset(members)
        cache = cls.__dict__.get("_intern")
        if cache is None:
            cache = {}
            cls._intern = cache
        if key not in cache:
            cache[key] = type.__call__(cls, key)  # bypass the singleton __call__
        return cache[key]


class SumOwlType(ScalarOwlType, metaclass=_SumInterningMeta):
    "Sum"
    # A union of several concrete scalar types: the return type of a DEF FN that
    # yields different types on different paths (e.g. Integer on one, String on
    # another). Assignment is structural -- a value that might be any member is
    # assignable to a target only if EVERY member is -- so int|string fits no
    # numeric or string variable, while int|float promotes (the numeric join
    # collapses those before a sum is ever formed). It is a scalar, so PRINT and
    # other scalar-accepting contexts take it.

    def __init__(self, members):
        self.members = frozenset(members)
        # __doc__ drives the type name in diagnostics.
        self.__doc__ = " | ".join(sorted(m.__doc__ for m in self.members))

    def isConvertibleTo(self, other):
        assert not isinstance(other, type)
        return all(member.isConvertibleTo(other) for member in self.members)

    def isAssignableFrom(self, other):
        assert not isinstance(other, type)
        return any(member.isAssignableFrom(other) for member in self.members)

    def isDefined(self):
        return all(member.isDefined() for member in self.members)

    def __eq__(self, other):
        return isinstance(other, SumOwlType) and other.members == self.members

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.members)

    def __str__(self):
        return self.__doc__


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
   
class LongIntegerArrayOwlType(ArrayOwlType):
    "Array[LongInteger]"

    def __init__(self, rank=None):
        super(LongIntegerArrayOwlType, self).__init__(LongIntegerOwlType(), rank)

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
   
