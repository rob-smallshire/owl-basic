# The Visitor base class

class Visitor:
    """
    A base visitor class
    """
    
    def visit(self, node):
        """
        Visits a given node by telling the node to call this Visitor's
        class-specific visitor method.
        """
        return node.accept(self)
    