from visitor import Visitor
from ast_utils import *

class LineNumberVisitor(Visitor):
    """
    This visitor builds a map from logical line numbers to the first statement
    to appear on that line. It is used for resolving the targets of GOTO, GOSUB, etc.
    """
    
    # TODO: This could be made into a much more useful in-order traversal visitor
    
    def __init__(self):
        # TODO: This should locate its own root, finding it on demand
        self.line_to_stmt = {}

    def registerStatement(self, statement):
        line_num = statement.lineNum
        if not self.line_to_stmt.has_key(line_num):
            self.line_to_stmt[line_num] = statement

    def firstStatementOnLine(self, line_number):
        return self.line_to_stmt[line_number]
            
    def visitAstNode(self, node):
        "Visit all children in order"
        node.forEachChild(self.visit)
                    
    def visitAstStatement(self, statement):
        self.registerStatement(statement)
            
    def visitIf(self, iff):
        """
        Process an IF statement. The true clause always precedes
        the false clause so we process that first
        """
        self.registerStatement(iff)
        
        if iff.trueClause is not None:
            if isinstance(iff.trueClause, list):
                for node in iff.trueClause:
                    self.visit(node)
            else:
                self.visit(iff.trueClause)
       
        if iff.falseClause is not None:
            if isinstance(iff.falseClause, list):
                for node in iff.falseClause:
                    self.visit(node)
            else:
                self.visit(iff.falseClause)
                   
    # TODO: Need BASIC IV and BASIC V statements here.
    
    
    
    
    
    
        
        
            
        