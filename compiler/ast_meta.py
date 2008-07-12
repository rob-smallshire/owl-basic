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

class FloatOption(Option):
    def __init__(self, default=None):
        self.value = default

class StringOption(Option):
    def __init__(self, default=None):
        self.value = default

class AstMeta(type):
    def __new__(cls, name, bases, dict):  
        # Allocate child infos
        dict["child_infos"] = {}
        for base in bases:
            if "child_infos" in base.__dict__:
                dict["child_infos"].update(base.__dict__["child_infos"])
        
        # Allocate option infos        
        dict["option_infos"] = {}
        for base in bases:
            if "option_infos" in base.__dict__:
                dict["option_infos"].update(base.__dict__["option_infos"])
                
        return type.__new__(cls, name, bases, dict)
        
    def __init__(cls, name, bases, dict):
        """
        Configure the class that is being created by introspecting its
        'declaration' and creating getters, setters and properties for its
        data memebers.
        """
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
        node_infos = {}           
        for info_name, v in dict.items():
            if isinstance(v, Node):
               node_infos[info_name] = v
                
        removal = []
        for info_name in node_infos.keys():
           property_name = underscoresToCamelCase(info_name)
           if info_name != property_name:
               removal.append(info_name)
           def _getProperty(self, info_name=info_name):
               return self._children[info_name]
           def _setProperty(self, value, info_name=info_name):
               print "info_name = %s" % info_name
               self._children[info_name] = value
           setattr(cls, property_name, property(_getProperty, _setProperty))
                        
        for info_name in removal:
            delattr(cls, info_name)
            
        cls.child_infos.update(node_infos)
    
    def _createChildListProperties(cls, name, bases, dict):    
        """
        Introspect the class being created to look for class members which
        contain 'declarative' [Node] objects. Move these declarations into the
        child_infos class member, and create getters, setters and properties
        to provide access to each of the child members.
        """
        list_infos = {}
        for info_name, v in dict.items():
            if isinstance(v, list) and isinstance(v[0], Node):
               list_infos[info_name] = v
                
        removal = []
        for info_name in list_infos.keys():
           property_name = underscoresToCamelCase(info_name)
           if info_name != property_name:
               removal.append(info_name)
           def _getProperty(self, info_name=info_name):
               return self._children[info_name]
           def _setProperty(self, value, info_name=info_name):
               print "info_name = %s" % info_name
               self._children[info_name] = value
           setattr(cls, property_name, property(_getProperty, _setProperty))
                        
        for info_name in removal:
            delattr(cls, info_name)
    
        cls.child_infos.update(list_infos)
    
    def _createOptionProperties(cls, name, bases, dict):
        """
        Introspect the class being created to look for class members which
        contain 'declarative' Option objects. Move these declarations into the
        option_infos class member, and create getters, setters and properties
        to provide access to each of the child members.
        """
        infos = {}
        for info_name, v in dict.items():
            if isinstance(v, Option):
               infos[info_name] = v
                
        removal = []
        for info_name in infos.keys():
           property_name = underscoresToCamelCase(info_name)
           if info_name != property_name:
               removal.append(info_name)
           def _getProperty(self, info_name=info_name):
               return self._options[info_name]
           def _setProperty(self, value, info_name=info_name):
               print "info_name = %s" % info_name
               self._options[info_name] = value
           setattr(cls, property_name, property(_getProperty, _setProperty))
                        
        for info_name in removal:
            delattr(cls, info_name)
            
        cls.option_infos.update(infos)
    
    def __call__(cls, *args, **kwargs):
        """
        Called when instances of classes with this metaclass. i.e. AstNodes.
        Consume keyword arguments with the same name as child properties and options then
        set the appropriate attributes.
        """        
        # First create the object
        obj = type.__call__(cls, *args)
                
        for kwarg in kwargs:
            if hasattr(cls, kwarg): # TODO: How to we test this? and isinstance(cls.__dict__[kwarg], property):
                setattr(obj, kwarg, kwargs[kwarg])
            else:
                raise AttributeError("No such property initialiser as '%s' on '%s'" % (kwarg, cls.__name__))
        
        # TODO: Should remove consumed kwargs here
            
        return obj
            
class AstNode(object):
    __metaclass__ = AstMeta
    
    #child_infos = {}
    
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
