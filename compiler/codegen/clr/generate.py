import re

import clr
import System
from System.Threading import Thread
from System.Reflection import *
from System.Reflection.Emit import *

from visitor import Visitor
from singleton import Singleton

from bbc_ast import DefinitionStatement, DefineProcedure, DefineFunction
from cil_visitor import CilVisitor, CodeGenerationError
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

class AssemblyGenerator(object):
    def __init__(self):
        self.owl_to_clr_method_names = {} # A map of OWL basic names to CLR names
        self.clr_to_owl_method_names = {} # A map of CLR names to OWL basic names
        self.method_builders = {}         # A map of CLR names to MethodBuilders
    
    def lookupMethod(self, clr_name):
        '''
        Lookup a MethodBuilder using is CLR name
        '''
        
        return self.method_builders[clr_name]
         
    def lookupCtsMethodName(self, owl_name):
        '''
        Lookup from an OWL identifier name (i.e. includes PROC or FN)
        '''
        return self.owl_to_clr_method_names[owl_name]
                   
    def generateAssembly(self, name, global_symbols, data_visitor, entry_points):
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
            self.generateStaticDataInitialization(data_visitor, type_builder)
        
        # Generate all the unique method names
        # TODO: This would be sooo much easier if the entry_point.name
        # property had been set useful, and PROC and FN retained in identifier names everywhere!
        # TODO: Should also wrap the main program in DEF PROCMain - safely!
        for name, entry_point in entry_points.items():
            if isinstance(entry_point, DefinitionStatement):
                self.createCtsMethodName(entry_point.name)   
            else: # Main
                assert name == '__owl__main'
                assert iter(entry_point.entryPoints).next().startswith('MAIN')
                self.createCtsMethodName('FNMain')    
        
        for owl_name, clr_name in self.owl_to_clr_method_names.items():
            print owl_name, " ==> ", clr_name
            
        # Generate all the empty methods, so we can retrieve them from the type builder    
        for entry_point in entry_points.values():
            self.generateMethod(type_builder, entry_point)
                
        # Generate the body of each method
        stop_on_error = False    
        for entry_point in entry_points.values():
            try:
                self.generateMethodBody(entry_point)
            except CodeGenerationError, e:
                print "STOPPING", e
                if stop_on_error:
                    break
            
        result = type_builder.CreateType()    
        assembly_builder.Save(name + ".exe")
            
    def generateStaticDataInitialization(self, data_visitor, type_builder):
        """
        Generate a type constructor to setup static data for DATA statements
        """
        # static (type) constructor - initialise static DATA
        
        
        # TODO: Replace this with Dictionary<int, int>
        
        self.data_field = type_builder.DefineField('data', cts.string_array_type,
                                                      FieldAttributes.Private | FieldAttributes.Static)
        self.data_line_number_map_field = type_builder.DefineField('dataLineNumbers', cts.int_int_dictionary_type,
                                                      FieldAttributes.Private | FieldAttributes.Static)
        self.data_index_field = type_builder.DefineField('dataIndex', clr.GetClrType(System.Int32),
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
        generator.Emit(OpCodes.Stsfld, self.data_field) # Store it in the static field
        
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
        generator.Emit(OpCodes.Stsfld, self.data_line_number_map_field)  # Store it in the static field
    
    def createCtsMethodName(self, owl_name):
        '''
        Given an entry point node devise a suitable name. Some names are reserved
        and names will be converted to valid CLR method identifiers.
        
        'Main' is reserved so will not be permitted.
        consecutive underscores will be removed
        leading @ will be removed
        The leading PROC or FN will be removed if names clash
        '''
        m = re.match(r'(PROC|FN)([a-zA-Z_0-9`@]+)', owl_name)
        assert m is not None
        owl_prefix = m.group(1)
        identifier = m.group(2)
        # TODO Remove initial digits
        # TODO: Deal with Main - and prior registration of that name, correctly
        identifier = re.sub(r'[@`]', '_', identifier)  # Replace @ and ` with underscores
        identifier = re.sub(r'_{2,}', '_', identifier) # Replace consecutive underscores with one
        # Remove the leading underscore
        if identifier.startswith('_'):
            if len(identifier == 1):
                identifier = 'Unnamed'
            else:
                identifier = identifier [1:]
        # Attempt to insert the identifier
        counter = None
        while True:
            if identifier not in self.clr_to_owl_method_names:
                self.owl_to_clr_method_names[owl_name] = identifier
                self.clr_to_owl_method_names[identifier] = owl_name
                break
            else:
                # Generated name already used
                clashing_owl_name = self.clr_to_owl_method_names[identifier]
                print "clashing_owl_name = ", clashing_owl_name
                # Attempt to resolve by prefixing with Proc or Fn
                # TODO: In future could consider simply overloading so
                #       long as the signatures are different
                print "owl_prefix = ", owl_prefix
                if owl_prefix == 'FN':
                    if clashing_owl_name.startswith('PROC'):
                        # Prefix the clashing identifier with 'Proc' and
                        # prefix this new identifier with 'Fn'
                        
                        # Modify the clasing entry by prefixing with 'Proc'
                        self.owl_to_clr_method_names[clashing_owl_name] = 'Proc' + identifier
                        self.clr_to_owl_method_names['Proc' + identifier] = clashing_owl_name
                        # Remove the old entry
                        del self.clr_to_owl_method_names[identifier]
                        # Add the new entry
                        identifier = 'Fn' + identifier
                        self.clr_to_owl_method_names[identifier] = owl_name
                        self.owl_to_clr_method_names[owl_name] = identifier
                        break
                    elif clashing_owl_name.startswith('FN'):
                        # Modify our name in some way to distinguish it
                        identifier = self.modifyName(identifier)
                        # TODO
                elif owl_prefix == 'PROC':
                    if clashing_owl_name.startswith('FN'):
                        # Prefix the clashing identifier with 'Fn' and
                        # prefix this new identifier with 'Proc'
                        self.owl_to_clr_method_names[clashing_owl_name] = 'Fn' + identifier
                        self.clr_to_owl_method_names['Fn' + identifier] = clashing_owl_name
                        # Remove the old entry
                        del self.clr_to_owl_method_names[identifier]
                        # Add the new entry
                        identifier = 'Proc' + identifier
                        self.clr_to_owl_method_names[identifier] = owl_name
                        self.owl_to_clr_method_names[owl_name] = identifier
                        break
                    elif clashing_owl_name.startswith('PROC'):
                        # Modify our name in some way to distinguish it
                        identifier = self.modifyName(identifier)
                        #TODO
        return identifier
                        
    def modifyName(self, identifier):
        '''
        Modify the given identifier into a new identifier which should be
        unique in the set of known identifiers
        '''
        raise NotImplementedException;
                                
    def generateMethod(self, type_builder, entry_point_node):
        """
        Generate the code for a single method starting a the entry_point node in the CFG
        """
    
        # Set up the method attributes
        method_attributes = MethodAttributes.Static
        method_return_type = None
        
        if isinstance(entry_point_node, DefinitionStatement):
            method_attributes |= MethodAttributes.Public
            method_parameters = self.methodParameters(entry_point_node)
            method_name = self.lookupCtsMethodName(entry_point_node.name)
            if isinstance (entry_point_node, DefineProcedure):
                method_return_type = System.Void
            elif isinstance (entry_point_node, DefineFunction):
                method_return_type = clr.GetClrType(System.Int32) # TODO just default to int for now
            assert(len(entry_point_node.outEdges) == 1)
            first_node = entry_point_node.outEdges[0]        
        else:
            assert iter(entry_point_node.entryPoints).next().startswith('MAIN')
            method_name = self.lookupCtsMethodName('FNMain')
            entry_point_node.name = method_name
            method_attributes |= MethodAttributes.Public
            method_return_type = clr.GetClrType(System.Int32)
            method_parameters = System.Array[System.Type]( (cts.string_array_type,) )
            first_node = entry_point_node
            
        print "generating method_name = ", method_name    
        self.method_builders[method_name] = type_builder.DefineMethod(method_name, method_attributes, CallingConventions.Standard,
                                                      method_return_type, method_parameters ) 
    
    def methodParameters(self, statement):
        '''
        Convert the formalParameters property of the supplied
        DefinitionStatement into an Array[Type]
        
        :param statement: A DefintionStatement
        :returns: An Array[Type] containing CTS types
        '''
        # TODO: Reference and out parameters not dealt with here!
        assert isinstance(statement, DefinitionStatement)
        print statement.formalParameters
        types = ()
        if statement.formalParameters is not None:
            formal_parameters = statement.formalParameters.arguments
            types = [cts.mapType(param.argument.actualType) for param in formal_parameters]
        return System.Array[System.Type](types)
    
    def generateMethodBody(self, entry_point_node):
        try:
            name = entry_point_node.name
            if name == 'Main':
                name = 'FNMain'
            clr_method_name = self.owl_to_clr_method_names[name]
        except KeyError:
            print entry_point_node.name
            print self.owl_to_clr_method_names
            assert 0
        print "Creating CIL for", clr_method_name
        method_builder = self.method_builders[clr_method_name]
        print "entry_point_node = ", entry_point_node
        cv = CilVisitor(self, method_builder, entry_point_node)

        

  
     