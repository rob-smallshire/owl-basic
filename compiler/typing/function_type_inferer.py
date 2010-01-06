import operator

from algorithms import all_equal
from bbc_ast import ReturnFromFunction
import errors
from bbc_types import *
from algorithms import representative

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
         setFunctionType(entry_point.name, PendingType)
    elif len(return_types) == 1:
        setFunctionType(entry_point.name, representative(return_types))
    elif reduce(operator.and_, [type.isA(NumericType) for type in return_types]):
        # TODO: Modify all function returns to cast to FloatType, if necessary
        setFunctionType(entry_point.name, FloatType)
    else:
        # TODO: Modify all function returns to box to ObjectType, if necessary
        # TODO: Modify all function calls to unbox from ObjectType, to what?
        setFunctionType(entry_point.name, ObjectType)
        pass
        
        
        
        


        
def setFunctionType(function_name, type):
    '''
    Given a function name such as 'FNx' set the actual type of all
    calls to that function.
    :param function_name: The name of a function including the FN prefix
    :param type: The type to which the actualType of call should be set
    '''
    assert function_name.startswith('FN')
    # TODO: Visit each function call and the the type of those that match
    print "Setting type of %s to %s" % (function_name, type)
    
        
        
        
            
            
        

# TODO: Factor out into a cfg_utils file.
def depthFirstSearch(vertex, visited = None):
    '''
    A generator which performs depth first search from the supplied vertex through
    the control flow graph.
    :param vertex: A CFG Vertex from which depth first search will be performed
    :param visited: A, optional set of vertices which need not be visited
    '''
    to_visit = []
    if visited is None:
        visited = set()
    to_visit.append(vertex)
    while len(to_visit) != 0:
        v = to_visit.pop()
        if v not in visited:
            visited.add(v)
            yield v
            to_visit.extend(v.outEdges)
            