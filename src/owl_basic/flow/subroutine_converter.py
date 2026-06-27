'''
Convert subroutines with named PROCedures
'''

import logging

from owl_basic.syntax.ast import (DefineProcedure, CallProcedure,
                                  ReturnFromProcedure, End, Until, Next,
                                  Endwhile)
from owl_basic.exceptions import CompileError
from owl_basic.ast_utils import insertStatementBefore, findFollowingStatement
from .convert_sub_visitor import ConvertSubVisitor
from .flow_analysis import tagSuccessors, deTagSuccessors
from .traversal import depthFirstSearch

logger = logging.getLogger('flow.subroutine_converter')


def bridgeFallthroughSubroutines(entry_points, line_mapper):
    """Replace each fall-through into a GOSUB'd subroutine head with an explicit
    PROC call, so the head is entered only by GOSUB and converts cleanly.

    A GOSUB target whose head is also reached by fall-through cannot be a plain
    single-entry PROC -- its RETURN would be ambiguous. Three shapes produce this,
    and all are bridged by splicing ``PROC PROCSub<head> : <terminator>`` onto the
    fall-through edge ``pred -> head``, so the call runs the routine and the
    terminator does what the original RETURN would:

      * a jump-table handler with no RETURN running into the next handler -- the
        fall-through is inside another subroutine, so a pending GOSUB frame exists
        and the terminator is ENDPROC, which unwinds to the one GOSUB frame the
        BBC's RETURN reaches (no return-address stack needed);
      * a fall-through from the *main line* -- no GOSUB frame exists, so the BBC's
        RETURN would be "RETURN without GOSUB", which halts; the terminator is END,
        reproducing that halt (and if the routine loops or recurses it is never
        reached);
      * dead code preceding the head -- the bridge is simply never executed.

    Only a *fall-through* entry is bridged (the head is the pred's textual
    successor). A *branch* (GOTO) into a head is a different case and is left for
    :func:`convertSubroutinesToProcedures` to reject. Returns True if any bridge
    was inserted, so the caller can re-parent the mutated tree.
    """
    # A fall-through from the main line has no pending GOSUB frame, so its bridge
    # ends the program (END); one from inside a subroutine returns to the caller
    # (ENDPROC).
    main_entry = entry_points.get("__owl__main")
    main_reachable = set(depthFirstSearch(main_entry)) if main_entry is not None else set()
    bridges = []
    for name, entry_point in entry_points.items():
        if not name.startswith("gosub"):
            continue
        # A GOSUB whose target is a loop closer (UNTIL/NEXT/ENDWHILE) jumps into
        # the middle of a loop, relying on the run-time loop stack to find the
        # matching opener -- genuinely dynamic and uncompilable. Do not bridge it:
        # severing the closer's body fall-through would break loop correlation.
        # Leave it for convertSubroutinesToProcedures to reject cleanly.
        if isinstance(entry_point, (Until, Next, Endwhile)):
            continue
        procname = "PROCSub" + name[len("gosub"):]
        # An in-edge from inside the routine (a GOTO back to the top -- a loop) is
        # internal and fine; only an edge from outside the body is foreign.
        body = set(depthFirstSearch(entry_point))
        for predecessor in list(entry_point.inEdges):
            if predecessor in body:
                continue
            if findFollowingStatement(predecessor) is entry_point:
                from_main = predecessor in main_reachable
                bridges.append((predecessor, entry_point, procname, from_main))
    for predecessor, head, procname, from_main in bridges:
        _bridgeFallthrough(predecessor, head, procname, from_main)
    return bool(bridges)


def _bridgeFallthrough(predecessor, head, procname, from_main):
    """Splice ``PROC procname : <terminator>`` between *predecessor* and *head*,
    and reroute the fall-through edge through it so *head* loses *predecessor* as
    an entry. The terminator is END for a main-line fall-through (no GOSUB frame)
    or ENDPROC for one inside another subroutine."""
    call = CallProcedure(name=procname)
    call.lineNum = predecessor.lineNum
    terminator = End() if from_main else ReturnFromProcedure()
    terminator.lineNum = predecessor.lineNum
    for tag in predecessor.entryPoints:          # the bridge runs in pred's routine
        call.addEntryPoint(tag)
        terminator.addEntryPoint(tag)
    # AST: place the bridge immediately after the predecessor in its statement
    # list (a stable .index lookup, since insertions may have made indices stale).
    parent_list = getattr(predecessor.parent, predecessor.parent_property)
    index = parent_list.index(predecessor)
    parent_list.insert(index + 1, call)
    parent_list.insert(index + 2, terminator)
    call.parent = terminator.parent = predecessor.parent
    call.parent_property = terminator.parent_property = predecessor.parent_property
    # CFG: predecessor -> call -> terminator (terminal); head loses the fall-through.
    predecessor.outEdges.discard(head)
    head.inEdges.discard(predecessor)
    predecessor.addOutEdge(call)
    call.addInEdge(predecessor)
    call.addOutEdge(terminator)
    terminator.addInEdge(call)

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
