import bbc_types
from visitor import Visitor
from singleton import Singleton
from bbc_ast import *

import clr
clr.AddReference("System")
import System
from System import Type, Array, String
from System.Threading import Thread
from System.Reflection import *
from System.Reflection.Emit import *


type_map = { bbc_types.VoidType    : 'System.Void',
             bbc_types.IntegerType : 'System.Int32',
             bbc_types.FloatType   : 'System.Double',
             bbc_types.StringType  : 'System.String',
             bbc_types.ByteType    : 'System.Byte',
             bbc_types.ObjectType  : 'System.Object'
            }

# Some useful .NET types
string_array_type = clr.GetClrType(System.String).MakeArrayType(1)
generic_dictionary_type = clr.GetClrType(System.Collections.Generic.Dictionary)
int_int_dictionary_type = generic_dictionary_type.MakeGenericType(
                           Array[Type]((clr.GetClrType(System.Int32), clr.GetClrType(System.Int32))))


def ctsBasicType(t):
    return Type.GetType(type_map[t])
        
def ctsType(symbol):
    """
    A mapping from BASIC symbol types to .NET types
    """
    # TODO: Rename to ctsSymbolType
    t = symbol.type
    if t.isA(bbc_types.ArrayType):
        element_type = t._getElementType()
        ctsBasicType(element_type).MakeArrayType(symbol.rank)
    return ctsBasicType(t)

def ctsIdentifier(symbol):
    """
    A mapping from BASIC names with sigils to .NET compliant name
    using Systems Hungarian notation
    """
    name = symbol.name
    if name.endswith('$'):
        return 's' + symbol.name[:-1]
    if name.endswith('%'):
        return 'i' + symbol.name[:-1]
    # TODO: May need additions to deal with arrays
    return 'f' + symbol.name
            
def generateAssembly(name, global_symbols, data_visitor, entry_point_visitor):
    """
    name - the name given to the assembly to be generated
    """
    # Generate an assembly
    # Generate a namespace
    # Generate a static class
    # Create global variables as members
    # For each entry point
    #  - create a method
    # Mark the entry point to the assembly
    
    
    # We build the assembly in the current AppDomain
    domain = Thread.GetDomain()
    assembly_name = AssemblyName(name)
    assembly_builder = domain.DefineDynamicAssembly(assembly_name, AssemblyBuilderAccess.RunAndSave)
    
    module_builder = assembly_builder.DefineDynamicModule(name + ".exe")
    type_builder = module_builder.DefineType(name, TypeAttributes.Class | TypeAttributes.Public, object().GetType())
    
    # Add global variables to the class
    for symbol in global_symbols.symbols.values():
        field_builder = type_builder.DefineField(ctsIdentifier(symbol), ctsType(symbol),
                                                 FieldAttributes.Private | FieldAttributes.Static)
    
    if len(data_visitor.data) > 0:
        generateStaticDataInitialization(data_visitor, type_builder)
        
    for entry_point in entry_point_visitor.entry_points:
        generateMethod(type_builder, entry_point)
        
    result = type_builder.CreateType()    
    assembly_builder.Save(name + ".exe")
        
