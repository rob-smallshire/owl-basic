import clr
import System
from System.Threading import Thread
from System.Reflection import *
from System.Reflection.Emit import *

from visitor import Visitor
from singleton import Singleton

from cil_visitor import CilVisitor
import cts

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
        field_builder = type_builder.DefineField(ctsIdentifier(symbol), cts.symbolType(symbol),
                                                 FieldAttributes.Private | FieldAttributes.Static)
        symbol.realization = field_builder
    
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
    
    data_field = type_builder.DefineField('data', cts.string_array_type,
                                                  FieldAttributes.Private | FieldAttributes.Static)
    data_line_number_map_field = type_builder.DefineField('dataLineNumbers', cts.int_int_dictionary_type,
                                                  FieldAttributes.Private | FieldAttributes.Static)
    data_line_number_index_field = type_builder.DefineField('dataIndex', clr.GetClrType(System.Int32),
                                                            FieldAttributes.Private | FieldAttributes.Static)
    
    type_constructor_builder = type_builder.DefineTypeInitializer()
    generator = type_constructor_builder.GetILGenerator()
    generator.DeclareLocal(cts.string_array_type)
    generator.DeclareLocal(cts.int_int_dictionary_type)
    
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
    #generic_dictionary_type = clr.GetClrType(System.Collections.Generic.Dictionary)
    #int_int_dictionary_type = generic_dictionary_type.MakeGenericType(
    #                       System.Array[System.Type]((clr.GetClrType(System.Int32), clr.GetClrType(System.Int32))))

    int_int_dictionary_ctor_info = cts.int_int_dictionary_type.GetConstructor(System.Type.EmptyTypes) # Get the default constructor
    generator.Emit(OpCodes.Newobj, int_int_dictionary_ctor_info)
    generator.Emit(OpCodes.Stloc_1) # Store array reference in local 1
    
    add_method_info = cts.int_int_dictionary_type.GetMethod('Add')
    
    for line_number, index in data_visitor.index.items():
        generator.Emit(OpCodes.Ldloc_1)               # Load the dictionary onto the stack
        generator.Emit(OpCodes.Ldc_I4, line_number)   # Load the line_number onto the stack
        generator.Emit(OpCodes.Ldc_I4, index)         # Load the index onto the stack
        generator.Emit(OpCodes.Call, add_method_info) # Call Dictionary<int,int>.Add()
        
    generator.Emit(OpCodes.Ldloc_1)                   # Load the dictionary onto the stack
    generator.Emit(OpCodes.Stsfld, data_line_number_map_field)  # Store it in the static field
         
def generateMethod(type_builder, entry_point_node):
    """
    Generate the code for a single method starting a the entry_point node in the CFG
    """

    # Traverse the CFG from the entry point, generating code as we co
    cv = CilVisitor(type_builder, entry_point_node)
    #entry_point.accept(gcv)
    

  
     