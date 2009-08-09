class ControlFlowVertex(object):
    """
    A vertex in the ControlFlowGraph.
    """
    def __init__(self, data):
        self.data = data
        self.in_edges = []
        self.out_edges = []

class ControlFlowGraph(object):
    """
    Storage of the ControlFlowGraph.  Built by the FlowGraphVisitor.
    """
    
    def __init__(self):
        self.vertices = [] # Graph 'nodes' containing AST statements
        self.edges = []    # Adjacency list - contains (from, to) tuples for directed edges
    
    def insert(self, statement):
        """
        Insert a vertex into the graph. Typically
        """
        
        self.vertices.append()
        