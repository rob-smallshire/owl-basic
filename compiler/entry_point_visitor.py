from visitor import Visitor
from find_line_visitor import FindLineVisitor
from ast_utils import *
import errors

class EntryPointVisitor(Visitor):
    """
    This enumerates all of the entry-points in the supplies ast
    """
    
    def __init__(self, line_mapper):
        # TODO: This should locate its own root, finding it on demand
        self.line_mapper = line_mapper
        self.entry_points = []
    
    # TODO: Factor this out of here
    def statementOnLine(self, targetLine):
        n = targetLine.value
        return self.line_mapper.logicalStatement(n)        
        #return self.line_to_stmt.has_key(n) and self.line_to_stmt[n]
    
    def mainEntryPoint(self, statement):
        """
        Set the main() entrypoint of the program (i.e. the first line)
        """
        if not hasattr(statement, "entryPoint"):
            statement.entryPoint = "main"
        self.entry_points.insert(0, statement)
            
    def visitAstNode(self, node):
        "Visit all children in order"
        node.forEachChild(self.visit)
        
    def visitDefineProcedure(self, defproc):
        self.entry_points.append(defproc)
        defproc.entryPoint = "public"
        
    def visitDefineFunction(self, deffn):
        self.entry_points.append(deffn)
        deffn.entryPoint = "public"
        
    def visitGosub(self, gosub):
        print "EntryPointVisitor.visitGosub"
        print "GOSUB at line %s" % gosub.lineNum
        gosub_target = self.statementOnLine(gosub.targetLogicalLine)
        if gosub_target:
            print "target is %s at line %s" % (gosub_target, gosub_target.lineNum)
            self.entry_points.append(gosub_target)
            gosub_target.entryPoint = "private"
            gosub_target.addComeFromEdge(gosub)
        else:
            print "Line not found"
            # TODO: Error!
            pass
        
    