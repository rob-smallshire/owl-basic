from visitor import Visitor
from find_line_visitor import FindLineVisitor
from ast_utils import *
import errors

class FlowgraphForwardVisitor(Visitor):
    """
    This visitor connects each statement node to its following statement node.
    For composite statement nodes (e.g. Program, If or Case nodes) the visitor connects
    the child nodes appropriately.
    """
    
    def __init__(self, line_mapper):
        # TODO: This should locate its own root, finding it on demand
        self.line_mapper = line_mapper
    
    # TODO: Factor this out of here
    def statementOnLine(self, targetLine):
        n = targetLine.value
        return self.line_mapper.logicalStatement(n)          
        #return self.line_to_stmt.has_key(n) and self.line_to_stmt[n]
            
    def visitAstNode(self, node):
        "Visit all children in order"
        node.forEachChild(self.visit)
            
    def connectToFollowing(self, statement):
        following = findFollowingStatement(statement)
        if following is not None:
            self.connect(statement, following)
    
    def connect(self, from_statement, to_statement):
        from_statement.addOutEdge(to_statement)
        to_statement.addInEdge(from_statement)
                    
    def visitAstStatement(self, statement):
        """
        Default behaviour for statements is to insert into the graph
        and connect to the following statement. We override this behaviour
        for conditional statements with more specific visitors.
        """
        self.connectToFollowing(statement)
    
    def visitIf(self, iff):
        """
        Connect the If to the initial statements of the true and false
        clauses.  Process each statement in both clauses.
        """
        #print "IF on line %d" % iff.lineNum
        following = findFollowingStatement(iff)
        #print "following = %s" % following
        if not following:
            errors.internal("Following statement to IF not found at line %d" % iff.lineNum)
        if iff.trueClause is not None:
            if isinstance(iff.trueClause, list):
                if len(iff.trueClause) > 0:
                    # Connect to the beginning of the true clause
                    first_true_statement = iff.trueClause[0]
                    self.connect(iff, first_true_statement)
                    
                    for statement in iff.trueClause:
                        self.visit(statement)
                else:
                    self.connect(iff.following)
            else:
                self.connect(iff, iff.trueClause)
                self.visit(iff.trueClause)                
        else:
            self.connect(iff, following)
                
        if iff.falseClause is not None:
            if isinstance(iff.falseClause, list):
                if len(iff.falseClause) > 0:
                    # Connect to the beginning of the false clause
                    first_false_statement = iff.falseClause[0]
                    self.connect(iff, first_false_statement)
                    
                    for statement in iff.falseClause:
                        self.visit(statement)
                else:
                    self.connect(iff.following)
            else:
                self.connect(iff, iff.falseClause)
                self.visit(iff.falseClause)
        else:
            self.connect(iff, following)       
            
    def visitGoto(self, goto):
        """
        Connect the Goto to the first statement on the target line if
        it exists. Error if it does not.
        """
        # TODO: targetLogicalLine needs to be a constant for this
        # to work
        #print "CFG goto"
        #print "goto.targetLogicalLine = %s" % goto.targetLogicalLine.value
        goto_target = self.statementOnLine(goto.targetLogicalLine)
        #print "goto_target = %s" % goto_target
        if goto_target:
            self.connect(goto, goto_target)
        else:
            errors.error("No such line %s at line %s" % (goto.targetLogicalLine.value, goto.lineNum))
            # TODO: Error!
            pass
            
#    def visitGosub(self, gosub):
#        """
#        Connect the Gosub to the first statement on the target line if
#        it exists. Error if it does not.
#        """
#        gosub_target = self.statementOnLine(gosub.targetLogicalLine)
#        if gosub_target:
#            self.connect(gosub, gosub_target)
#        else:
#            print "Line not found"
#            # TODO: Error!
#            pass
        
    def visitOnGoto(self, ongoto):
        """
        Connect the OnGoto to the first statement on each of the target lines
        if they exist. Error if they do not. Also connect to the first line of
        the out-of-range clause if present, and process each statement within
        that clause.
        """
        for targetLogicalLine in ongoto.targetLogicalLines:
            ongoto_target = self.statementOnLine(targetLogicalLine)
            if ongoto_target:
                self.connect(ongoto, ongoto_target)
            else:
                print "Line not found"
                # TODO: Error!
                pass
            
        if ongoto.outOfRangeClause is not None:
            if isinstance(ongoto.outOfRangeClause, list):
                if len(ongoto.outOfRangeClause) > 0:
                    # Connect to the beginning of the else clause
                    first_else_statement = ongoto.outOfRangeClause[0]
                    self.connect(ongoto, first_else_statement)
                    
                    for statement in ongoto.outOfRangeClause:
                        self.visit(statement)
                else:
                    self.connect(ongoto, ongoto.outOfRangeClause)
                    self.visit(ongoto.outOfRangeClause)
            
    def visitCase(self, case):
        """
        Connect the Case statement to the first statement of each when clause and
        the otherwise clause. Process the statements within each clause.
        """
        for when_clause in case.whenClauses:
            if when_clause.statements is not None and len(when_clause.statements) > 0:
                # Connect to the beginning of the when clause
                first_when_statement = when_clause.statements[0]
                self.connect(case,first_when_statement)
                
                for statement in when_clause.statements:
                    self.visit(statement)
                                        
    # The following are statements which do not pass control to the
    # succeeding statement in the linear source code order of the program
    
    def visitReturnFromFunction(self, return_from_function):
        # Do not connect to following statement
        pass
    
    def visitReturnFromProcedure(self, return_frin_procedure):
        # Do not connect to following statement
        pass
        
    def visitGenerateError(self, generator_error):
        # Do not connect to following statement
        pass
    
    def visitReturnError(self, return_error):
        # Do not connect to following statement
        pass
    
    def visitQuit(self, quit):
        # Do not connect to following statement
        pass
    
    def visitStop(self, stop):
        # Do not connect to following statement
        pass
                
    def visitEnd(self, end):
        # Do not connect to following statement
        pass
    
    def visitReturn(self, end):
        # Do not connect to following statement
        # TODO: Rheolism!
        pass
    
