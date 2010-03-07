import sys
import logging

import bbc_ast
import ast_utils
import errors
import flow_analysis

from entry_point_visitor import EntryPointVisitor

def locateEntryPoints(parse_tree, line_mapper, options):
    '''
    Locate all the program, procedure, function and subroutine entry points in the program
    represented by parse_tree.
    :param parse_tree: The root AstNode of an abstract syntax tree representing the program.
    :param line_mapper: A LineMapper for the program.
    :param options: Command line options.
    :returns: A dictionary of entry point names to entry point AstStatement nodes.  The name
              of the program entry point, if there is one, will be '__owl__main'
    '''
    logging.debug("locateEntryPoints")    
    epv = EntryPointVisitor(line_mapper)
    parse_tree.accept(epv)
    first_statement = line_mapper.firstStatement()
    epv.mainEntryPoint(first_statement)

    logging.debug("Checking for direct execution of function or procedure bodies...")    
    entry_points = epv.entryPoints
    for entry_point in entry_points.values():
        if isinstance(entry_point, bbc_ast.DefinitionStatement):
            if len(entry_point.inEdges) != 0:
                errors.warning("Execution of procedure/function at line %s" % entry_point.lineNum)
                # TODO: Could use ERROR statement here
                raise_stmt = bbc_ast.Raise(type = "ExecutedDefinitionException")
                raise_stmt.lineNum = entry_point.lineNum
                ast_utils.insertStatementBefore(entry_point, raise_stmt)
                raise_stmt.clearOutEdges()
                entry_point.clearInEdges()

    # Tag each statement with its predecessor entry point
    logging.debug("Tagging statements with entry point\n")
    for entry_point in entry_points.values():
        flow_analysis.tagSuccessors(entry_point, line_mapper)
    return entry_points
