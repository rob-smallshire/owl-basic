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
    
    def visit(self, node):
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
        
    def visitRestore(self, restore):
        # TODO: Can we RESTORE to lines which don't contain DATA?
        print "Visiting ", restore
        print "target_logical_line = ", restore.targetLogicalLine
        # Lookup the data pointer value for this line number
        self.generator.Emit(OpCodes.Ldsfld, self.assembly_generator.data_line_number_map_field)         # Load the dictionary onto the stack
        restore.targetLogicalLine.accept(self) # Push the line number onto the stack
        get_item_method_info = cts.int_int_dictionary_type.GetMethod('get_Item')
        self.generator.Emit(OpCodes.Call, get_item_method_info) # Call get_Item and the put the new data point result on the stack
        self.generator.Emit(OpCodes.Stsfld, self.assembly_generator.data_index_field)
        return self.successorOf(restore)
        
    def visitForToStep(self, for_to_step):
        # TODO: Future optimizations
        # - if STEP is a constant we can simplify the test depending on its sign
        # - if the values are ints we can convert the type of the counter to an int
        # - if last is a constant its worth convert <= last into < last + 1 or the
        #   reverse, if we know the sign of step
        
        # TODO: Could probably hit most common cases STEP == +1 with completely different
        #       code gen FOR i% = 0 TO 9
        
        print "Visiting ", for_to_step

        # Load the initial counter value onto the stack
        for_to_step.first.accept(self)

        # Store in the loop counter variable
        name = for_to_step.identifier.identifier
        print name
        symbol = for_to_step.symbolTable.lookup(name)
        assert symbol is not None
        print repr(symbol)
        assert symbol.realization is not None
        print repr(symbol.realization)
        if isinstance(symbol.realization, FieldBuilder):
            self.generator.Emit(OpCodes.Stsfld, symbol.realization)
        else:
            print clt.GetClrType(symbol.realization)
            assert "Unknown symbol.realization type"
        
        # Evaluate the last value and store in an unnamed local
        last_value_local = self.generator.DeclareLocal(cts.symbolType(symbol))
        for_to_step.last.accept(self)
        self.generator.Emit(OpCodes.Stloc, last_value_local)
        
        # Evaluate the step value and store in an unnamed local
        step_value_local = self.generator.DeclareLocal(cts.symbolType(symbol))
        for_to_step.step.accept(self)
        self.generator.Emit(OpCodes.Stloc, step_value_local)
                        
        # The loop body goes in here - later, but first...
        loop_body_label = self.generator.DefineLabel()
        
        # Define a function (closure) which can be called later to generate
        # the code for the corresponding NEXT statements
        def correspondingNext():
            # Increment the counter
            self.generator.Emit(OpCodes.Ldloc, step_value_local) # Load the STEP value
            self.generator.Emit(OpCodes.Ldsfld, symbol.realization) # Load the counter
            self.generator.Emit(Add)
            self.generator.Emit(OpCodes.Stsfld, symbol.realization) # Store the counter
            
            # Check the sign of the step value
            self.generator.Emit(OpCodes.Ldloc, step_value_local) # Load the STEP value
            self.generator.Emit(OpCodes.Ldc_I4_0)                # Push zero on the stack
            
            positive_step_label = self.generator.DefineLabel()   
            self.generator.Emit(Bgt_S, positive_step_label)      # if step > 0 jump to positive_step_label
            
            # step is negative - implement >= as NOT <
            self.generator.Emit(OpCodes.Ldsfld, symbol.realization) # Load the counter
            self.generator.Emit(OpCodes.Ldloc, last_value_local)    # Load the last value
            self.generator.Emit(OpCodes.Clt)                        # Compare less-than
            self.generator.Emit(OpCodes.Not)                        # Not 
            
            loop_back_label = self.generator.DefineLabel()
            self.generator.Emit(OpCodes.Br_S, loop_back_label)
            
            # step is positive - implement <= as NOT >
            self.generator.MarkLabel(positive_step_label)
            self.generator.Emit(OpCodes.Ldsfld, symbol.realization) # Load the counter
            self.generator.Emit(OpCodes.Ldloc, last_value_local)    # Load the last value
            self.generator.Emit(OpCodes.Cgt)                        # Compare less-than
            self.generator.Emit(OpCodes.Not)                        # Not 
            
            # loop back if not finished
            self.generator.MarkLabel(loop_back_label)
            self.generator.Emit(OpCodes.Brtrue, loop_body_label)
        
        # Attach the closure to the for_to_step object for later use
        for_to_step.generateNext = correspondingNext
        return self.successorOf(for_to_step)
    
    def visitRead(self, read):
        # Determine the type of the value and dispatch appropriately
        # Read the DATA, evaluate the expression in the context of the
        # value required, and place the value of the stack. Then assign
        # the value of top of the stack to the value.
        print "Visiting ", read
        # TODO: Convert IndexOutOfRangeException to NoDataException
        # Get the DATA as a string
        self.generator.Emit(OpCodes.Ldsfld, self.assembly_generator.data_field) # Load the DATA array onto the stack
        self.generator.Emit(OpCodes.Ldsfld, self.assembly_generator.data_index_field) # Load the DATA index onto the stack
        self.generator.Emit(OpCodes.Ldelem_Ref) # Push the DATA element (a string) onto the stack
        
        print "READ writables = ", read.writables
        assert len(read.writables.writables) == 1
        read.writables.writables[0].accept(self)
        return self.successorOf(read)
        
    def visitDyadicByteIndirection(self, dyadic):
        # If this is an l-value take the value from the top of the stack, and assign it
        # as a byte to the location, otherwise read from that value
        if dyadic.isLValue:
            # Pop the byte on top of the stack and write to the location
            print "Dyadic byte indirection l-value"
            # Are we writing to a block or directly into memory?
            if dyadic.base.formalType is PtrType:
                # Writing directly into address space
                # TODO: get the array representing our faked address space onto the stack
                pass
            elif dyadic.base.formalType is ByteArrayType:
                # Writing into a byte array
                # TODO: get the array onto the stack
                pass
            # TODO: Index and write into the array
        else:
            # Read from the location and push onto the stack
            print "Dyadic byte indirection r-value"
            # Are we reading from a block or directly from memory?
        
             
            
            
        
         
        