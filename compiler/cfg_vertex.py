# Control Flow Graph Node

class CfgVertex(object):
    __counter = 0
    
    def __init__(self):
        self.__in_edges  = set()
        self.__out_edges = set()
        self.__come_from_edges = set()
        self.__back_edges = set()
        self.__entry_points = set()
        
        CfgVertex.__counter += 1
        self.__id = CfgVertex.__counter
        
        self.block = None
    
    def _getId(self):
        return self.__id
    
    id = property(_getId)
        
    def _getInEdges(self):
        return self.__in_edges
    
    inEdges = property(_getInEdges)
    
    def _getOutEdges(self):
        return self.__out_edges
    
    outEdges = property(_getOutEdges)
    
    def _getComeFromEdges(self):
        return self.__come_from_edges
    
    comeFromEdges = property(_getComeFromEdges)
    
    def _getBackEdges(self):
        return self.__back_edges
    
    backEdges = property(_getBackEdges)
    
    def _getEntryPoints(self):
        return self.__entry_points
    
    entryPoints = property(_getEntryPoints)
    
    def clearInEdges(self):
        self.__in_edges = set()
    
    def clearOutEdges(self):
        self.__out_edges = set()
    
    def clearComeFromEdges(self):
        self.__come_from_edges = set()
    
    def clearEntryPoints(self):
        self.__entry_points.clear()
    
    def addInEdge(self, from_vertex):
        self.inEdges.add(from_vertex)
        
    def addOutEdge(self, to_vertex):
        self.outEdges.add(to_vertex)
        
    def addComeFromEdge(self, from_vertex):
        self.comeFromEdges.add(from_vertex)
    
    def addBackEdge(self, to_vertex):
        self.backEdges.add(to_vertex)
        
    def addEntryPoint(self, name):
        self.entryPoints.add(name)
        
    inDegree  = property(lambda self: len(self.__in_edges) + len(self.__come_from_edges))
    outDegree = property(lambda self: len(self.__out_edges) + len(self.__back_edges))
    
    
        