'''
Algorithms for traversal of the control flow graph
'''

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
