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

# Load the OWL Runtime library so we may both call and reference
# methods within it
clr.AddReferenceToFileAndPath(r'C:\Users\rjs\Documents\dev\p4smallshire\sandbox\bbc_sharp_basic\OwlRuntime\OwlRuntime\bin\Debug\OwlRuntime.dll')
import OwlRuntime

class CilVisitor(Visitor):
    '''
    Emit CIL bytecode whilst traversing the AST/CFG
    '''


    def __init__(self, assembly_generator, method_builder, entry_point_node):
        '''
        Create a new CilVisitor for generating a CIL method.
        
        :param type_builder A System.Reflection.Emit.TypeBuilder
        :param entry_point_node The entry point CFG node of a method
        '''
        assert(len(entry_point_node.entryPoints) == 1)
        self.assembly_generator = assembly_generator
        self.method_builder = method_builder
        
        # Get the type of OwnRuntime.BasicCommand so we can retrieve methods
        self.basic_commands_type = clr.GetClrType(OwlRuntime.BasicCommands)
        
        self.generator = self.method_builder.GetILGenerator()
        self.generator.Emit(OpCodes.Nop) # Every method needs at least one OpCode
                
        node = self.successorOf(entry_point_node)
        while True:
            node = node.accept(self)
            if node is None:
                break
            
        if isinstance(entry_point_node, DefineFunction):
            self.generator.Emit(OpCodes.Ldc_I4, 0)
            self.generator.Emit(OpCodes.Ret) # Functions must return something
    
    def lookupMethod(self, name):
        '''
        Return a MethodInfo object for the named PROC or FN
        using the OWL name, e.g. 'PROCfoo'
        '''
        cts_name = self.assembly_generator.lookupCtsMethodName(name)
        return self.assembly_generator.lookupMethod(cts_name)
        
    
    def basicCommandMethod(self, name):
        '''
        Return a MethodInfo object for the named method of OwlRuntime.BasicCommands
        '''
        return self.basic_commands_type.GetMethod(name)
    
    def visit(self, item):
        print "Visiting unhandled node", node
        print "STOPPING"
        assert 0
            
    def visitAstStatement(self, node):
        print "Visiting unhandled statement", node
        print "STOPPING"
        return None
        
    def visitData(self, data):
        return self.successorOf(data)
        
    def successorOf(self, node):
        assert(len(node.outEdges) <= 1)
        if len(node.outEdges) == 0:
            return None
        return node.outEdges[0]
        
    def visitAssignment(self, assignment):
        print "Visiting ", assignment
        # TODO: If the lhs is not a simple variable, stop.
        print type(assignment.lValue)
        assert isinstance(assignment.lValue, Variable)
        print "Assigning to variable"
        # Evaluate the expression on the right hand side
        print type(assignment.rValue)
        assignment.rValue.accept(self)
        # Assign to the variable on the left hand side
        #  Lookup in the symbol table
        name = assignment.lValue.identifier
        print name
        symbol = assignment.symbolTable.lookup(name)
        assert symbol is not None
        print repr(symbol)
        assert symbol.realization is not None
        print repr(symbol.realization)
        if isinstance(symbol.realization, FieldBuilder):
            self.generator.Emit(OpCodes.Stsfld, symbol.realization)
        else:
            print clt.GetClrType(symbol.realization)
            assert "Unknown symbol.realization type"
        return self.successorOf(assignment)
        
    def visitLiteralString(self, literal_string):
        print "Visiting ", literal_string
        print "value = ", literal_string.value
        self.generator.Emit(OpCodes.Ldstr, literal_string.value)
        
    def visitCast(self, cast):
        print "Visiting ", cast
        print "sourceType = ", cast.sourceType
        print "targetType = ", cast.targetType
        print "value      = ", cast.value
        # Get the value onto the stack
        cast.value.accept(self)
        # Convert - Int32 can be exactly converted to Double
        if cast.sourceType is IntegerType:
            if cast.targetType is FloatType:
                self.generator.Emit(OpCodes.Conv_R8)
                return
        print "Unsupported cast"
                
    def visitLiteralInteger(self, literal_integer):
        print "Visiting ", literal_integer
        print "value = ", literal_integer.value
        # TODO: Optimization with shorter OpCodes
        self.generator.Emit(OpCodes.Ldc_I4, literal_integer.value)
    
    def visitVdu(self, vdu):
        print "Visiting ", vdu
        print "bytes = ", vdu.bytes
        assert hasattr(vdu.bytes, '__getitem__')
        assert hasattr(vdu.bytes, '__len__')
        if len(vdu.bytes) == 1:
            vdu_item = vdu.bytes[0]
            vdu_item.item.accept(self)
            if vdu_item.length == 1 or vdu_item.length == 9:
                self.generator.Emit(OpCodes.Conv_I1)
            elif vdu_item.length == 2:
                self.generator.Emit(OpCodes.Conv_I2)
            self.generator.Emit(OpCodes.Call, self.basicCommandMethod('Vdu'))
            if vdu_item.length == 9:
                self.generator.Emit(OpCodes.Call, self.basicCommandMethod('VduFlush'))    
        else:
            # VDU with multiple items, e.g. VDU 23, 232, 23, 12 ...
            # TODO: Avoid multiple VDU calls
            print "Unhandled"
            return None
        return self.successorOf(vdu)
                  
    def visitCallProcedure(self, call_proc):
        print "Visiting ", call_proc
        print "name = ", call_proc.name
        # TODO: Push the procedure call arguments onto the stack
        print "actual_parameters = ", call_proc.actualParameters
        for actual_parameter in call_proc.actualParameters:
            print "Actual parameters are unhandled"
            return None
        # TODO: Call the procedure
        proc_method_info = self.lookupMethod(call_proc.name)
        print proc_method_info
        self.generator.Emit(OpCodes.Call, proc_method_info)
        return self.successorOf(call_proc)
        
        
        