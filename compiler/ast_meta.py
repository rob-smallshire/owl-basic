import re
import sys

from bbc_types import *

def underscoresToCamelCase(s):
    t = s.replace('_', ' ').title().replace(' ', '')
    u = t[0].lower() + t[1:]
    return u

class Node(object):
    def __init__(self, type=None):
        self.type = type

class Option(object):
    pass

class BoolOption(Option):
    def __init__(self, default=None):
        self.value = default
        
class IntegerOption(Option):
    def __init__(self, default=None):
        self.value = default

class AstMeta(type):
    def __init__(cls, name, bases, dict):
        """
        Configure the class that is being created by introspecting its
        'declaration' and creating getters, setters and properties for its
        data memebers.
        """
        super(AstMeta, cls).__init__(name, bases, dict)
        cls._createChildProperties(name, bases, dict)
        cls._createChildListProperties(name, bases, dict)
        cls._createOptionProperties(name, bases, dict)
    
    # TODO: These methods have a lot of common code.
    
    def _createChildProperties(cls, name, bases, dict):    
        """
        Introspect the class being created to look for class members which
        contain 'declarative' Node objects. Move these declarations into the
        child_infos class member, and create getters, setters and properties
        to provide access to each of the child members.
        """
        cls.child_infos = {}
        for info_name, v in dict.items():
            if isinstance(v, Node):
               cls.child_infos[info_name] = v
                
        removal = []
        for info_name in cls.child_infos.keys():
           property_name = underscoresToCamelCase(info_name)
           if info_name != property_name:
               removal.append(info_name)
           def _getProperty(self, info_name=info_name):
               return self._children[info_name]
           def _setProperty(self, value, info_name=info_name):
               self._children[info_name] = value
           setattr(cls, property_name, property(_getProperty, _setProperty))
                        
        for info_name in removal:
            delattr(cls, info_name)
    
    def _createChildListProperties(cls, name, bases, dict):    
        """
        Introspect the class being created to look for class members which
        contain 'declarative' [Node] objects. Move these declarations into the
        child_infos class member, and create getters, setters and properties
        to provide access to each of the child members.
        """
        cls.child_infos = {}
        for info_name, v in dict.items():
            if isinstance(v, list) and isinstance(v[0], Node):
               cls.child_infos[info_name] = v
                
        removal = []
        for info_name in cls.child_infos.keys():
           property_name = underscoresToCamelCase(info_name)
           if info_name != property_name:
               removal.append(info_name)
           def _getProperty(self, info_name=info_name):
               return self._children[info_name]
           def _setProperty(self, value, info_name=info_name):
               self._children[info_name] = value
           setattr(cls, property_name, property(_getProperty, _setProperty))
                        
        for info_name in removal:
            delattr(cls, info_name)
    
    def _createOptionProperties(cls, name, bases, dict):
        """
        Introspect the class being created to look for class members which
        contain 'declarative' Option objects. Move these declarations into the
        option_infos class member, and create getters, setters and properties
        to provide access to each of the child members.
        """
        cls.option_infos = {}
        for info_name, v in dict.items():
            if isinstance(v, Option):
               cls.option_infos[info_name] = v
                
        removal = []
        for info_name in cls.option_infos.keys():
           property_name = underscoresToCamelCase(info_name)
           if info_name != property_name:
               removal.append(info_name)
           def _getProperty(self, info_name=info_name):
               return self._options[info_name]
           def _setProperty(self, value, info_name=info_name):
               self._options[info_name] = value
           setattr(cls, property_name, property(_getProperty, _setProperty))
                        
        for info_name in removal:
            delattr(cls, info_name)
    
    def __call__(cls, *args, **kwargs):
        """
        Called when instances of classes with this metaclass. i.e. AstNodes.
        Consume keyword arguments with the same name as child properties and options then
        set the appropriate attributes.
        """        
        # First create the object
        obj = type.__call__(cls, *args)
                
        for kwarg in kwargs:
            if kwarg in cls.__dict__ and isinstance(cls.__dict__[kwarg], property):
                setattr(obj, kwarg, kwargs[kwarg])
        
        # Should remove consumed kwargs here
            
        return obj
            
