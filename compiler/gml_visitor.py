# A visitor implementation that creates an XML representation of the control flow graph

from visitor import Visitor
from bbc_ast import If, OnGoto

class GmlVisitor(Visitor):
    """
    AST visitor for converting the CFG into an XML representation in GraphML.
    We traverse the AST rather than the CFG to output the graph. We can more reliably
    visit all nodes, since we know the AST is a single connected component.
    """
    def __init__(self, filename, out_edges=True, in_edges=False, back_edges=True):
        # .NET Framework
        import clr
        clr.AddReference('System.Xml')
        from System.Xml import XmlTextWriter, Formatting
        
        self.out_edges = out_edges
        self.in_edges  = in_edges
        self.back_edges = back_edges
        
        self.writer = XmlTextWriter(filename, None)
        
        self.writer.Formatting = Formatting.Indented
        self.writer.WriteComment("GraphML representation of the Control Flow Graph")

        self.writer.WriteStartElement("graphml")
        self.writer.WriteAttributeString("xmlns", "http://graphml.graphdrawing.org/xmlns")
        self.writer.WriteAttributeString("xmlns", "xsi", None, "http://www.w3.org/2001/XMLSchema-instance")
        self.writer.WriteAttributeString("xmlns", "y", None, "http://www.yworks.com/xml/graphml")
        self.writer.WriteAttributeString("xsi", "schemaLocation", "http://graphml.graphdrawing.org/xmlns/graphml", "http://www.yworks.com/xml/schema/graphml/1.0/ygraphml.xsd")
        
        self.writer.WriteStartElement("key")
        self.writer.WriteAttributeString("id", "d0")
        self.writer.WriteAttributeString("for", "node")
        self.writer.WriteAttributeString("yfiles.type", "nodegraphics")
        self.writer.WriteEndElement() # key
        
        self.writer.WriteStartElement("key")
        self.writer.WriteAttributeString("id", "d1")
        self.writer.WriteAttributeString("for", "node")
        self.writer.WriteAttributeString("attr.name", "description")
        self.writer.WriteAttributeString("attr.type", "string")
        self.writer.WriteEndElement() # key
        
        self.writer.WriteStartElement("key")
        self.writer.WriteAttributeString("id", "d3")
        self.writer.WriteAttributeString("for", "edge")
        self.writer.WriteAttributeString("yfiles.type", "edgegraphics")
        self.writer.WriteEndElement() # key
        
        self.writer.WriteStartElement("key")
        self.writer.WriteAttributeString("id", "d4")
        self.writer.WriteAttributeString("for", "graphml")
        self.writer.WriteAttributeString("yfiles.type", "resources")
        self.writer.WriteEndElement() # key
        
        self.writer.WriteStartElement("graph")
        self.writer.WriteAttributeString("id", "CFG")
        self.writer.WriteAttributeString("edgedefault", "directed")
        
    def close(self):
        self.writer.WriteEndElement() # graph
        self.writer.WriteEndElement() # graphml
        self.writer.Flush()
        self.writer.Close()

    def visitAstNode(self, node):
        node.forEachChild(self.visit)
        
    def visitAstStatement(self, node):
        self.writer.WriteStartElement("node")
        self.writer.WriteAttributeString("id", str(node.id))
        
        self.writer.WriteStartElement("data")
        self.writer.WriteAttributeString("key", "d0") # Shape and label
        self.writer.WriteStartElement("y:ShapeNode")
        self.writer.WriteStartElement("y:NodeLabel")
        self.writer.WriteString(str(node.lineNum) + ": "+ str(node.description) + ": " + ';'.join(node.entryPoints))
        self.writer.WriteEndElement() # y:NodeLabel
        self.writer.WriteStartElement("y:Shape")
        if hasattr(node, "entryPoint"):
            self.writer.WriteAttributeString("type", "hexagon")
        elif isinstance(node, If) or isinstance(node, OnGoto):
            self.writer.WriteAttributeString("type", "diamond")
        else:    
            self.writer.WriteAttributeString("type", "roundrectangle")
        self.writer.WriteEndElement() # y:Shape
        self.writer.WriteEndElement() # y:ShapeNode
        self.writer.WriteEndElement()
        
        self.writer.WriteStartElement("data")
        self.writer.WriteAttributeString("key", "d1") # description
        self.writer.WriteString(node.description)
        self.writer.WriteEndElement()
        
        self.writer.WriteEndElement() # node
        
        if self.out_edges:
            for target in node.outEdges:
                self.writer.WriteStartElement("edge")
                self.writer.WriteAttributeString("source", str(node.id))
                self.writer.WriteAttributeString("target", str(target.id))
                self.writer.WriteStartElement("data")
                self.writer.WriteAttributeString("key", "d3")
                self.writer.WriteStartElement("y:PolyLineEdge")
                self.writer.WriteStartElement("y:Arrows")
                self.writer.WriteAttributeString("source", "none")
                self.writer.WriteAttributeString("target", "standard")
                self.writer.WriteEndElement() # y:Arrows
                self.writer.WriteEndElement() # y:PolyLineEdge
                self.writer.WriteEndElement() # data
                self.writer.WriteEndElement() # edge
        
        if self.in_edges:
            for source in node.inEdges:
                self.writer.WriteStartElement("edge")
                self.writer.WriteAttributeString("source", str(source.id))
                self.writer.WriteAttributeString("target", str(node.id))
                self.writer.WriteStartElement("data")
                self.writer.WriteAttributeString("key", "d3")
                self.writer.WriteStartElement("y:PolyLineEdge")
                self.writer.WriteStartElement("y:Arrows")
                self.writer.WriteAttributeString("source", "none")
                self.writer.WriteAttributeString("target", "standard")
                self.writer.WriteEndElement() # y:Arrows
                self.writer.WriteEndElement() # y:PolyLineEdge
                self.writer.WriteEndElement() # data
                self.writer.WriteEndElement() # edge
        
        if self.back_edges:
             for target in node.loopBackEdges:
                self.writer.WriteStartElement("edge")
                self.writer.WriteAttributeString("source", str(node.id))
                self.writer.WriteAttributeString("target", str(target.id))
                self.writer.WriteStartElement("data")
                self.writer.WriteAttributeString("key", "d3")
                self.writer.WriteStartElement("y:PolyLineEdge")
                self.writer.WriteStartElement("y:Arrows")
                self.writer.WriteAttributeString("source", "none")
                self.writer.WriteAttributeString("target", "standard")
                self.writer.WriteEndElement() # y:Arrows
                self.writer.WriteEndElement() # y:PolyLineEdge
                self.writer.WriteEndElement() # data
                self.writer.WriteEndElement() # edge
                
        node.forEachChild(self.visit)
            
        
        
        