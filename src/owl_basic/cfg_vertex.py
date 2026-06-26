# Control Flow Graph Node

from owl_basic.ordered_set import OrderedSet


class CfgVertex(object):
    __counter = 0

    def __init__(self):
        # Edge collections are OrderedSets so traversals follow program order
        # and compilation is deterministic (see owl_basic.ordered_set). The
        # entry-point tags stay a plain set: only order-independent set algebra
        # (issubset, difference) is done on them, never an order-sensitive walk.
        self.__in_edges  = OrderedSet()
        self.__out_edges = OrderedSet()
        self.__come_from_gosub_edges = OrderedSet()
        self.__loop_back_edges = OrderedSet()
        self.__loop_from_edges = OrderedSet()
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
        self.__in_edges = OrderedSet()

    def clearOutEdges(self):
        self.__out_edges = OrderedSet()

    def clearComeFromGosubEdges(self):
        self.__come_from_gosub_edges = OrderedSet()

    def clearLoopBackEdges(self):
        self.__loop_back_edges = OrderedSet()

    def clearLoopFromEdges(self):
        self.__loop_from_edges = OrderedSet()
    
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
        