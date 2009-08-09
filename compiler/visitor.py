# The Visitor base class

class Visitor(object):
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

class Visitable(object):
    """
    A mixin for classes which are visitable
    """    
    def accept(self, visitor):
        """
        Accept method for visitor pattern.
        """
        return self._accept(self.__class__, visitor)
    
    def _accept(self, klass, visitor):
        """
        Recursive accept implementation that calls the right visitor
        method 'overloaded' for the type of AstNode. This is done by
        appending the class name to 'visit' so if the class name is AstNode
        the method called is visitor.visitAstNode. If a method of that name
        does not exist, then it recursively attempts to call the visitor
        method on the superclass.
        """
        visitor_method = getattr(visitor, "visit%s" % klass.__name__, None)
        if visitor_method is None:
            bases = klass.__bases__
            last = None
            for i in bases:
                last = self._accept(i, visitor)
            return last
        else:
            return visitor_method(self)