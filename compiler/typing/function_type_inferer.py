import operator

from algorithms import all_equal
from bbc_ast import ReturnFromFunction
import errors
from bbc_types import *
from algorithms import representative
from flow.traversal import depthFirstSearch

def inferTypeOfFunction(entry_point):
    '''
    Infer the type of the function defined at entry_point by discovering the
    type of all of the return points from the function.  If the types are
    different numeric types, promote IntegerTypes to FloatTypes.  If the types
    are a mixture of StringTypes and NumericTypes box the return value in an
    object type.
    
    :param entry_point: A DefineFunction AstNode at the start of a user
                        defined function.
    :returns: The infered type of the function. One of IntegerType, FloatType,
              StringType or ObjectType.  If the type of the function could not
              be inferred (possibly because other function types need inferring too)
              return PendingType.
    '''
    print "DEF ", entry_point.name
    return_types = set()
    for vertex in depthFirstSearch(entry_point):
        if isinstance(vertex, ReturnFromFunction):
            return_types.add(vertex.returnValue.actualType)
    
    for type in return_types:
        print " =", type
    
    # If there is only one return type, set the type of the function, and exit
    if len(return_types) == 0:
        errors.warning("%s never returns at line %s" % (entry_point.name, entry_point.lineNum))
    elif PendingType in return_types:
         return PendingType
    elif len(return_types) == 1:
        return representative(return_types)
    elif reduce(operator.and_, [type.isA(NumericType) for type in return_types]):
        # TODO: Modify all function returns to cast to FloatType, if necessary
        return FloatType
    else:
        # TODO: Modify all function returns to box to ObjectType, if necessary
        # TODO: Modify all function calls to unbox from ObjectType, to what?
        return ObjectType
            