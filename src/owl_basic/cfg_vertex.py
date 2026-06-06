# Control Flow Graph Node

class CfgVertex(object):
    __counter = 0
    
    def __init__(self):
        self.__in_edges  = set()
        self.__out_edges = set()
        self.__come_from_gosub_edges = set()
        self.__loop_back_edges = set()
        self.__loop_from_edges = set()
        self.__entry_points = set()
        
        CfgVertex.__counter += 1
        self.__id = CfgVertex.__counter
        
        self.block = None
        
    id                 = property(lambda self: self.__id)  
    inEdges            = property(lambda self: self.__in_edges)
    outEdges           = property(lambda self: self.__out_edges)
    comeFromGosubEdges = property(lambda self: self.__come_from_gosub_edges)
    loopBackEdges      = property(lambda self: self.__loop_back_edges)
    loopFromEdges      = property(lambda self: self.__loop_from_edges)
    entryPoints        = property(lambda self: self.__entry_points)
    
    def clearInEdges(self):
        self.__in_edges = set()
    
    def clearOutEdges(self):
        self.__out_edges = set()
    
    def clearComeFromGosubEdges(self):
        self.__come_from_gosub_edges = set()
    
    def clearLoopBackEdges(self):
        self.__loop_back_edges = set()
        
    def clearLoopFromEdges(self):
        self.__loop_from_edges = set()
    
    def clearEntryPoints(self):
        self.__entry_points.clear()
        
    def addInEdge(self, from_vertex):
        self.inEdges.add(from_vertex)
        
    def addOutEdge(self, to_vertex):
        self.outEdges.add(to_vertex)
        
    def addComeFromGosubEdge(self, from_vertex):
        self.comeFromGosubEdges.add(from_vertex)
    
    def addLoopBackEdge(self, to_vertex):
        self.loopBackEdges.add(to_vertex)
        
    def addLoopFromEdge(self, to_vertex):
        self.loopFromEdges.add(to_vertex)
        
    def addEntryPoint(self, name):
        self.entryPoints.add(name)
        
    inDegree  = property(lambda self: len(self.inEdges) + len(self.comeFromGosubEdges) + len(self.loopFromEdges))
    outDegree = property(lambda self: len(self.outEdges) + len(self.loopBackEdges))
        