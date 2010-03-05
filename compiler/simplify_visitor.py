import logging

from utility import camelCaseToUnderscores
from visitor import Visitor
from node import *
from options import *
from ast_utils import elideNode, insertStatementAfter
from bbc_ast import StatementList, Next

logger = logging.getLogger('simplify_visitor')

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
        
    def visitAstStatement(self, statement):
        self._accumulated_statements.append(statement)
                    
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
            statement.parent_property = "statements"
            statement.parent_index = index
            self.visit(statement)
            
        statement_list.parent.child_infos["statements"] = statement_list.child_infos["statements"]
        assert hasattr(statement_list, "statements")
        statement_list.parent.statements = statement_list.statements
    
    def visitIf(self, iff):
        if isinstance(iff.trueClause, StatementList):
            sslv = SimplifyStatementListVisitor()
            sslv.visit(iff.trueClause)
            iff.child_infos['true_clause'] = iff.trueClause.child_infos['statements']
            iff.trueClause = sslv.accumulatedStatements
            if len(iff.trueClause) == 0:
                iff.trueClause = None
            else:
                for index, statement in enumerate(iff.trueClause):
                    statement.parent = iff
                    statement.parent_property = 'trueClause'
                    statement.parent_index = index
                    self.visit(statement)
        else:
            self.visit(iff.trueClause)
                
        if isinstance(iff.falseClause, StatementList):
            sslv = SimplifyStatementListVisitor()
            sslv.visit(iff.falseClause)
            iff.child_infos['false_clause'] = iff.falseClause.child_infos['statements']
            iff.falseClause = sslv.accumulatedStatements
            if len(iff.falseClause) == 0:
                iff.falseClause = None
            else:
                for index, statement in enumerate(iff.falseClause):
                    statement.parent = iff
                    statement.parent_property = 'falseClause'
                    statement.parent_index = index
                    self.visit(statement)
        else:
            self.visit(iff.falseClause)
                    
        self.visit(iff.condition)
    
    def visitOnGoto(self, ongoto):
        if ongoto.outOfRangeClause is not None:
            if isinstance(ongoto.outOfRangeClause, StatementList):
                sslv = SimplifyStatementListVisitor()
                sslv.visit(ongoto.outOfRangeClause)
                ongoto.child_infos['out_of_range_clause'] = ongoto.outOfRangeClause.child_infos['statements']
                ongoto.outOfRangeClause = sslv.accumulatedStatements
                if len(ongoto.outOfRangeClause) == 0:
                    ongoto.outOfRangeClause = None
                else:
                    for index, statement in enumerate(ongoto.outOfRangeClause):
                        statement.parent = ongoto
                        statement.parent_property = 'outOfRangeClause'
                        statement.parent_index = index
                        self.visit(statement)
            else:
                self.visit(ongoto.outOfRangeClause)
                
        self.visit(ongoto.switch)
        self.visit(ongoto.targetLogicalLines)
                                    
    def visitDim(self, dim):
        """
        Convert DIM statements and their lists of arrays/blocks into
        individual AllocateArray and AllocateBlock statements
        """
        # TODO: Move to SeparationVisitor
        items = dim.items.items
        # Locate this DIM in its parent statement list
        dim_index = dim.parent.statements.index(dim)
        dim.parent.statements.remove(dim)
        items.reverse()
        for item in items:
            dim.parent.statements.insert(dim_index, item)
            item.parent = dim.parent
            item.parent_property = dim.parent_property
            item.parent_index = dim_index
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
        Remove the followingStatement from the Repeat, DefineProcedure, etc, moving it to immediately
        after the statement in the parent StatementList
        """
        logger.debug("visitMarkerStatement %s at line number %s", marker, marker.lineNum)
        if marker.followingStatement is not None:
            following = marker.followingStatement
            marker.followingStatement = None
            insertStatementAfter(marker, following)
            # TODO: Does the moved statement node ever get visited? Are we inserting into a sequence during iteration?
            #self.visit(following)
                   
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
    
    def visitInputList(self, input_list):
        """
        Remove the InputList level from the AST by replacing the contents of the
        owning attribute of its parent.
        """
        input_list.forEachChild(self.visit)
        elideNode(input_list, liftFormalTypes=True)
        
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

    # TODO: visitInputList
    
    