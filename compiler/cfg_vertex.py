# Control Flow Graph Node

class CfgVertex(object):
    __counter = 0
    
    def __init__(self):
        self.__in_edges  = []
        self.__out_edges = []
        
        CfgVertex.__counter += 1
        self.__id = CfgVertex.__counter
    
    def _getId(self):
        return self.__id
    
    id = property(_getId)
        
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
        