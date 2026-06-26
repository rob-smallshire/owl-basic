import logging

from owl_basic.utility import camelCaseToUnderscores
from owl_basic.visitor import Visitor
from owl_basic.node import *
from owl_basic.options import *
from owl_basic.ast_utils import elideNode, insertStatementAfter
from owl_basic.syntax.ast import StatementList, Next

logger = logging.getLogger('simplify_visitor')


def _localize_child_infos(node):
    """Give *node* its own ``child_infos`` before reclassifying a child.

    ``child_infos`` is a class-level dict shared by every instance of the node
    type, so mutating it in place (e.g. when a clause changes from a single
    StatementList child to a list of statements) would corrupt all other
    instances of that type across the whole process. Copying onto the instance
    shadows the class dict and keeps the change local.
    """
    if "child_infos" not in node.__dict__:
        node.child_infos = dict(node.child_infos)

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
            logging.debug("statements: %s", statement_list.statements)
            assert 0
        sslv = SimplifyStatementListVisitor()
        sslv.visit(statement_list)
        statement_list.statements = sslv.accumulatedStatements
        for index, statement in enumerate(statement_list.statements):
            statement.parent = statement_list
            statement.parent_property = "statements"
            statement.parent_index = index
            self.visit(statement)
            
        _localize_child_infos(statement_list.parent)
        statement_list.parent.child_infos["statements"] = statement_list.child_infos["statements"]
        assert hasattr(statement_list, "statements")
        statement_list.parent.statements = statement_list.statements
    
    def visitIf(self, iff):
        if isinstance(iff.trueClause, StatementList):
            sslv = SimplifyStatementListVisitor()
            sslv.visit(iff.trueClause)
            _localize_child_infos(iff)
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
            _localize_child_infos(iff)
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
                _localize_child_infos(ongoto)
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
            
    def visitCase(self, case):
        "Remove the WhenClauseList level and flatten each clause's body."
        _localize_child_infos(case)
        case.child_infos["when_clauses"] = case.whenClauses.child_infos["clauses"]
        case.whenClauses = case.whenClauses.clauses
        for index, clause in enumerate(case.whenClauses):
            clause.parent = case
            clause.parent_property = "whenClauses"
            clause.parent_index = index
            # Flatten the clause body (a StatementList) into a plain list on the
            # clause, exactly as visitIf does for its clauses, so the body
            # statements live in the CFG and a body's last statement rejoins
            # after ENDCASE (via findFollowingStatement).
            if isinstance(clause.statements, StatementList):
                sslv = SimplifyStatementListVisitor()
                sslv.visit(clause.statements)
                _localize_child_infos(clause)
                clause.child_infos["statements"] = \
                    clause.statements.child_infos["statements"]
                clause.statements = sslv.accumulatedStatements
                for statement_index, statement in enumerate(clause.statements):
                    statement.parent = clause
                    statement.parent_property = "statements"
                    statement.parent_index = statement_index
                    self.visit(statement)
            else:
                self.visit(clause.statements)
            # The WHEN match expressions are not statements; simplify them too.
            matches = getattr(clause, "matches", None)
            if matches is not None:
                self.visit(matches)
        self.visit(case.condition)
            
    def visitMarkerStatement(self, marker):
        """
        Remove the followingStatement from the Repeat, DefineProcedure, etc, moving it to immediately
        after the statement in the parent StatementList
        """
        logger.debug("visitMarkerStatement %s at line number %s", marker, marker.lineNum)
        if marker.followingStatement is not None:
            following = marker.followingStatement
            marker.followingStatement = None
            # Separation may have replaced the following statement with a
            # StatementList (e.g. REPEAT READ X -> REPEAT (X=READ:...), or a
            # multi-variable READ/NEXT/DIM). Splice its statements in one by one
            # so none reaches the flow graph as an un-flattened StatementList --
            # this move happens after the list-flattening pass above.
            if isinstance(following, StatementList):
                previous = marker
                for statement in list(following.statements):
                    insertStatementAfter(previous, statement)
                    previous = statement
            else:
                insertStatementAfter(marker, following)
                   
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
    
    