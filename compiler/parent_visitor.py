from functools import partial

from visitor import Visitor

class ParentVisitor(Visitor):
    """
    Visitor setting and verifying existing parent references on each AST node
    """
    def __init__(self):
        pass
    
    def visitAstNode(self, node):
        # TODO: This partial function application doesn't work correctly with IronPython
        #node.forEachChild(partial(self._setParent, parent = node))
        
        # TODO: Inlining the forEachChild function works, however...
        for name, child in node.children.items():
            if isinstance(child, list):
                for subchild in child:
                    self._setParent(node, name, subchild)
            else:
                self._setParent(node, name, child) 
        
        node.forEachChild(self.visit)
        
    def _setParent(self, parent, parent_property, node):
        if node is not None:
            if hasattr(node, "parent"):
                assert node.parent is parent
            node.parent_property = parent_property # The property through which the parent can be accessed.
            node.parent = parent
        