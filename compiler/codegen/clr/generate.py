import re
import logging
from functools import partial

import clr
import System
from System.Threading import Thread
from System.Reflection import *
from System.Reflection.Emit import *

from visitor import Visitor
from singleton import Singleton

from bbc_ast import DefinitionStatement, DefineProcedure, DefineFunction, Local
from ast_utils import findNode
from cil_visitor import CilVisitor, CodeGenerationError
from symbol_tables import hasSymbolTableLookup, StaticSymbolTable
from emitters import *
import cts
from algorithms import representative
from flow.traversal import depthFirstSearch

# Load the OWL Runtime library so we may both call and reference
# methods within it
clr.AddReferenceToFileAndPath(r'C:\Users\rjs\Documents\dev\p4smallshire\sandbox\bbc_sharp_basic\OwlRuntime\OwlRuntime\bin\Debug\OwlRuntime.dll')
import OwlRuntime

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
                   
    def generateAssembly(self, name, global_symbols, data_visitor, ordered_basic_blocks):
        """
        :param name: The name given to the assembly to be generated.
        :param ordered_basic_blocks: A mapping type where keys are the entry point name
                                     and values are a sequence of BasicBlocks for that method/program.
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
        owl_module = clr.GetClrType(OwlRuntime.OwlModule)
        type_builder = module_builder.DefineType(name,
                                                 TypeAttributes.Class | TypeAttributes.Public,
                                                 object().GetType())
        
        # Add accessors for the inherited static variables
        static_symbols = StaticSymbolTable.getInstance()
        for symbol in static_symbols.symbols.values():
            field_info = owl_module.GetField(ctsIdentifier(symbol))
            self.createAndAttachFieldEmitters(field_info, symbol)
            
        # Add global variables and their accessors to the class
        for symbol in global_symbols.symbols.values():
            field_builder = type_builder.DefineField(ctsIdentifier(symbol), cts.symbolType(symbol),
                                                     FieldAttributes.Private | FieldAttributes.Static)
            self.createAndAttachFieldEmitters(field_builder, symbol) 
        
        if len(data_visitor.data) > 0:
            self.generateStaticDataInitialization(data_visitor, type_builder)
        
        # Generate all the unique method names
        # TODO: This would be sooo much easier if the entry_point.name
        # property had been set useful, and PROC and FN retained in identifier names everywhere!
        # TODO: Should also wrap the main program in DEF PROCMain - safely!
        for entry_name, basic_blocks in ordered_basic_blocks.items():
            entry_point = basic_blocks[0].entryPoint
            if isinstance(entry_point, DefinitionStatement):
                self.createCtsMethodName(entry_point.name)   
            else: # Main
                assert entry_name == '__owl__main'
                assert iter(entry_point.entryPoints).next().startswith('MAIN')
                self.createCtsMethodName('FNMain')    
        
        #for owl_name, clr_name in self.owl_to_clr_method_names.items():
        #    print owl_name, " ==> ", clr_name
            
        # Generate all the empty methods, so we can retrieve them from the type builder    
        for basic_blocks in ordered_basic_blocks.values():
            self.generateMethod(type_builder, basic_blocks)
                
        # Generate the body of each method
        stop_on_error = False    
        for basic_blocks in ordered_basic_blocks.values():
            try:
                self.generateMethodBody(basic_blocks)
            except CodeGenerationError, e:
                logging.critical("STOPPING %s\n\n\n", e)
                if stop_on_error:
                    break
        
        if 'Main' in self.method_builders:
            logging.debug("Setting assembly entry point")
            assembly_builder.SetEntryPoint(self.method_builders['Main'])
        
        result = type_builder.CreateType()
        name += ".exe"    
        logging.debug("Creating %s", name)
        assembly_builder.Save(name)
    
    def createAndAttachFieldEmitters(self, field_info, symbol):
        '''
        Generate a two methods for generating CIL to load and store the value of the global variable (field)
        :param generator: A CIL generator
        :param field_info: The FieldInfo metadata
        :param symbol: The symbol to which fieldStoreEmitter and fieldLoadEmitter methods will be attached
        ''' 
        def fieldLoadEmitter(generator, field_info=field_info):
            '''
            A closure which emits CIL into the supplied generator to load a field
            :param generator: A CIL generator
            :param field_info: The FieldInfo metadata
            '''
            generator.Emit(OpCodes.Ldsfld, field_info)
            
        def fieldStoreEmitter(generator, field_info=field_info):
            '''
            A closure which emits CIL into the supplied generator to store a field
            :param generator: A CIL generator
            :param field_info: The FieldInfo metadata
            '''
            generator.Emit(OpCodes.Stsfld, field_info)
        
        symbol.loadEmitter = fieldLoadEmitter
        symbol.storeEmitter = fieldStoreEmitter
            
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
        data_local = generator.DeclareLocal(cts.string_array_type)
        data_index_local = generator.DeclareLocal(cts.int_int_dictionary_type)
        
        # Initialise the data field
        emitLdc_I4(generator, len(data_visitor.data)) # Load the array length onto the stack
        generator.Emit(OpCodes.Newarr, System.String) # New array with type information
        generator.Emit(OpCodes.Stloc, data_local) # Store array reference in local 0
        for index, item in enumerate(data_visitor.data):
            generator.Emit(OpCodes.Ldloc, data_local)       # Load the array onto the stack
            emitLdc_I4(generator, index)          # Load the index onto the stack
            generator.Emit(OpCodes.Ldstr, item)   # Load the string onto the stack
            generator.Emit(OpCodes.Stelem_Ref)    # Assign to array element
        generator.Emit(OpCodes.Ldloc, data_local)            # Load the array onto the stack
        generator.Emit(OpCodes.Stsfld, self.data_field) # Store it in the static field
        
        # Initialise the data index field -
        # this needs to be initialized with a Dictionary
        #generic_dictionary_type = clr.GetClrType(System.Collections.Generic.Dictionary)
        #int_int_dictionary_type = generic_dictionary_type.MakeGenericType(
        #                       System.Array[System.Type]((clr.GetClrType(System.Int32), clr.GetClrType(System.Int32))))
    
        int_int_dictionary_ctor_info = cts.int_int_dictionary_type.GetConstructor(System.Type.EmptyTypes) # Get the default constructor
        generator.Emit(OpCodes.Newobj, int_int_dictionary_ctor_info)
        generator.Emit(OpCodes.Stloc, data_index_local) # Store dictionary reference in local 1
        
        add_method_info = cts.int_int_dictionary_type.GetMethod('Add')
        
        for line_number, index in data_visitor.index.items():
            generator.Emit(OpCodes.Ldloc, data_index_local)   # Load the dictionary onto the stack
            emitLdc_I4(generator, line_number)                # Load the line_number onto the stack
            emitLdc_I4(generator, index)                      # Load the index onto the stack
            generator.Emit(OpCodes.Call, add_method_info)     # Call Dictionary<int,int>.Add()
            
        generator.Emit(OpCodes.Ldloc, data_index_local)       # Load the dictionary onto the stack
        generator.Emit(OpCodes.Stsfld, self.data_line_number_map_field)  # Store it in the static field
        generator.Emit(OpCodes.Ret)
    
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
                logging.debug("clashing_owl_name = %s", clashing_owl_name)
                # Attempt to resolve by prefixing with Proc or Fn
                # TODO: In future could consider simply overloading so
                #       long as the signatures are different
                logging.debug("owl_prefix = %s", owl_prefix)
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
                                
    def generateMethod(self, type_builder, basic_blocks):
        """
        Generate the code for a single method starting a the entry_point node in the CFG. Attaches
        code generation functionality to the symbols representing the formal parameters of the method.
        """
        logging.debug("generateMethod")

        # The first statement of the first basic block is the entry point
        entry_point_node = basic_blocks[0].entryPoint

        # Set up the method attributes
        method_attributes = MethodAttributes.Static
        method_return_type = None
        
        if isinstance(entry_point_node, DefinitionStatement):
            method_name, method_return_type, method_attributes, method_parameters = self.generateDefinedMethod(entry_point_node, method_attributes)     
        else:
            method_name, method_return_type, method_attributes, method_parameters = self.generateMainProgram(entry_point_node, method_attributes)
            
        logging.debug("generating method %s with type %s", method_name, method_return_type)
        self.method_builders[method_name] = type_builder.DefineMethod(method_name, method_attributes, CallingConventions.Standard,
                                                      method_return_type, method_parameters ) 

    def generateDefinedMethod(self, entry_point_node, method_attributes):
        method_attributes |= MethodAttributes.Public
        method_parameters = self.methodParameters(entry_point_node)
        method_name = self.lookupCtsMethodName(entry_point_node.name)
        logging.debug("name = %s", entry_point_node.name)
        # Setup code generators for loading and storing the methods arguments
        if entry_point_node.formalParameters is not None:
            formal_parameters = entry_point_node.formalParameters.arguments
            for index, param in enumerate(formal_parameters):
            # TODO: Lookup the argument symbol
                name = param.argument.identifier
                logging.debug("formal parameter identifier = %s", name)
                symbol_node = findNode(entry_point_node, hasSymbolTableLookup)
                arg_symbol = symbol_node.symbolTable.lookup(name)
                assert arg_symbol is not None
                arg_symbol.loadEmitter  = partial(emitLdarg, index=index)
                arg_symbol.storeEmitter = partial(emitStarg, index=index)
                # Setup the return type of the method
            
        if isinstance(entry_point_node, DefineProcedure):
            method_return_type = System.Void
        elif isinstance(entry_point_node, DefineFunction):
            method_return_type = cts.mapType(entry_point_node.returnType)
        
        return method_name, method_return_type, method_attributes, method_parameters
    
    def generateMainProgram(self, entry_point_node, method_attributes):
        assert iter(entry_point_node.entryPoints).next().startswith('MAIN')
        method_name = self.lookupCtsMethodName('FNMain')
        entry_point_node.name = method_name
        method_attributes |= MethodAttributes.Public
        # TODO: Parameters and returns from Main
        method_return_type = None
        method_parameters = None
        return method_name, method_return_type, method_attributes, method_parameters
    
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
    
    def generateMethodBody(self, basic_blocks):
        # The first statement of the first basic block is the entry point
        entry_point_node = basic_blocks[0].entryPoint
        try:
            name = entry_point_node.name
            if name == 'Main':
                name = 'FNMain'
            clr_method_name = self.owl_to_clr_method_names[name]
        except KeyError:
            print entry_point_node.name
            print self.owl_to_clr_method_names
            assert 0
        logging.debug("Creating CIL for %s", clr_method_name)
        method_builder = self.method_builders[clr_method_name]
        logging.debug("entry_point_node = %s", entry_point_node)

        # Create the visitor which holds the code generator 
        cv = CilVisitor(self, method_builder)
        
        # Declare LOCAL variables and attach load and store emitters to the symbols
        for node in depthFirstSearch(entry_point_node):
            if isinstance(node, Local):
                symbol_table = node.symbolTable
                for symbol in symbol_table.symbols.values():
                    local_builder = cv.generator.DeclareLocal(cts.symbolType(symbol))
                    self.createAndAttachLocalEmitters(local_builder, symbol)
        
        # TODO: Declare PRIVATE variables and attach load and store emitters to the symbols
        
        # For each basic block (including the first, if it has an in-degree > 1)
        # define a label, and attach it to the block
        for basic_block in basic_blocks:
            basic_block.label = cv.generator.DefineLabel()
            basic_block.is_label_marked = False

        # Generate the code for blocks and statements in sequence
        for basic_block in basic_blocks:
            for statement in basic_block.statements:
                cv.visit(statement)
                assert statement.block.is_label_marked
            self.transferControlToNextBlock(cv.generator, basic_block)
        logging.debug("COMPLETE\n\n\n")
        
    def createAndAttachLocalEmitters(self, local_builder, symbol):
        '''
        Generate a two methods for generating CIL to load and store the value of the global variable (field)
        :param generator: A CIL generator
        :param local_builder: The LocalBuilder metadata
        :param symbol: The symbol to which localStoreEmitter and localLoadEmitter methods will be attached
        ''' 
        def localLoadEmitter(generator, local_builder=local_builder):
            '''
            A closure which emits CIL into the supplied generator to load a field
            :param generator: A CIL generator
            :param local_builder: The LocalBuilder metadata
            '''
            generator.Emit(OpCodes.Ldloc, local_builder)
            
        def localStoreEmitter(generator, local_builder=local_builder):
            '''
            A closure which emits CIL into the supplied generator to store a field
            :param generator: A CIL generator
            :param local_builder: The LocalBuilder metadata
            '''
            generator.Emit(OpCodes.Stloc, local_builder)
        
        symbol.loadEmitter = localLoadEmitter
        symbol.storeEmitter = localStoreEmitter
        
    def transferControlToNextBlock(self, generator, current_block):
        '''
        Transfer control to the next block for blocks with
        an out-degree of one.  (More complex block exits should
        already have been dealt with by code generation of the
        last statement of the block). If control can fall through
        to the next block because they are consecutive in the topological
        order no code is generated, otherwise an unconditional branch is inserted.
        :param generator: A code generator.
        :param current_block: The block from which to transfer control.
        '''
        
        if current_block.outDegree == 1:
            successor_block = representative(current_block.outEdges)
            # If we can't fall through to the next block, branch unconditionally to it
            if successor_block.topological_order != current_block.topological_order + 1:
                generator.Emit(OpCodes.Br, successor_block.label)
                
                           