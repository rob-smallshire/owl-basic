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
        self.visit(node)
        self.writer.WriteEndElement()
    
    def childListElement(self, name, nodes):
        self.writer.WriteStartElement(name)
        for node in nodes:
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
        self.writer.WriteString(str(value))
        self.writer.WriteEndAttribute()

    def visitAstNode(self, node):
        self.beginElement(node)
        for name, value in node.options.items():
            if value is not None:
                self.childAttribute(name, value)
        for name, child in node.children.items():
            if child is None:
                self.childNoneElement()
            elif isinstance(child, list):
                self.childListElement(name, child)
            else:    
                self.childElement(name, child)
        self.endElement()
        