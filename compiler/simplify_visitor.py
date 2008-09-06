# A visitor implementation that creates an XML representation of the abstract syntax tree

from utility import camelCaseToUnderscores
from visitor import Visitor
from node import *
from options import *
from ast_utils import elideNode

class SimplifyStatementListVisitor(Visitor):
    """
    Visitor for simplifying nested StatementList nodes by flattening the
    list of statements.
    """
    def __init__(self):
        self._accumulated_statements = []
    
    def visitAstNode(self, node):
        if node is not None:
            self._accumulated_statements.append(node)
            
    def visitStatementList(self, statement_list):
        statement_list.forEachChild(self.visit)
        
    def visitStatement(self, statement):
        """
        Append the body of the current statement, skipping the Statement node and
        filtering out None (i.e empty) statements
        """
        if statement.body is not None:
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
        "Flatten nested StatementLists and remove Statement nodes."
        if not hasattr(statement_list, "parent"):
            print statement_list.statements
            assert 0
        sslv = SimplifyStatementListVisitor()
        sslv.visit(statement_list)
        statement_list.statements = sslv.accumulatedStatements
        for index, statement in enumerate(statement_list.statements):
            statement.parent = statement_list
            statement.parent_index = index
            self.visit(statement)
            
        statement_list.parent.child_infos["statements"] = statement_list.child_infos["statements"]
        assert hasattr(statement_list, "statements")
        statement_list.parent.statements = statement_list.statements
                            
    def visitDim(self, dim):
        """
        Convert DIM statements and their lists of arrays/blocks into
        individual AllocateArray and AllocateBlock statements
        """
        items = dim.items.items
        # Locate this DIM in its parent statement list
        dim_index = dim.parent.statements.index(dim)
        dim.parent.statements.remove(dim)
        items.reverse()
        for item in items:
            dim.parent.statements.insert(dim_index, item)
            item.parent = dim.parent
            item.lineNum = dim.lineNum
            self.visit(item)
            
    def visitCase(self, case):
        "Remove the WhenClauseList level from the AST"
        case.child_infos["when_clauses"] = case.whenClauses.child_infos["clauses"]
        case.whenClauses = case.whenClauses.clauses
        for clause in case.whenClauses:
            clause.parent = case
            self.visit(clause)
            
    def visitMarkerStatement(self, marker):
        """
        Remove the followingStatement from the Repeat, moving it to immediately
        after the Repeat in the parent StatementList
        """
        if marker.followingStatement is not None:
            marker_index = marker.parent.statements.index(marker)
            marker.parent.statements.insert(marker_index + 1, marker.followingStatement.body)
            marker.followingStatement = None
        # TODO: Does the moved statement node ever get visited? Are we inserting into a sequence during iteration?
        
    def visitExpressionList(self, expr_list):
        """
        Remove ExpressionList level from the AST by replacing the contents of
        the owning attribute of its parents with the ExpressionList's own list of expressions 
        """
        expr_list.forEachChild(self.visit)
        elideNode(expr_list, liftFormalTypes=True)
        
    def visitVduList(self, vdu_list):
        """
        Remove VduList level from the AST by replacing the contents of
        the owning attribute of its parent with the VduList's own list of items 
        """
        vdu_list.forEachChild(self.visit)
        elideNode(vdu_list, liftFormalTypes=True)

    def visitActualArgList(self, actual_arg_list):
        """
        Remove the ActualArgList level from the AST by replacing the contents of
        the owning attribute of its parent with the ActualArgList's own list of arguments
        """
        actual_arg_list.forEachChild(self.visit)
        elideNode(actual_arg_list, liftFormalTypes=True)

    def visitFormalArgList(self, formal_arg_list):
        """
        Remove the FormalArgList level from the AST by replacing the contents of
        the owning attribute of its parent with the FormalArgList's own list of arguments
        """
        formal_arg_list.forEachChild(self.visit)
        elideNode(formal_arg_list, liftFormalTypes=True)
        
    def visitPrintList(self, print_list):
        """
        Remove the PrintList level from the AST by replacing the contents of the
        owning attribute of its parent.
        """
        print_list.forEachChild(self.visit)
        elideNode(print_list, liftFormalTypes=True)
        
    def visitVariableList(self, variable_list):
        """
        Remove the VariableList level from the AST by replacing the contents of the
        owning attribute of its parent.
        """
        variable_list.forEachChild(self.visit)
        elideNode(variable_list, liftFormalTypes=True)
    
    def visitExpressionList(self, expression_list):
        """
        Remove the ExpresionList level from the AST by replacing the contents of the
        owning attribute of its parent.
        """
        expression_list.forEachChild(self.visit)
        elideNode(expression_list, liftFormalTypes=True)
