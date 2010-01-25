from visitor import Visitor
from ast_utils import replaceStatement
from bbc_ast import LiteralInteger, CallProcedure, ReturnFromProcedure
import errors

class ConvertSubVisitor(Visitor):
    """
    Replaces RETURN with ENDPROC
    """
    
    def __init__(self):
        pass
            
    def visitAstNode(self, node):
        node.forEachChild(self.visit)
        
    def visitGosub(self, gosub):
        if isinstance(gosub.targetLogicalLine, LiteralInteger):
            # Convert to a procedure call
            proc = CallProcedure(name="PROCSub" + str(gosub.targetLogicalLine.value))
            replaceStatement(gosub, proc)           
        else:
            errors.fatalError("Cannot compile computed GOSUB target at line %s" % gosub.lineNum)        
        
    def visitReturn(self, ret):
        # Convert each RETURN to an ENDPROC by changing the class
        ret.__class__ = ReturnFromProcedure
        
