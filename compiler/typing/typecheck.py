'''
Created on 5 Jan 2010

@author: rjs
'''

import logging

from bbc_ast import DefineFunction

from typecheck_visitor import TypecheckVisitor
from function_type_inferer import inferTypeOfFunction

def typecheck(parse_tree, epv, options):
    logging.debug("typecheck")
    if options.use_typecheck:
        if options.verbose:
            sys.stderr.write("Type checking... ")
        
        # TODO: Need to iteratively resolve types here.
        #       while (pending_types_remaining):
        parse_tree.accept(TypecheckVisitor())
        inferUserFunctionTypes(parse_tree, epv, options)  
        if options.verbose:
            sys.stderr.write("done\n")

def inferUserFunctionTypes(parse_tree, epv, options):
    """
    Iteratively examine the return types of user defined function calls
    and assign the actual type
    """
    logging.debug("Infer user function types")
    for entry_point in epv.entry_points:
        if isinstance(entry_point, DefineFunction):
            inferTypeOfFunction(entry_point)
