from owl_basic.visitor import Visitor
from owl_basic.ast_utils import replaceStatement
from owl_basic.syntax.ast import LiteralInteger, CallProcedure, ReturnFromProcedure
from owl_basic import errors

class ConvertSubVisitor(Visitor):
    """
    Replaces RETURN with ENDPROC
    """

    def __init__(self, entry_points=None):
        # entry_points maps each entry name to its entry statement. We need it
        # so that replacing a GOSUB that is itself an entry point can move the
        # reference to the replacement (see visitGosub).
        self.entry_points = entry_points if entry_points is not None else {}

    def visitAstNode(self, node):
        node.forEachChild(self.visit)

    def visitGosub(self, gosub):
        if isinstance(gosub.targetLogicalLine, LiteralInteger):
            # Convert to a procedure call
            proc = CallProcedure(name="PROCSub" + str(gosub.targetLogicalLine.value))
            replaceStatement(gosub, proc)
            # If this GOSUB was an entry point (the program's first statement is
            # a GOSUB, so it is __owl__main), repoint the entry to the call.
            # replaceStatement disconnects the old node from the CFG, and basic
            # block identification starts each method's walk from the node held
            # in entry_points -- leaving the stale Gosub there yields a main
            # method that is a lone, un-lowerable Gosub.
            for name, entry in list(self.entry_points.items()):
                if entry is gosub:
                    self.entry_points[name] = proc
        else:
            errors.fatalError("Cannot compile computed GOSUB target at line %s" % gosub.lineNum)
        
    def visitReturn(self, ret):
        # Convert each RETURN to an ENDPROC by changing the class
        ret.__class__ = ReturnFromProcedure
        