def generateStaticDataInitialization(data_visitor, type_builder):
    """
    Generate a type constructor to setup static data for DATA statements
    """
    # static (type) constructor - initialise static DATA
    
    
    # TODO: Replace this with Dictionary<int, int>
    
    data_field = type_builder.DefineField('data', string_array_type,
                                                  FieldAttributes.Private | FieldAttributes.Static)
    data_line_number_map_field = type_builder.DefineField('dataLineNumbers', int_int_dictionary_type,
                                                  FieldAttributes.Private | FieldAttributes.Static)
    data_line_number_index_field = type_builder.DefineField('dataIndex', clr.GetClrType(System.Int32),
                                                            FieldAttributes.Private | FieldAttributes.Static)
    
    type_constructor_builder = type_builder.DefineTypeInitializer()
    generator = type_constructor_builder.GetILGenerator()
    generator.DeclareLocal(string_array_type)
    generator.DeclareLocal(int_int_dictionary_type)
    
    # Initialise the data field
    generator.Emit(OpCodes.Ldc_I4, len(data_visitor.data)) # Load the array length onto the stack
    generator.Emit(OpCodes.Newarr, System.String) # New array with type information
    generator.Emit(OpCodes.Stloc_0) # Store array reference in local 0
    for index, item in enumerate(data_visitor.data):
        generator.Emit(OpCodes.Ldloc_0)       # Load the array onto the stack
        generator.Emit(OpCodes.Ldc_I4, index) # Load the index onto the stack
        generator.Emit(OpCodes.Ldstr, item)   # Load the string onto the stack
        generator.Emit(OpCodes.Stelem_Ref)    # Assign to array element
    generator.Emit(OpCodes.Ldloc_0)            # Load the array onto the stack
    generator.Emit(OpCodes.Stsfld, data_field) # Store it in the static field
    
    # Initialise the data index field -
    # this needs to be initialized with a Dictionary
    int_int_dictionary_ctor_info = int_int_dictionary_type.GetConstructor(Array[Type](())) # Get the default constructor
    generator.Emit(OpCodes.Newobj, int_int_dictionary_ctor_info)
    generator.Emit(OpCodes.Stloc_1) # Store array reference in local 1
    
    add_method_info = int_int_dictionary_type.GetMethod('Add')
    
    for line_number, index in data_visitor.index.items():
        generator.Emit(OpCodes.Ldloc_1)               # Load the dictionary onto the stack
        generator.Emit(OpCodes.Ldc_I4, line_number)   # Load the line_number onto the stack
        generator.Emit(OpCodes.Ldc_I4, index)         # Load the index onto the stack
        generator.Emit(OpCodes.Call, add_method_info) # Call Dictionary<int,int>.Add()
        
    generator.Emit(OpCodes.Ldloc_1)                   # Load the dictionary onto the stack
    generator.Emit(OpCodes.Stsfld, data_line_number_map_field)  # Store it in the static field

def methodParameters(statement):
    '''
    Convert the formalParameters property of the supplied
    DefinitionStatement into an Array[Type]
    '''
    print "methodParameters for ", statement.name
    # TODO: Reference and out parameters not dealt with here!
    assert isinstance(statement, DefinitionStatement)
    print statement.formalParameters
    types = ()
    if statement.formalParameters is not None:
        formal_parameters = statement.formalParameters.arguments
        types = [ctsBasicType(param.argument.actualType) for param in formal_parameters]
    return Array[Type](types)
         
def generateMethod(type_builder, entry_point):
    """
    Generate the code for a single method starting a the entry_point node in the CFG
    """
    assert(len(entry_point.entryPoints) == 1)
    #basic_name = iter(entry_point.entryPoints).next() # The name used in OWL BASIC. eg. PROCfoo or FNbar
     # For now we keep the same.  Later we may want to use more .NET-ish names
                             # But we need to avoid collisions between FNfoo and PROCfoo
                             
    method_attributes = MethodAttributes.Static
    method_return_type = None
    #print "basic_name = ", basic_name
    # TODO: Look at using a visitor here
    if isinstance(entry_point, DefinitionStatement):
        method_name = entry_point.name
        method_attributes |= MethodAttributes.Public
        method_parameters = methodParameters(entry_point)
        if isinstance (entry_point, DefineProcedure):
            method_return_type = System.Void
        elif isinstance (entry_point, DefineProcedure):
            method_return_type = clr.GetClrType(System.Int32) # TODO just default to int for now        
    else:
        assert iter(entry_point.entryPoints).next().startswith('MAIN')
        method_name = 'Main'
        method_attributes |= MethodAttributes.Public
        method_return_type = clr.GetClrType(System.Int32)
        method_parameters = Array[Type]( (string_array_type,) )
        
    print "generating method_name = ", method_name    
    method_builder = type_builder.DefineMethod(method_name, method_attributes, CallingConventions.Standard,
                                               method_return_type, method_parameters ) 
    
    generator = method_builder.GetILGenerator()
    generator.Emit(OpCodes.Nop)
    
  
     