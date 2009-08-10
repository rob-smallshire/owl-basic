'''
Created on 10 Aug 2009

@author: rjs
'''

import clr
import System
from System.Reflection import *
from System.Reflection.Emit import *

from visitor import Visitor
from bbc_ast import *
import cts

class CilVisitor(Visitor):
    '''
    Emit CIL bytecode whilst traversing the AST/CFG
    '''


    def __init__(self, type_builder, entry_point_node):
        '''
        Create a new CilVisitor for generating a CIL method.
        
        :param type_builder A System.Reflection.Emit.TypeBuilder
        :param entry_point_node The entry point CFG node of a method
        '''
        assert(len(entry_point_node.entryPoints) == 1)
        
        method_attributes = MethodAttributes.Static
        method_return_type = None
        #print "basic_name = ", basic_name
        # TODO: Look at using a visitor here
        if isinstance(entry_point_node, DefinitionStatement):
            method_name = entry_point_node.name
            method_attributes |= MethodAttributes.Public
            method_parameters = self.methodParameters(entry_point_node)
            if isinstance (entry_point_node, DefineProcedure):
                method_return_type = System.Void
            elif isinstance (entry_point_node, DefineFunction):
                method_return_type = clr.GetClrType(System.Int32) # TODO just default to int for now
            assert(len(entry_point_node.outEdges) == 1)
            first_node = entry_point_node.outEdges[0]        
        else:
            assert iter(entry_point_node.entryPoints).next().startswith('MAIN')
            method_name = 'Main'
            method_attributes |= MethodAttributes.Public
            method_return_type = clr.GetClrType(System.Int32)
            method_parameters = System.Array[System.Type]( (cts.string_array_type,) )
            first_node = entry_point_node
            
        print "generating method_name = ", method_name    
        self.method_builder = type_builder.DefineMethod(method_name, method_attributes, CallingConventions.Standard,
                                                   method_return_type, method_parameters ) 
        
        self.generator = self.method_builder.GetILGenerator()
        self.generator.Emit(OpCodes.Nop) # Every method needs at least one OpCode
        
        # Get the outgoing node, and visit it
        first_node.accept(self)
    
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
        
    def visitAstStatement(self, node):
        print "Visiting ", node
        
    def visitData(self, data):
        # TODO: Find a way to do this without accumulating the stack
        print "Visiting ", data
        assert(len(data.outEdges) == 1)
        next_node = data.outEdges[0]
        next_node.accept(self)
        
    def visitAssignment(self, assignment):
        print "Visiting ", assignment
        
        
    
        