import re

from bbc_types import *

def underscoresToCamelCase(s):
    t = s.replace('_', ' ').title().replace(' ', '')
    u = t[0].lower() + t[1:]
    return u

class Node(object):
    def __init__(self, type):
        self.type = type

class BoolOption(object):
    def __init__(self, default):
        self.value = default

class AstMeta(type):
    def __init__(cls, name, bases, dict):
        super(AstMeta, cls).__init__(name, bases, dict)
        cls.child_infos = {}
        for info_name, v in dict.items():
            if isinstance(v, Node):
               cls.child_infos[info_name] = v
        
        removal = []
        for info_name in cls.child_infos.keys():
           # Create lowerCamelCase accessor
           property_name = underscoresToCamelCase(info_name)
           if info_name != property_name:
               removal.append(info_name)
           def _getProperty(self, info_name=info_name):
               return self._children[info_name]
           def _setProperty(self, value, info_name=info_name):
               self._children[info_name] = value
           setattr(cls, property_name, property(_getProperty, _setProperty))
           #dict[property_name] = property(_getProperty, _setProperty)
                
        for info_name in removal:
            delattr(cls, info_name)
    
    def __call__(cls, *args, **kwargs):
        print "cls = %s" % cls
        print "kwargs = %s" % str(kwargs)
        
        # First create the object
        obj = type.__call__(cls, *args)
        
        print obj
        
        for kwarg in kwargs:
            if kwarg in cls.__dict__ and isinstance(cls.__dict__[kwarg], property):
                print "Setting %s to %s" % (kwarg, kwargs[kwarg])
                setattr(obj, kwarg, kwargs[kwarg])
        
        # Should remove consumed kwargs here
            
        return obj
            
class AstNode(object):
    __metaclass__ = AstMeta
    
    def __init__(self):
        print "AstNode.__init__()"
        # Initialise children
        self._children = {}
        for info_name in self.child_infos.keys():
            print "info_name = %s" % info_name
            self._children[info_name] = None
        
        self._options = {}
        
    # Children accessor
    
    def _getChildren(self):
        return self._children
    
    children = property(_getChildren)
    
    # Options accessor
    
    def _getOptions(self):
        return self._options
    
    options = property(_getOptions)
        
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
    newline = BoolOption

class Circle(AstNode):
    x_coord = Node(IntegerType)
    y_coord = Node(IntegerType)
    radius  = Node(IntegerType)
    fill    = BoolOption(False)
    
#class Case(AstNode):
#    condition    = Node(ScalarType)
#    when_clauses = Node(WhenClauseList)

#class WhenClauseList(AstNode):
#    clauses = [Node(StatementList)]
#    
#    def append(self, when_clause):
#        self.clauses.append(when_clause)
    
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