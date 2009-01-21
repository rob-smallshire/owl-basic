# Control Flow Graph Node

class CfgVertex(object):
    __counter = 0
    
    def __init__(self):
        self.__in_edges  = []
        self.__out_edges = []
        self.__come_from_edges = []
        self.__entry_points = set()
        
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
    
    def _getComeFromEdges(self):
        return self.__come_from_edges
    
    comeFromEdges = property(_getComeFromEdges)
    
    def _getEntryPoints(self):
        return self.__entry_points
    
    entryPoints = property(_getEntryPoints)
    
    def clearInEdges(self):
        self.__in_edges = []
    
    def clearOutEdges(self):
        self.__out_edges = []
    
    def clearComeFromEdges(self):
        self.__come_from_edges = []
    
    def clearEntryPoints(self):
        self.__entry_points.clear()
    
    def addInEdge(self, from_vertex):
        self.inEdges.append(from_vertex)
        
    def addOutEdge(self, to_vertex):
        self.outEdges.append(to_vertex)
        
    def addComeFromEdge(self, from_vertex):
        self.comeFromEdges.append(from_vertex)
        
    def addEntryPoint(self, name):
        self.entryPoints.add(name)
        