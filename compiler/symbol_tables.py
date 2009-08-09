import logging

from singleton import Singleton
from bbc_types import *

# Symbol table

class AddSymbolException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class SymbolInfo(object):
    """
    Stores information regarding a symbol
    """
    (modifier_static, modifier_system, modifier_global, modifier_arg, modifier_ref_arg, modifier_local, modifier_private) = range(7)
    
    def __init__(self, name, type, modifier=None, table=None, rank=None):
        self.name     = name
        self.table    = table
        self.type     = type
        self.modifier = modifier
        self.rank     = rank
    
class SymbolTable(object):
    
    protections = range(3)
    (readonly, writethrough, writable) = protections
    
    symbol_tables = set()
    
    def __init__(self, name, protection=writable, parent=None):
        self.__name = name
        assert protection in SymbolTable.protections
        self.__protection = protection
        assert parent is None or isinstance(parent, SymbolTable)
        self.__parent = parent
        self._symbols = {} # TODO: Wrap this in a property
        logging.debug("Creating symbol table %s", self.__name)
        SymbolTable.symbol_tables.add(self)
    
    def __getName(self):
        return self.__name
    
    name = property(__getName)
    
    def __getSymbols(self):
        return self._symbols
    
    symbols = property(__getSymbols)
    
    def __getParent(self):
        return self.__parent
    
    parent = property(__getParent)
    
    def isWritable(self):
        return self.__protection == SymbolTable.writable
    
    def isWritethrough(self):
        return self.__protection == SymbolTable.writethrough
    
    def isReadonly(self):
        return self.__protection == SymbolTable.readonly
    
    def tryAdd(self, symbol_info):
        """
        Add a SymbolInfo object to the table if its not already present.
        Returns True if the symbol was added, otherwise False.
        """
        if self.lookup(symbol_info.name) is None:
            self.add(symbol_info)
            return True
        return False
        
    def add(self, symbol_info):
        """
        Add a SymbolInfo object to the table
        """
        if self.isWritable():
            symbol_info.table = self
            self._symbols[symbol_info.name] = symbol_info
        elif self.isWritethrough():
            if self.__parent is not None:
                self.__parent.add(symbol_info)
            else:
                raise AddSymbolException("Cannot add symbol '%s' because write-through symbol table '%s' has no parent" % (symbol_info.name, self.name))
        elif self.isReadonly():
            raise AddSymbolException("Cannot add symbol '%s' to read-only symbol table '%s'" % (symbol_info.name, self.name))
        
    def lookup(self, name):
        """
        Returns a SymbolInfo object or None
        """
        if name in self._symbols:
            return self._symbols[name]
        if self.__parent is not None:
            return self.__parent.lookup(name)
        return None

class StaticSymbolTable(SymbolTable, Singleton):
    """
    A symbol table used for representing the built-in static
    integer variables A% to Z%
    """
    
    def __init__(self):
        super(StaticSymbolTable, self).__init__("static symbol table", protection=SymbolTable.readonly, parent=None)
        # Add IntegerTypes for A% to Z% into the symbol table
        names = [chr(x) + '%' for x in range(65, 91)]
        symbol_infos = [(name, SymbolInfo(name, IntegerType, SymbolInfo.modifier_static)) for name in names]
        self._symbols.update(symbol_infos)
         
