import logging
from owl_basic.visitor import Visitor
from owl_basic.ast_utils import *
from owl_basic import errors

class EntryPointVisitor(Visitor):
    """
    This enumerates all of the entry-points in the supplied AST
    """
    
    def __init__(self, line_mapper):
        # TODO: This should locate its own root, finding it on demand
        self.line_mapper = line_mapper
        self.__entry_points = {}
    
    entryPoints = property(lambda self: self.__entry_points)
                
    def mainEntryPoint(self, statement):
        '''
        Set the main() entrypoint of the program (i.e. the first line)
        '''
        if not hasattr(statement, "entryPoint"):
            statement.entryPoint = "__owl__main"
        self.__entry_points['__owl__main'] = statement
            
    def visitAstNode(self, node):
        "Visit all children in order"
        node.forEachChild(self.visit)
        
    def visitDefineProcedure(self, defproc):
        self.__entry_points[defproc.name] = defproc
        defproc.entryPoint = "public"
        
    def visitDefineFunction(self, deffn):
        self.__entry_points[deffn.name] = deffn
        deffn.entryPoint = "public"
        
    def visitGosub(self, gosub):
        gosub_target = self.line_mapper.statementOnLine(gosub.targetLogicalLine)
        if gosub_target:
            self.__entry_points["gosub%d" % int(gosub.targetLogicalLine.value)] = gosub_target
            gosub_target.entryPoint = "private"
            gosub_target.addComeFromGosubEdge(gosub)
        else:
            logging.debug("Line not found")
            # TODO: Error!
            pass

    def visitOnGosub(self, ongosub):
        # Each ON x GOSUB target is a GOSUB'd subroutine, registered exactly as a
        # plain GOSUB target so it is converted to a PROC.
        for target_line in ongosub.targetLogicalLines:
            target = self.line_mapper.statementOnLine(target_line)
            if target:
                self.__entry_points["gosub%d" % int(target_line.value)] = target
                target.entryPoint = "private"
                target.addComeFromGosubEdge(ongosub)
        
    