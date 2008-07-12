# A visitor implementation that creates an XML representation of the abstract syntax tree

from visitor import Visitor



class SimplifyStatementListVisitor(Visitor):
    """
    Visitor for simplifying nested StatementList nodes by flattening the
    list of statements.
    """
    def __init__(self):
        self._accumulated_statements = []
            
    def visitStatementList(self, statement_list):
        print "SimplifyStatementListVisitor.visitStatementList" 
        statement_list.forEachChild(self.visit)
        
    def visitStatement(self, statement):
        print "SimplifyStatementListVisitor.visitStatement"
        self._accumulated_statements.append(statement.body)
                
    def _accumulatedStatements(self):
        return self._accumulated_statements;
    
    accumulatedStatements = property(_accumulatedStatements)
    
class SimplificationVisitor(Visitor):
    """
    AST visitor for simplifying the AST, by removing redundant nodes.
    """
    
    def visitAstNode(self, node):
        node.forEachChild(self.visit)
    
    def visitStatementList(self, statement_list):
        print "SimplificationVisitor.visitStatementList"
        sslv = SimplifyStatementListVisitor()
        sslv.visit(statement_list)
        statement_list.statements = sslv.accumulatedStatements
        for statement in statement_list.statements:
            self.visit(statement)