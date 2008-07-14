# A visitor implementation that creates an XML representation of the abstract syntax tree

from visitor import Visitor


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
        for statement in statement_list.statements:
            statement.parent = statement_list
            self.visit(statement)
            
        statement_list.parent.child_infos["statements"] = []
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
        case.child_infos["when_clauses"] = []
        case.whenClauses = case.whenClauses.clauses
        for clause in case.whenClauses:
            clause.parent = case
            self.visit(clause)
            
    def visitExpressionList(self, expr_list):
        """
        Remove ExpressionList level from the AST by replacing the contents of
        the owning attribute of its parents with the ExpressionList's own list of expressions 
        """
        for expr in expr_list.expressions:
            expr.parent = expr_list.parent
            expr.parent_property = expr_list.parent_property
            self.visit(expr)
        expr_list.parent.child_infos[expr_list.parent_property] = []
        assert hasattr(expr_list.parent, expr_list.parent_property)
        setattr(expr_list.parent, expr_list.parent_property, expr_list.expressions)
        
    def visitVduList(self, vdu_list):
        """
        Remove VduList level from the AST by replacing the contents of
        the owning attribute of its parent with the VduList's own list of items 
        """
        for item in vdu_list.items:
            item.parent = vdu_list.parent
            item.parent_property = vdu_list.parent_property
            self.visit(item)
        vdu_list.parent.child_infos[vdu_list.parent_property] = []
        assert hasattr(vdu_list.parent, vdu_list.parent_property)
        setattr(vdu_list.parent, vdu_list.parent_property, vdu_list.items)
        
    def visitFormalArgList(self, formal_arg_list):
        """
        Remove the FormalArgList level from the AST by replacing the contents of
        the owning attribute of its parent with the FormalArgList's own list of arguments
        """
        print "visitFormalArgList"
        print "formal_arg_list.parent_property = %s" % formal_arg_list.parent_property
        for arg in formal_arg_list.arguments:
            arg.parent = formal_arg_list.parent
            arg.parent_property = formal_arg_list.parent_property
            self.visit(arg)
        formal_arg_list.parent.child_infos[formal_arg_list.parent_property] = []
        assert hasattr(formal_arg_list.parent, formal_arg_list.parent_property)
        setattr(formal_arg_list.parent, formal_arg_list.parent_property, formal_arg_list.arguments)    