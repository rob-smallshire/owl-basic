import logging

from owl_basic.visitor import Visitor
from owl_basic.ast_utils import findFollowingStatement
from .connectors import connect, connectToFollowing
from owl_basic import errors

logger = logging.getLogger('flow.flowgraph_visitor')

class FlowgraphForwardVisitor(Visitor):
    """
    This visitor connects each statement node to its following statement node.
    For composite statement nodes (e.g. Program, If or Case nodes) the visitor connects
    the child nodes appropriately.
    """
    
    def __init__(self, line_mapper):
        self.line_mapper = line_mapper
               
    def visitAstNode(self, node):
        "Visit all children in order"
        node.forEachChild(self.visit)
                                
    def visitAstStatement(self, statement):
        """
        Default behaviour for statements is to insert into the graph
        and connect to the following statement. We override this behaviour
        for conditional statements with more specific visitors.
        """
        connectToFollowing(statement)
    
    def visitIf(self, iff):
        """
        Connect the If to the initial statements of the true and false
        clauses.  Process each statement in both clauses.
        """
        # `following` may be None: when the IF is the last statement, a branch
        # that would fall through to "the next statement" instead runs off the
        # end of the program -- a terminal node, not an error.
        following = findFollowingStatement(iff)

        def connect_fall_through():
            # The condition-true (no THEN body) or condition-false (no ELSE body)
            # path continues at the following statement, or terminates if none.
            if following is not None:
                connect(iff, following)

        if iff.trueClause is not None:
            if isinstance(iff.trueClause, list):
                if len(iff.trueClause) > 0:
                    # Connect to the beginning of the true clause
                    first_true_statement = iff.trueClause[0]
                    connect(iff, first_true_statement)

                    for statement in iff.trueClause:
                        self.visit(statement)
                else:
                    connect_fall_through()
            else:
                connect(iff, iff.trueClause)
                self.visit(iff.trueClause)
        else:
            connect_fall_through()

        if iff.falseClause is not None:
            if isinstance(iff.falseClause, list):
                if len(iff.falseClause) > 0:
                    # Connect to the beginning of the false clause
                    first_false_statement = iff.falseClause[0]
                    connect(iff, first_false_statement)

                    for statement in iff.falseClause:
                        self.visit(statement)
                else:
                    connect_fall_through()
            else:
                connect(iff, iff.falseClause)
                self.visit(iff.falseClause)
        else:
            connect_fall_through()
            
    def visitGoto(self, goto):
        """
        Connect the Goto to the first statement on the target line if
        it exists. Error if it does not.
        """
        # TODO: targetLogicalLine needs to be a constant for this
        # to work
        #print "CFG goto"
        logger.debug("visitGoto")
        #print "goto.targetLogicalLine = %s" % goto.targetLogicalLine.value
        goto_target = self.line_mapper.statementOnLine(goto.targetLogicalLine)
        #print "goto_target = %s" % goto_target
        if goto_target:
            connect(goto, goto_target)
        else:
            errors.error("No such line %s at line %s" % (goto.targetLogicalLine.value, goto.lineNum))
                    
    def visitOnError(self, on_error):
        """Connect ON ERROR to the next statement (normal flow) and to its
        handler, which runs via the runtime error path. The handler must be in
        the CFG so it gets a basic block and is analysed/lowered; normal flow
        skips it (it is reached only by the error dispatch).

        ON ERROR GOTO <line> connects to the existing target line. A statement
        handler (the rest of the line) is connected at its first statement, and
        the handler statements are chained into the CFG; they normally end in
        END/GOTO, which terminate, so they do not fall back into normal flow."""
        connectToFollowing(on_error)
        statements = getattr(on_error.handler, "statements", None)
        if not statements:
            return  # ON ERROR OFF
        if len(statements) == 1 and type(statements[0]).__name__ == "Goto":
            target = self.line_mapper.statementOnLine(statements[0].targetLogicalLine)
            if target:
                connect(on_error, target)
            return
        connect(on_error, statements[0])
        for statement in statements:
            self.visit(statement)

    def visitOnGosub(self, ongosub):
        """ON x GOSUB calls a subroutine and returns, so control continues at the
        following statement. The targets are PROCs reached via come-from-GOSUB
        edges (registered by the entry-point visitor), not normal successors."""
        connectToFollowing(ongosub)

    def visitOnGoto(self, ongoto):
        """
        Connect the OnGoto to the first statement on each of the target lines
        if they exist. Error if they do not. Also connect to the first line of
        the out-of-range clause if present, and process each statement within
        that clause.
        """
        logger.debug("visitOnGoto")
        ongoto.targetStatements = [] # TODO: Fix this so it isn't a monkey patch!
        for targetLogicalLine in ongoto.targetLogicalLines:
            ongoto_target = self.line_mapper.statementOnLine(targetLogicalLine)
            if ongoto_target:
                connect(ongoto, ongoto_target)
                ongoto.targetStatements.append(ongoto_target)
            else:
                errors.error("No such line %s at line %s" % (targetLogicalLine.value, ongoto.lineNum))
        
        first_else_statement = None    
        if ongoto.outOfRangeClause is not None:
            if isinstance(ongoto.outOfRangeClause, list):
                if len(ongoto.outOfRangeClause) > 0:
                    # Connect to the beginning of the else clause
                    first_else_statement = ongoto.outOfRangeClause[0]
                    connect(ongoto, first_else_statement)
                    
                    for statement in ongoto.outOfRangeClause:
                        self.visit(statement)
            else:
                first_else_statement = ongoto.outOfRangeClause
                connect(ongoto, ongoto.outOfRangeClause)
                self.visit(ongoto.outOfRangeClause)
        ongoto.outOfRangeStatement = first_else_statement  # TODO: Fix this so it isn't a monkey patch!

        assert hasattr(ongoto, "targetStatements")
        assert hasattr(ongoto, "outOfRangeStatement")
            
    def visitCase(self, case):
        """
        Connect the Case statement to the first statement of each when clause and
        the otherwise clause. Process the statements within each clause.
        """
        logger.debug("visitCase")
        for when_clause in case.whenClauses:
            if when_clause.statements is not None and len(when_clause.statements) > 0:
                # Connect to the beginning of the when clause
                first_when_statement = when_clause.statements[0]
                connect(case,first_when_statement)
                
                for statement in when_clause.statements:
                    self.visit(statement)
                                        
    # The following are statements which do not pass control to the
    # succeeding statement in the linear source code order of the program
    
    def visitReturnFromFunction(self, return_from_function):
        # Do not connect to following statement
        logger.debug("visitReturnFromFunction")

    def visitReturnFromProcedure(self, return_frin_procedure):
        # Do not connect to following statement
        logger.debug("visitReturnFromProcedure")
    
    def visitRaise(self, raise_stmt):
        # A raised exception transfers control out of the routine; like a return,
        # it does not fall through to the following statement.
        logger.debug("visitRaise")

    def visitGenerateError(self, generator_error):
        # Do not connect to following statement
        logger.debug("visitGenerateError")

    def visitReturnError(self, return_error):
        # Do not connect to following statement
        logger.debug("visitReturnError")

    def visitQuit(self, quit):
        # Do not connect to following statement
        logger.debug("visitQuit")

    def visitStop(self, stop):
        # Do not connect to following statement
        logger.debug("visitStop")
            
    def visitEnd(self, end):
        # Do not connect to following statement
        logger.debug("visitEnd")

    def visitChain(self, chain):
        # CHAIN replaces the running program: control never returns, so it is a
        # terminal node with no edge to the following statement.
        logger.debug("visitChain")

    def visitReturn(self, end):
        # Do not connect to following statement
        # TODO: Rheolism!
        logger.debug("visitReturn")
    
    
