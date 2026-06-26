'''
Convert subroutines with named PROCedures
'''

import logging

from owl_basic.syntax.ast import DefineProcedure
from owl_basic.exceptions import CompileError
from owl_basic.ast_utils import insertStatementBefore
from .convert_sub_visitor import ConvertSubVisitor
from .flow_analysis import tagSuccessors, deTagSuccessors
from .traversal import depthFirstSearch

logger = logging.getLogger('flow.subroutine_converter')

def convertSubroutinesToProcedures(parse_tree, entry_points, line_mapper, options):
    logger.info("Convert subroutines to procedures")   
    entry_point_names_to_remove = []
    entry_points_to_add = {}
    for name, entry_point in list(entry_points.items()):
        # TODO: This will only work with simple (i.e. single entry) subroutines
        logging.debug("name = %s, entry_point = %s", name, entry_point)
        # Identify GOSUB-derived subroutines by their entry-point dict key
        # ('gosubNNN', set deterministically in AST order), not by
        # next(iter(entry_point.entryPoints)): a line reachable both by GOSUB
        # and by fall-through carries several tags ({'MAIN', 'SUBNNN'}), and
        # picking one arbitrarily from that set made the whole compilation
        # depend on hash-randomised set iteration order.
        if name.startswith('gosub'):
            subname = 'SUB' + name[len('gosub'):]
            procname = 'PROCSub' + subname[3:]
            # Converting a GOSUB'd line to a PROC is sound as long as GOSUB is
            # the routine's only *foreign* entry. A control-flow edge into the
            # head from a statement that is itself inside the routine -- a GOTO
            # back to the top, i.e. a loop -- is fine: it lowers as a branch
            # within the PROC. Only an edge from outside (the main line falling
            # in) makes RETURN ambiguous and the conversion unsound.
            #
            # In the forward CFG a GOSUB target is a root whose body is exactly
            # what is reachable from it (RETURN nodes have no successor, so the
            # body is sealed), and main reaches it only via the separate
            # come-from-GOSUB edges. So an in-edge is internal iff its source is
            # forward-reachable from the head, and foreign otherwise.
            body = set(depthFirstSearch(entry_point))
            foreign_entries = [predecessor for predecessor in entry_point.inEdges
                               if predecessor not in body]
            if foreign_entries:
                raise CompileError(
                    "the subroutine at line %s is reached other than by GOSUB "
                    "(by fall-through or a branch); compiling such a subroutine "
                    "is not supported" % subname[3:]
                )
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
    
    csv = ConvertSubVisitor(entry_points)
    parse_tree.accept(csv)
