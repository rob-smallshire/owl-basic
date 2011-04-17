'''
Created on 5 Jan 2010

@author: rjs
'''

import logging

from syntax.ast import DefineFunction

from typecheck_visitor import TypecheckVisitor
from function_type_inferer import inferTypeOfFunction
from set_function_type_visitor import SetFunctionTypeVisitor
from typing.type_system import PendingOwlType


def typecheck(parse_tree, entry_points, options):
    '''
    :param parse_tree: The parse_tree to be type checked
    :param entry_points: A dictionary of entry point names to AstStatements
    :param options: Command line options.
    '''
    logging.debug("Type checking... ")
    
    # TODO: Need to iteratively resolve types here.
    #       while (pending_types_remaining):
    parse_tree.accept(TypecheckVisitor(entry_points))
    pending = True
    while pending:
        pending = inferUserFunctionTypes(parse_tree, entry_points, options)  

def inferUserFunctionTypes(parse_tree, entry_points, options):
    """
    Iteratively examine the return types of user defined function calls
    and assign the actual type.
    :returns: True if any function types are still pending, otherwise False.
    """
    logging.debug("Infer user function types")
    pending = False
    for entry_point in entry_points.values():
        if isinstance(entry_point, DefineFunction):
            function_type = inferTypeOfFunction(entry_point)
            if function_type != PendingOwlType():
                setFunctionType(parse_tree, entry_point.name, function_type)
            else:
                pending = True
    return pending

def setFunctionType(parse_tree, function_name, function_type):
    '''
    Given a function name such as 'FNx' set the actual type of all
    calls to that function.
    :param function_name: The name of a function including the FN prefix
    :param type: The type to which the actualType of call should be set
    '''
    assert function_name.startswith('FN')
    # TODO: Visit each function call and the the type of those that match
    print "Setting type of %s to %s" % (function_name, function_type)
    sftv = SetFunctionTypeVisitor(function_name, function_type)
    parse_tree.accept(sftv)
