import logging
import errors
from collections import deque
from syntax.ast import Repeat, While, ForToStep
from flow.connectors import connectLoop
from visitor import Visitor

class CorrelationVisitor(Visitor):
    """
    This visitor performs abstract execution of the control-flow-graph in order
    to correlate the opening and closing statements or FOR..NEXT, REPEAT..UNTIL
    and WHILE..ENDWHILE loops.
    
    CFG nodes where execution branches are annotated with the current stack of
    loop structures, and a depth first search is performed through the CFG.
    If the stack is non-empty when a terminal node (no out-edges) is encountered
    an error is reported.  If loops are incorrectly nested an error is reported.
    If loops are correctly nested, back-edges are inserted into the CFG.
    """
    
    def __init__(self):
        self.to_visit = deque()
        self.visited = set()
        self.loops = [] # A stack for tracking the current abstract execution state

    def start(self, entry_point):
        """
        The entry-point from which loop correlation should start
        """
        self.depthFirstSearch(entry_point)
        for v in self.visited:
            if hasattr(v, "loop_stack"):
                del v.loop_stack

    def depthFirstSearch(self, entry_point):
        self.to_visit.append(entry_point)
        while len(self.to_visit):
            v = self.to_visit.pop()
            # Restore the loop stack
            if hasattr(v, "loop_stack"):
                self.loops = v.loop_stack[:]
            if v not in self.visited:
                self.visited.add(v)
                v.accept(self)
                if len(v.outEdges) == 0 and len(self.loops) != 0:
                    # TODO: Improve this error message by printing an
                    # abstract stack trace
                    errors.fatalError("In loops at terminal statement at line %s" % v.lineNum)
                # If execution splits, take a copy of the current loop stack
                # and store a reference to it on each of the target nodes of
                # the out edges of the current node, so the state can be
                # restored later in the traversal
                if len(v.outEdges) > 1:
                    loop_stack = self.loops[:]
                    for target in v.outEdges:
                        target.loop_stack = loop_stack
                self.to_visit.extend(v.outEdges)

    def visitAstStatement(self, statement):
        """
        Do nothing for most AST statements
        """
        pass
    
    def visitRepeat(self, repeat_stmt):
        self.loops.append(repeat_stmt)
        
    def visitUntil(self, until_stmt):
        if len(self.loops) == 0:
            errors.fatalError("Not in a REPEAT loop at line %d." % until_stmt.lineNum)
        peek = self.loops[-1]
        if not isinstance(peek, Repeat):
            errors.fatalError("Not in a REPEAT loop at line %d; currently in %s loop opened at line %d" % (until_stmt.lineNum, peek.description, peek.lineNum))
        repeat_stmt = self.loops.pop()
        connectLoop(until_stmt, repeat_stmt)
        
    def visitWhile(self, while_stmt):
        self.loops.append(while_stmt)
        
    def visitEndwhile(self, endwhile_stmt):
        if len(self.loops) == 0:
            errors.fatalError("Not in a WHILE loop at line %d." % endwhile_stmt.lineNum)
        peek = self.loops[-1]
        if not isinstance(peek, While):
            errors.fatalError("Not in a WHILE loop at line %d; currently in %s loop opened at line %d" % (endwhile_stmt.lineNum, peek.description, peek.lineNum))
        while_stmt = self.loops.pop()
        connectLoop(endwhile_stmt, while_stmt)
        
    def visitForToStep(self, for_stmt):
        self.loops.append(for_stmt)
        
    def visitNext(self, next_stmt):
        logging.debug("NEXT statement = %s", next_stmt)
        #logging.debug("NEXT identifiers = %s", next_stmt.identifiers[0].identifier)
        while True:
            if len(self.loops) == 0:
                errors.fatalError("Not in a FOR loop at line %d." % next_stmt.lineNum)
            peek = self.loops[-1]
            if not isinstance(peek, ForToStep):
                errors.fatalError("Not in a FOR loop at line %d; currently in %s loop opened at line %d" % (next_stmt.lineNum, peek.description, peek.lineNum))
            
            for_stmt = self.loops.pop()
            # If the next_stmt has no attached identifiers, it applies to the
            # top FOR statement on the stack
            if len(next_stmt.identifiers) == 0:
                 next_stmt.identifiers.append(for_stmt.identifier)
            id1 = for_stmt.identifier.identifier
            print next_stmt.identifiers
            id2 = next_stmt.identifiers[0].identifier
            print "self.loops = ", self.loops
            print "id1 = ", id1
            print "id2 = ", id2
            # TODO: Check that the symbols are equal, not just the names
            if for_stmt.identifier.identifier == next_stmt.identifiers[0].identifier:
                connectLoop(next_stmt, for_stmt)
                break    
    
        
        