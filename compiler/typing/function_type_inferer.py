import operator

from algorithms import all_equal
from syntax.ast import ReturnFromFunction
import errors
from algorithms import representative
from flow.traversal import depthFirstSearch
from typing.type_system import PendingOwlType, ObjectOwlType, FloatOwlType

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
    elif PendingOwlType() in return_types:
         return_type = PendingOwlType()
    elif len(return_types) == 1:
        return_type = representative(return_types)
    elif reduce(operator.and_, [type.isA(NumericOwlType()) for type in return_types]):
        # TODO: Modify all function returns to cast to FloatOwlType, if necessary
        return_type = FloatOwlType()
    else:
        # TODO: Modify all function returns to box to ObjectOwlType, if necessary
        # TODO: Modify all function calls to unbox from ObjectOwlType, to what?
        return_type =  ObjectOwlType()
    entry_point.returnType = return_type
    return return_type
            