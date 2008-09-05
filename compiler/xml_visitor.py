# A visitor implementation that creates an XML representation of the abstract syntax tree

from visitor import Visitor

class XmlVisitor(Visitor):
    """
    AST visitor for converting the AST into an XML representation.
    """
    def __init__(self, filename):
        # .NET Framework
        import clr
        clr.AddReference('System.Xml')
        from System.Xml import XmlTextWriter, Formatting
        
        self.writer = XmlTextWriter(filename, None)
        self.writer.Formatting = Formatting.Indented
        self.writer.WriteComment("XML Parse Tree")
        
    def close(self):
        self.writer.Flush()
        self.writer.Close()

    def beginElement(self, node):
        name = node.__class__.__name__
        self.writer.WriteStartElement(name)
        
    def endElement(self):
        self.writer.WriteEndElement()
    
    def childElement(self, name, node):
        self.writer.WriteStartElement(name)
        if node is None:
            self.childNoneElement()
        else:
            self.visit(node)
        self.writer.WriteEndElement()
    
    def childNodeElement(self, name, node):
        self.writer.WriteStartElement(name)
        if node is None:
            self.childNoneElement()
        else:
            if name in node.parent.child_infos:
                print "node = %s, name = %s" % (node, name)
                print "node.parent.child_infos = %s" % str(node.parent.child_infos)
                # TODO: Next if is temporary
                if not isinstance(node.parent.child_infos[name], list):
                    if node.parent.child_infos[name].nodeType is not None:
                        self.childAttribute("node_type", node.parent.child_infos[name].nodeType)
                    if node.parent.child_infos[name].formalType is not None:
                        self.childAttribute("formal_type", node.parent.child_infos[name].formalType)
            self.visit(node)
        self.writer.WriteEndElement()
    
    def childListElement(self, name, nodes):
        self.writer.WriteStartElement(name)
        for node in nodes:
            if node is None:
                self.childNoneElement()
            else:
                self.visit(node)
        self.writer.WriteEndElement()
    
    def childTextElement(self, name, text):
        self.writer.WriteStartElement(name)
        self.writer.WriteString(str(text))
        self.writer.WriteEndElement()
    
    def childNoneElement(self):
        self.writer.WriteStartElement("None")
        self.writer.WriteEndElement()
    
    def childAttribute(self, name, value):
        self.writer.WriteStartAttribute(name)
        if isinstance(value, type):
            if hasattr(value, '__doc__'):
                self.writer.WriteString(value.__doc__)
            else:
                self.writer.WriteString(value.__name__)
        else:
            self.writer.WriteString(str(value))
        self.writer.WriteEndAttribute()

    def visitAstNode(self, node):
        self.beginElement(node)
        for name, value in node.options.items():
            if value is not None:
                self.childAttribute(name, value)
        for name, child in node.children.items():
            print "child = %s" % child
            if isinstance(child, list):
                print "child!"
                self.childListElement(name, child)
            else:    
                print "node!"
                self.childNodeElement(name, child)
        self.endElement()
        