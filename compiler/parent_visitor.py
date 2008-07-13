from functools import partial

from visitor import Visitor

class ParentVisitor(Visitor):
    """
    Visitor setting and verifying existing parent references on each AST node
    """
    def __init__(self):
        pass
    
    def visitAstNode(self, node):
        node.forEachChild(partial(self._setParent, parent = node))
        
    def _setParent(self, parent, node):
        if hasattr(node, "parent"):
            assert node.parent is parent
        node.parent = parent
        