class AstNode(object):
    __metaclass__ = AstMeta
    
    def __init__(self):
        # Initialise children
        self._children = {}
        for info_name, info in self.child_infos.items():
            if isinstance(info, Node):
                self._children[info_name] = None
            elif isinstance(info, list):
                self._children[info_name] = []
        
        self._options = {}
        for info_name, option in self.option_infos.items():
            self._options[info_name] = option.value
        
    # Children accessor
    
    def _getChildren(self):
        return self._children
    
    children = property(_getChildren)
    
    # Options accessor
    
    def _getOptions(self):
        return self._options
    
    options = property(_getOptions)
    
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

# ================================================================

# Visitors for testing

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
    
    def childTextElement(self, name, text):
        self.writer.WriteStartElement(name)
        self.writer.WriteString(str(text))
        self.writer.WriteEndElement()
    
    def childAttribute(self, name, value):
        self.writer.WriteStartAttribute(name)
        self.writer.WriteString(str(value))
        self.writer.WriteEndAttribute()

    def visitAstNode(self, node):
        self.beginElement(node)
        for name, value in node.options.items():
            self.childAttribute(name, value)
        for name, child in node.children.items():
            self.childElement(name, child)
        self.endElement()

class BasicVisitor(Visitor):
    """
    AST visitor for converting the AST into back into OWL BASIC.
    """
    def __init__(self):
        pass
        
    def visitLiteralInteger(self, integer):
        sys.stdout.write(str(integer.value))
        
    def visitCircle(self, circle):
        sys.stdout.write("CIRCLE ")
        if circle.fill:
            sys.stdout.write("FILL ")
        self.visit(circle.xCoord)
        sys.stdout.write(", ")
        self.visit(circle.yCoord)
        sys.stdout.write(", ")
        self.visit(circle.radius)
        sys.stdout.write('\n')

# ================================================================
        
class Envelope(AstNode):
    n                 = Node(IntegerType)
    t                 = Node(IntegerType)
    pitch1            = Node(IntegerType)
    pitch2            = Node(IntegerType)
    pitch3            = Node(IntegerType)
    num_steps_1       = Node(IntegerType)
    num_steps_2       = Node(IntegerType)
    num_steps_3       = Node(IntegerType)
    amplitude_attack  = Node(IntegerType)
    amplitude_decay   = Node(IntegerType)
    amplitude_sustain = Node(IntegerType)
    amplitude_release = Node(IntegerType)
    target_attack     = Node(IntegerType)
    target_decay      = Node(IntegerType)
    
class Bput(AstNode):
    channel = Node(ChannelType)
    data    = Node(IntegerType)
    newline = BoolOption(False)

class Circle(AstNode):
    x_coord = Node(IntegerType)
    y_coord = Node(IntegerType)
    radius  = Node(IntegerType)
    fill    = BoolOption(False)

class LiteralInteger(AstNode):
    value = IntegerOption()

class Case(AstNode):
    condition    = Node(ScalarType)
    when_clauses = Node()

class WhenClauseList(AstNode):
    clauses = [Node()]
    
    def append(self, when_clause):
        self.clauses.append(when_clause)
    
class Data(AstNode):
    data = Node(ScalarType)
    
    def __init__(self, data):
        super(Data, self).__init__()
        self.data = self.parse(data)
    
    def parse(self, data):
        "Parse the text following a DATA statement into items"
        # Break the data into fields
        raw_items = re.findall(r'(?:\s*"((?:[^"]+|"")*)"(?!")\s*)|([^,]+)', data)
        items = []
        for i, (quoted, unquoted) in enumerate(raw_items):
            if quoted:
                item = quoted.replace('""', '"')
            else:
                item = unquoted.lstrip()
                # If its the last item on the line, strip trailing space
                if i == len(raw_items) - 1:
                    item = item.rstrip()
            items.append(item)
        print items
        return items