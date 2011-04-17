'''
Convert subroutines with named PROCedures
'''

import logging

from syntax.ast import DefineProcedure
from ast_utils import insertStatementBefore
from convert_sub_visitor import ConvertSubVisitor
from flow_analysis import tagSuccessors, deTagSuccessors

logger = logging.getLogger('flow.subroutine_converter')

def convertSubroutinesToProcedures(parse_tree, entry_points, line_mapper, options):
    logger.info("Convert subroutines to procedures")   
    entry_point_names_to_remove = []
    entry_points_to_add = {}
    for name, entry_point in entry_points.items():
        # TODO: This will only work with simple (i.e. single entry) subroutines
        print "name = %s, entry_point = %s" % (name, entry_point)
        subname = iter(entry_point.entryPoints).next()
        if subname.startswith('SUB'):
            procname = 'PROCSub' + subname[3:]
            assert len(entry_point.inEdges) == 0
            defproc = DefineProcedure(name=procname, formalParameters=None)
            insertStatementBefore(entry_point, defproc)
            deTagSuccessors(entry_point)
            entry_point.clearEntryPoints()
            entry_point_names_to_remove.append(name)
            entry_points_to_add[procname] = defproc
            entry_point.clearComeFromGosubEdges()
            tagSuccessors(defproc, line_mapper)
    for name in entry_point_names_to_remove:
        del entry_points[name]
    entry_points.update(entry_points_to_add)
    
    csv = ConvertSubVisitor()
    parse_tree.accept(csv)
