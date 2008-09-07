from visitor import Visitor

class FlowgraphVisitor(Visitor):
    
    def __init__(self):
        self.cdg = ControlFlowGraph()
    
    def visitAstStatement(self, statement):
        """
        Used for regular statements which do not affect the
        control flow. 
        """
        next_index = statement.parent_index + 1
        if next_index > len(getattr(statement.parent, statement.parent_property)):
            # TODO: No more statements in this list!
            next_statement = None
        else
            next_statement = getattr(statement.parent, statement.parent_property)[next_index]
        self.connect(statement, next_statement)
        
    def visitGoto(self, goto):
        # TODO: Do GOTOs need to be resolved before the other
        #       flowgraph edges?
        self.connectJump(goto)
        
    def visitGosub(self, gosub):
        # TODO: Do GOSUBs need to be resolved before the other
        #       flowgraph edges?
        self.connectJump(gosub)
    
    def visitUntil(self, until):
        # Locate the previous REPEAT statement
        self.findAllReverse(until, Repeat)
        
    def findAllReverse(self, node, queryType):
        """
        Search backwards from node to find a node that matches the query
        function.
        """        
        while len(statement.previousStatements) > 0:
            # TODO: This is all wrong!
            if node is queryType:
                return [node]
            if len(statement.previousStatements == 1):
                statement = statement.previousStatement
            else:
                for statement in statement.previousStatements:
                    result.extend(findAllReverse(statement))
    
    def connectJump(self, jump):
        # TODO: This relies on constant folding having been done
        logical_line_number = jump.targetLogicalLine
        if logical_line_number is None:
            error("%s target could not be evaluated at compile time" % jump.__doc__)
        target_statement = findStatement(logical_line_number)
        if target_statement is None:
            error("%s target line %d does not exist" % (jump.__doc__, logical_line_number)
        connect(jump, target_statement)
            
    def connect(self, predecesor, successor):
        """
        Insert a bidirectal edge between two nodes is the flowgraph
        """
        predecessor.nextStatement = successor
        successor.previousStatements.append(predecessor)
        
            
        