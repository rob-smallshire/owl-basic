'''
Functions for dealing with the .NET Common Type System
'''

import clr
import System

import bbc_types

# A basic mapping of OWL BASIC types to CTS types
type_map = { bbc_types.VoidType    : System.Void,
             bbc_types.IntegerType : System.Int32,
             bbc_types.FloatType   : System.Double,
             bbc_types.StringType  : System.String,
             bbc_types.ByteType    : System.Byte,
             bbc_types.ObjectType  : System.Object }

# Some useful .NET types
string_array_type = clr.GetClrType(System.String).MakeArrayType()
generic_dictionary_type = clr.GetClrType(System.Collections.Generic.Dictionary)
int_int_dictionary_type = generic_dictionary_type.MakeGenericType(
                           System.Array[System.Type]((clr.GetClrType(System.Int32), clr.GetClrType(System.Int32))))

print

def mapType(basic_type):
    '''
    Map an OWL BASIC type to its equivalent CTS type
    :param basic_type: A BASIC Type
    '''
    return clr.GetClrType(type_map[basic_type])

def symbolType(symbol):
    '''
    Given a symbol return its CTS type
    :param symbol: A SymbolInfo instance
    :returns: A System.Type
    '''
    t = symbol.type
    if t.isA(bbc_types.ArrayType):
        element_type = t._getElementType()
        ctsBasicType(element_type).MakeArrayType(symbol.rank)
    return clr.GetClrType(type_map[t])

    