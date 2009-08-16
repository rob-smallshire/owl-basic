from visitor import Visitor
import ast_utils
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
            ast_utils.insertStatementBefore(gosub, proc)
            ast_utils.removeStatement(gosub)
        else:
            errors.fatalError("Cannot compile computed GOSUB target at line %s" % gosub.lineNum)        
        
    def visitReturn(self, ret):
        # Convert each RETURN to an ENDPROC by changing the class
        ret.__class__ = ReturnFromProcedure
        
