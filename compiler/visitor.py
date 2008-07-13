# The Visitor base class

class Visitor:
    """
    A base visitor class
    """
    
    def visit(self, node):
        """
        Visits a given node by telling the node to call this Visitor's
        class-specific visitor method. No-op if node is None.
        """
        if node is not None:
            return node.accept(self)
    