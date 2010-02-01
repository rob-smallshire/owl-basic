from itertools import chain

from bbc_ast import If, OnGoto
from flow.traversal import depthFirstSearch

def dumpXmlBlocks(basic_blocks, filename, options):
    import clr
    clr.AddReference('System.Xml')
    from System.Xml import XmlTextWriter, Formatting
    
    writer = XmlTextWriter(filename, None)
    writer.Formatting = Formatting.Indented
    writeHeader(writer)
    
    print basic_blocks
    
    for entry_block in basic_blocks.values():
        for block in depthFirstSearch(entry_block):
            writeBlock(writer, block)
        
    for entry_block in basic_blocks.values():
        for block in depthFirstSearch(entry_block):    
            for statement in block.statements:
                writeStatementEdges(writer, statement)   
        
    writeFooter(writer)
      
def writeHeader(writer):
    writer.WriteComment("GraphML representation of the Basic Block Graph")

    writer.WriteStartElement("graphml")
    writer.WriteAttributeString("xmlns", "http://graphml.graphdrawing.org/xmlns")
    writer.WriteAttributeString("xmlns", "xsi", None, "http://www.w3.org/2001/XMLSchema-instance")
    writer.WriteAttributeString("xmlns", "y", None, "http://www.yworks.com/xml/graphml")
    writer.WriteAttributeString("xsi", "schemaLocation", "http://graphml.graphdrawing.org/xmlns/graphml", "http://www.yworks.com/xml/schema/graphml/1.0/ygraphml.xsd")
    
    writer.WriteStartElement("key")
    writer.WriteAttributeString("id", "d0")
    writer.WriteAttributeString("for", "node")
    writer.WriteAttributeString("yfiles.type", "nodegraphics")
    writer.WriteEndElement() # key
    
    writer.WriteStartElement("key")
    writer.WriteAttributeString("id", "d1")
    writer.WriteAttributeString("for", "node")
    writer.WriteAttributeString("attr.name", "description")
    writer.WriteAttributeString("attr.type", "string")
    writer.WriteEndElement() # key
    
    writer.WriteStartElement("key")
    writer.WriteAttributeString("id", "d3")
    writer.WriteAttributeString("for", "edge")
    writer.WriteAttributeString("yfiles.type", "edgegraphics")
    writer.WriteEndElement() # key
    
    writer.WriteStartElement("key")
    writer.WriteAttributeString("id", "d4")
    writer.WriteAttributeString("for", "graphml")
    writer.WriteAttributeString("yfiles.type", "resources")
    writer.WriteEndElement() # key
    
    writer.WriteStartElement("graph")
    writer.WriteAttributeString("id", "CFG")
    writer.WriteAttributeString("edgedefault", "directed")

def writeBlock(writer, block):
    writer.WriteStartElement("node")
    writer.WriteAttributeString("id", str(block.id))
        
    writer.WriteStartElement("graph")
    writer.WriteAttributeString("edgedefault", "directed")
    
    for statement in block.statements:
        writeStatementNode(writer, statement)
    
    writer.WriteEndElement() # graph  
    writer.WriteEndElement() # node
    
def writeStatementNode(writer, statement):
    writer.WriteStartElement("node")
    writer.WriteAttributeString("id", str(statement.block.id) + '::' + str(statement.id))
    
    writer.WriteStartElement("data")
    writer.WriteAttributeString("key", "d0") # Shape and label
    writer.WriteStartElement("y:ShapeNode")
    writer.WriteStartElement("y:NodeLabel")
    writer.WriteString(str(statement.lineNum) + ": "+ str(statement.description))
    writer.WriteEndElement() # y:NodeLabel
    writer.WriteStartElement("y:Shape")
    if hasattr(statement, "entryPoint"):
        writer.WriteAttributeString("type", "hexagon")
    elif isinstance(statement, If) or isinstance(statement, OnGoto):
        writer.WriteAttributeString("type", "diamond")
    else:    
        writer.WriteAttributeString("type", "roundrectangle")
    writer.WriteEndElement() # y:Shape
    writer.WriteEndElement() # y:ShapeNode
    writer.WriteEndElement()
    
    writer.WriteStartElement("data")
    writer.WriteAttributeString("key", "d1") # description
    writer.WriteString(statement.description)
    writer.WriteEndElement()
        
    writer.WriteEndElement() # node

def writeStatementEdges(writer, statement):
    for target in chain(statement.outEdges, statement.loopBackEdges):
        writer.WriteStartElement("edge")
        writer.WriteAttributeString("source", str(statement.block.id) + '::' + str(statement.id))
        writer.WriteAttributeString("target", str(target.block.id) + '::' + str(target.id))
        writer.WriteStartElement("data")
        writer.WriteAttributeString("key", "d3")
        writer.WriteStartElement("y:PolyLineEdge")
        writer.WriteStartElement("y:Arrows")
        writer.WriteAttributeString("source", "none")
        writer.WriteAttributeString("target", "standard")
        writer.WriteEndElement() # y:Arrows
        writer.WriteEndElement() # y:PolyLineEdge
        writer.WriteEndElement() # data
        writer.WriteEndElement() # edge
    
def writeFooter(writer):
    writer.WriteEndElement() # graph
    writer.WriteEndElement() # graphml
    writer.Flush()
    writer.Close()
     