class SystemSymbolTable(SymbolTable, Singleton):
    """
    A symbol table for build-in system variables.
    """
    
    def __init__(self):
        super(SystemSymbolTable, self).__init__("system symbol table", protection=SymbolTable.readonly, parent=StaticSymbolTable.getInstance())
        # Add the built-in symbols
        self._symbols['@%'] = SymbolInfo('@%', IntegerType, SymbolInfo.modifier_system)
        self._symbols['@hwnd%'] = SymbolInfo('@hwnd%', PtrType, SymbolInfo.modifier_system)
        self._symbols['@memhdc%'] = SymbolInfo('@memhdc%', PtrType, SymbolInfo.modifier_system)
        self._symbols['@prthdc%'] = SymbolInfo('@prthdc%', PtrType, SymbolInfo.modifier_system)
        self._symbols['@hcsr%'] = SymbolInfo('@hcsr%', IntegerType, SymbolInfo.modifier_system)
        self._symbols['@hpal%'] = SymbolInfo('@hpal%', IntegerType, SymbolInfo.modifier_system)
        self._symbols['@msg%'] = SymbolInfo('@msg%', IntegerType, SymbolInfo.modifier_system)
        self._symbols['@wparam%'] = SymbolInfo('@wparam%', IntegerType, SymbolInfo.modifier_system)
        self._symbols['@lparam%'] = SymbolInfo('@lparam%', IntegerType, SymbolInfo.modifier_system)
        self._symbols['@midi%'] = SymbolInfo('@midi%', IntegerType, SymbolInfo.modifier_system)
        self._symbols['@ispal%'] = SymbolInfo('@ispal%', IntegerType, SymbolInfo.modifier_system)
        self._symbols['@hfile%'] = SymbolInfo('@hfile%', IntegerType, SymbolInfo.modifier_system)
        self._symbols['@vdu%'] = SymbolInfo('@vdu%', IntegerType, SymbolInfo.modifier_system)
        self._symbols['@cmd$'] = SymbolInfo('@cmd$', StringType, SymbolInfo.modifier_system)
        self._symbols['@dir$'] = SymbolInfo('@dir$', StringType, SymbolInfo.modifier_system)
        self._symbols['@hmdi%'] = SymbolInfo('@hmdi%', IntegerType, SymbolInfo.modifier_system)
        self._symbols['@flags%'] = SymbolInfo('@flags%', IntegerType, SymbolInfo.modifier_system)
        self._symbols['@lib$'] = SymbolInfo('@lib$', StringType, SymbolInfo.modifier_system)
        self._symbols['@ox%'] = SymbolInfo('@ox%', IntegerType, SymbolInfo.modifier_system)
        self._symbols['@oy%'] = SymbolInfo('@oy%', IntegerType, SymbolInfo.modifier_system)
        self._symbols['@tmp$'] = SymbolInfo('@tmp$', StringType, SymbolInfo.modifier_system)
        self._symbols['@usr$'] = SymbolInfo('@usr$', StringType, SymbolInfo.modifier_system)
        self._symbols['@vdu{}'] = SymbolInfo('@vdu{}', IntegerType, SymbolInfo.modifier_system)

class ScopedSymbolTable(SymbolTable):
    """
    A symbol table containing additional scope information.
    """
    def __init__(self, procedure, protection, parent):
        super(ScopedSymbolTable, self).__init__(procedure, protection, parent)
        self.procedure = procedure

class FormalParameterSymbolTable(ScopedSymbolTable):
    """
    A write-through symbol table for storing formal parameters of
    procedures and functions
    """
    def __init__(self, symbol_infos, procedure, parent):
        super(FormalParameterSymbolTable, self).__init__("formal parameters for PROC/FN %s" % procedure, SymbolTable.writethrough, parent)
        print "symbol_infos = %s" % symbol_infos
        for symbol_info in symbol_infos:
            self._symbols[symbol_info.name] = symbol_info

class LocalSymbolTable(ScopedSymbolTable):
    """
    A write-through symbol table for storing local variables. Generated by a LOCAL statement
    """
    def __init__(self, symbol_infos, procedure, parent):
        super(LocalSymbolTable, self).__init__("LOCAL symbols for %s" % procedure, SymbolTable.writethrough, parent)
        for symbol_info in symbol_infos:
            self._symbols[symbol_info.name] = symbol_info

class PrivateSymbolTable(ScopedSymbolTable):
    """
    A write-through symbol table for storing private variables. Generated by a PRIVATE statement
    """
    def __init__(self, symbol_infos, procedure, parent):
        super(PrivateSymbolTable, self).__init__("PRIVATE symbols for %s" % procedure, SymbolTable.writethrough, parent)
        for symbol, type in symbol_types:
            self._symbols.update(symbol_types)

