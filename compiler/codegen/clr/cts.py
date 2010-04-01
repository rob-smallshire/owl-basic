'''
Functions for dealing with the .NET Common Type System
'''

import clr
import System

from typing.type_system import (VoidOwlType, IntegerOwlType, FloatOwlType, StringOwlType,
                                ByteOwlType, ObjectOwlType)

# A basic mapping of OWL BASIC types to CTS types
type_map = { VoidOwlType()    : System.Void,
             IntegerOwlType() : System.Int32,
             FloatOwlType()   : System.Double,
             StringOwlType()  : System.String,
             ByteOwlType()    : System.Byte,
             ObjectOwlType()  : System.Object }

# Some useful .NET types
string_array_type = clr.GetClrType(System.String).MakeArrayType()
generic_dictionary_type = clr.GetClrType(System.Collections.Generic.Dictionary)
int_int_dictionary_type = generic_dictionary_type.MakeGenericType(
                           System.Array[System.Type]((clr.GetClrType(System.Int32), clr.GetClrType(System.Int32))))

print

def typeof(t):
    'Simulate C# typeof operator'
    return clr.GetClrType(t)

def mapType(basic_type):
    '''
    Map an OWL BASIC type to its equivalent CTS type
    :param basic_type: A BASIC Type
    '''
    return typeof(type_map[basic_type])

def symbolType(symbol):
    '''
    Given a symbol return its CTS type
    :param symbol: A SymbolInfo instance
    :returns: A System.Type
    '''
    t = symbol.type
    if t.isArray():
        # TODO: Rank of array is important here
        assert symbol.rank > 0
        element_type = typeof(type_map[t.elementType()])
        return element_type.MakeArrayType(symbol.rank)
    return typeof(type_map[t])

    