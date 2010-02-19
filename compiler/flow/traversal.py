'''
Algorithms for traversal of the control flow graph
'''

import logging
from itertools import chain

logger = logging.getLogger('flow.traversal')

def depthFirstSearch(vertex, visited = None):
    '''
    A generator which performs depth first search from the supplied vertex through
    the control flow graph.
    :param vertex: A CFG Vertex from which depth first search will be performed
    :param visited: A, optional set of vertices which need not be visited
    :yields: Successive CfgVertices in a depth first traversal of the graph
    '''
    to_visit = []
    if visited is None:
        visited = set()
    to_visit.append(vertex)
    while len(to_visit) != 0:
        v = to_visit.pop()
        if v not in visited:
            visited.add(v)
            yield v
            to_visit.extend(v.outEdges)

class ApproximateToplogicalOrderer(object):
    
    def __init__(self, vertex, vertices_to_consider):
        self.order = []
        self.stack = []
        self.cur_dfsnum = 0
        self.index = {}
        self.low = {}
        self.vertices_to_consider = vertices_to_consider
           
        for v in self.vertices_to_consider:
            self.index[v] = "To be done"
            
        # Special case the start vertex to prevent infinite recursion
        self.index[vertex] = "Done"
        for successor in chain(vertex.outEdges, vertex.loopBackEdges):
            if successor in self.vertices_to_consider:
                if self.index[successor] == "To be done":
                    self.visit(successor)
        self.order.insert(0, vertex)
        
    def visit(self, cur_vertex):
        self.index[cur_vertex] = self.cur_dfsnum
        self.low[cur_vertex] = self.cur_dfsnum
        self.cur_dfsnum += 1
        self.stack.append(cur_vertex)
        
        for successor in chain(cur_vertex.outEdges, cur_vertex.loopBackEdges):
            if successor in self.vertices_to_consider:
                if self.index[successor] == "To be done":
                    self.visit(successor)
                    self.low[cur_vertex] = min(self.low[cur_vertex], self.low[successor])
                elif self.index[successor] == "Done":
                    pass
                
                #else:
                elif successor in self.stack:
                    self.low[cur_vertex] = min(self.low[cur_vertex], self.index[successor])
                    
        if self.low[cur_vertex] == self.index[cur_vertex]:
            # We found a strongly connected component
            scc = []
            while True:
                popped = self.stack.pop()
                scc.append(popped)
                self.index[popped] = "Done"
                if popped == cur_vertex:
                    break
                
            if len(scc) == 1:
                self.order.insert(0, cur_vertex)
            else:
                self.order = approximateTopologicalOrder(self.chooseFirst(scc), scc) + self.order
        
    def chooseFirst(self, scc):
        '''
        Returns the vertex with the most in edges which are not in scc. This function
        is used for computing a likely starting point for the SCC.
        :param scc: A list of vertices comprising a strong-connected-component.
        '''
        sizes = [v.inDegree for v in scc]
        index = sizes.index(max(sizes))
        return scc[index]

def approximateTopologicalOrder(vertex, vertices_to_consider=None):
    '''
    A function which performs approximate topological ordering of the vertices
    reachable from the supplied vertices, taking into account strongly
    connected components in the graph.
    :param vertex: The starting CfgVertex
    :param vertices_to_consider: A set of vertices to which the search should be limited. If None, all vertices
                                 reachable from vertex are used.
    :returns A sequence of basic blocks in approximate toplogical order
    '''
    logger.debug("approximateTopologicalOrder(%s, %s)", str(vertex), str(vertices_to_consider))
    vertices_under_consideration = set(depthFirstSearch(vertex)) if vertices_to_consider is None else vertices_to_consider
    ato = ApproximateToplogicalOrderer(vertex, vertices_under_consideration)
    assert set(ato.order) == set(vertices_under_consideration)
    return ato.order

               
                