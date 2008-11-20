# Control Flow Graph Node

class CfgVertex(object):
    def __init__(self):
        self.__in_edges  = []
        self.__out_edges = []
        
    def _getInEdges(self):
        return self.__in_edges
    
    inEdges = property(_getInEdges)
    
    def _getOutEdges(self):
        return self.__out_edges
    
    outEdges = property(_getOutEdges)
    
    def addInEdge(self, from_vertex):
        self.inEdges.append(from_vertex)
        
    def addOutEdge(self, to_vertex):
        self.outEdges.append(to_vertex)
        