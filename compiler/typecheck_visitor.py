# A visitor for performing type-checking over the Abstract Syntax Tree

from visitor import Visitor

class TypecheckVisitor(Visitor):
    """
    AST visitor for converting the AST into an XML representation.
    """
    def __init__(self):
        pass
    
    def visitAstNode(self, node):
        pass
    
    def visitBinaryOperation(self, binop):
        