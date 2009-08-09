import re
import sys

from utility import underscoresToCamelCase, hasprop
from node import *
from options import *
from bbc_types import *
from visitor import Visitable
        
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
        
        if '__doc__' in dict:
            dict["_description"] = dict['__doc__']
        else:
            dict["_description"] = name
                
        return type.__new__(cls, name, bases, dict)
        
    def __init__(cls, name, bases, dict):
        """
        Configure the class that is being created by introspecting its
        'declaration' and creating getters, setters and properties for its
        data members.
        """
        cls._createChildProperties(name, bases, dict)
        cls._createChildListProperties(name, bases, dict)
        cls._createOptionProperties(name, bases, dict)
        super(AstMeta, cls).__init__(name, bases, dict)
    
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
               self._children[info_name] = value
           if not hasprop(cls, property_name):
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
               self._children[info_name] = value
           if not hasprop(cls, property_name):
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
               self._options[info_name] = value
           if not hasprop(cls, property_name):
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
            if hasprop(cls, kwarg):
                setattr(obj, kwarg, kwargs[kwarg])
            else:
                raise AttributeError("No such property initialiser as '%s' on '%s'" % (kwarg, cls.__name__))
        
        # TODO: Should remove consumed kwargs here
            
        return obj
            
class AstNode(Visitable):
    __metaclass__ = AstMeta
    
    formal_type = TypeOption()
    actual_type = TypeOption()
    line_num = IntegerOption()
    
    def __init__(self):
        self.parent = None
        
        self.__symbol_table = None
        
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
        super(AstNode, self).__init__()
        
    # Children accessor
    
    def _getChildren(self):
        return self._children
    
    children = property(_getChildren)
    
    # Options accessor
    
    def _getOptions(self):
        return self._options
    
    options = property(_getOptions)
    
    def forEachChild(self, f):
        for child in self.children.values():
            if isinstance(child, list):
                for subchild in child:
                    f(subchild)
            else:
                f(child)
                
    def findChild(self, search_child):
        """Locate a child node within this AstNode. Returns a tuple containing
           (property_name, index) where index may be None for non-indexable properties. Returns None
           if the child is not found"""
        for name, child in self.children.items():
            if isinstance(child, list):
                for index, subchild in enumerate(child):
                    if subchild is search_child:
                        return (underscoresToCamelCase(name), index)
            else:
                if child is search_child:
                   return (underscoresToCamelCase(name), None)
        return (None, None) 
    
    def _getDescription(self):
        return self._description or self.__class__.__name__
    
    description = property(_getDescription)
    
    def setProperty(self, value, property_name, index=None):
        if index is not None:
            getattr(self, property_name)[index] = value
        else:
            setattr(self, property_name, value)
    
    def _getSymbolTable(self):
        return self.__symbol_table
    
    def _setSymbolTable(self, table):
        self.__symbol_table = table
        
    symbolTable = property(_getSymbolTable, _setSymbolTable)
    

