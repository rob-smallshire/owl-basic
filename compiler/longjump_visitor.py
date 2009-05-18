# A visitor for locating longjumps

from visitor import Visitor
import errors
from utility import underscoresToCamelCase
from bbc_types import *
from bbc_ast import Goto, LongJump
from ast_utils import elideNode
import flow_analysis

class LongjumpVisitor(Visitor):
    """
    AST visitor for locating long jumps (jumps out of
    procedures or functions) and replacing GOTOs with LONGJUMPs
    """
    def __init__(self, line_mapper):
        self.line_mapper = line_mapper
        self.longjumps = []
        
    def visitAstNode(self, node):
        node.forEachChild(self.visit)
    
    def visitCfgVertex(self, vertex):
        "Generic visitor for simple statements"
        
        # Check the entry points
        for following in vertex.outEdges:
            if len(vertex.entryPoints) > 0:
                # Not unreachable code
                if following.entryPoints != vertex.entryPoints:
                    if isinstance(vertex, Goto):
                        self.longjumps.append(vertex)
            else:
                # TODO: Improve error message
                errors.warning("Unreachable statement at line %s" % vertex.lineNum)

        vertex.forEachChild(self.visit)      
        
    def createLongjumps(self):
        """
        Iterate through the discovered long jump locations, modify entry point
        tags in the following statements, replace Goto nodes with Longjump nodes
        and modify the control flow graph.
        """
        #print "createLongjumps"
        for node in self.longjumps:
            flow_analysis.deTagSuccessors(node)
            
        for node in self.longjumps:
            node.__class__ = LongJump
            for target in node.outEdges:
                target.inEdges.remove(node)
            node.clearOutEdges()
        