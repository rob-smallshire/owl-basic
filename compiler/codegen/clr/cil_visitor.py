'''
Created on 10 Aug 2009

@author: rjs
'''

import logging

import clr
import System
from System.Reflection import *
from System.Reflection.Emit import *

from visitor import Visitor
from syntax.ast import *
from ast_utils import findNode
import cts
import errors
from emitters import *
from symbol_tables import hasSymbolTableLookup
from algorithms import representative
from typing.type_system import (OwlType, NumericOwlType, ObjectOwlType, StringOwlType, ByteArrayOwlType)

# Load the OWL Runtime library so we may both call and reference
# methods within it
clr.AddReferenceToFileAndPath(r'C:\Users\rjs\Documents\dev\p4smallshire\sandbox\bbc_sharp_basic\OwlRuntime\OwlRuntime\bin\Debug\OwlRuntime.dll')
import OwlRuntime

class CodeGenerationError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def binaryTypeMatch(operator, lhs_type, rhs_type):
    '''
    Returns True if the left hand side and right hand side of the supplied binary operator
    match the supplied types.
    :param lhs_type: The Type of the left hand side expression
    :param rhs_type: The Type of the right hand side expression
    :returns: True if the types match, otherwise False
    '''
    return operator.lhs.actualType.isA(lhs_type) and operator.lhs.actualType.isA(rhs_type)

def getMethod(type, name, *args):
    '''
    Obtain the MethodInfo object from a type for a method called name
    with argument types equivalent to the OWL BASIC types supplied in
    *args.
    '''
    return type.GetMethod(name, System.Array[System.Type]([cts.mapType(arg) for arg in args]))

class CilVisitor(Visitor):
    '''
    Emit CIL bytecode whilst traversing the AST/CFG
    '''


    def __init__(self, assembly_generator, type_builder, method_builder, line_mapper, doc):
        '''
        Create a new CilVisitor for generating a CIL method.
        :param type_builder A System.Reflection.Emit.TypeBuilder
        :param entry_point_node The entry point CFG node of a method
        :param doc: The ISymbolDocumentWriter for debugging information
        '''
        self.assembly_generator = assembly_generator
        self.type_builder = type_builder
        self.method_builder = method_builder
        self.line_mapper = line_mapper
        self.doc = doc

        # Pending rvalue - used using generation of assignment statements
        # A callable used to defer generation of code to get the right stack sequence
        self.__pending_rvalue = None
        
        # Used for tracking whether we need to generation a query on INPUT
        self.__query = True
        
        # Used for the local variable builder for the temporary queue used by INPUT
        self.__queue_builder = None
        
        self.__cil_debug = True
        
        # Do we allow arrays to be re-DIMed; BBC BASIC does not
        self.__allow_redimension = False 
        
        # Get the type of OwnRuntime.BasicCommand so we can retrieve methods
        self.basic_commands_type = clr.GetClrType(OwlRuntime.BasicCommands)
        self.memory_map_type = clr.GetClrType(OwlRuntime.MemoryMap)
        self.string_type = clr.GetClrType(System.String)
        self.math_type = clr.GetClrType(System.Math)
        self.console_type = clr.GetClrType(System.Console)
        self.type_type = clr.GetClrType(System.Type)
        self.array_type = clr.GetClrType(System.Array)
        generic_queue_type = clr.GetClrType(System.Collections.Generic.Queue)
        self.object_queue_type = generic_queue_type.MakeGenericType(
                           System.Array[System.Type]([clr.GetClrType(System.Object)]))
        self.generator = self.method_builder.GetILGenerator()
        #self.generator.Emit(OpCodes.Nop) # Every method needs at least one OpCode

    def symbolFromVariable(self, variable):
        name = variable.identifier
        logging.debug("identifier = %s", name)
        symbol_node = findNode(variable, hasSymbolTableLookup)
        symbol = symbol_node.symbolTable.lookup(name)
        assert symbol is not None
        return symbol


    def generatePendingRValue(self):
        assert self.__pending_rvalue
        self.__pending_rvalue()
        self.__pending_rvalue = None

    def lookupMethod(self, name):
        '''
        Return a MethodInfo object for the named PROC or FN
        using the OWL name, e.g. 'PROCfoo'
        '''
        cts_name = self.assembly_generator.lookupCtsMethodName(name)
        return self.assembly_generator.lookupMethod(cts_name)
        
    def basicCommandMethod(self, name, *args):
        '''
        Return a MethodInfo object for the named method of OwlRuntime.BasicCommands
        '''
        print args
        method = self.basic_commands_type.GetMethod(name)
        assert method, "Could not locate BasicCommands method %s" % name
        return method
    
    def basicCommandOverloadedMethod(self, name, *args):
        '''
        Return a MethodInfo object for the named method of OwlRuntime.BasicCommands
        '''
        print args
        method = self.basic_commands_type.GetMethod(name, System.Array[System.Type]([cts.mapType(arg) for arg in args]))
        assert method, "Could not locate BasicCommands method %s" % name
        return method
    
    def convertClrToOwlBool(self):
        '''
        Convert the CLR bool value on the stack (0 or 1) to an OWL BASIC
        integer on the stack (0 or -1)
        '''
        self.generator.Emit(OpCodes.Neg)
                
    def successorOf(self, node):
        assert len(node.outEdges) <= 1
        if len(node.outEdges) == 0:
            return None
        return representative(node.outEdges)
    
    def checkMark(self, statement):
        '''
        If this basic block has not yet been marked, mark the label prior
        to the next instruction to be emitted into the CIL stream.
        '''
        if not statement.block.is_label_marked:
            self.generator.MarkLabel(statement.block.label)
            statement.block.is_label_marked = True
    
    def visitAstNode(self, node):
        raise CodeGenerationError("Visiting unhandled node %s" % node)
    
    def visitAstStatement(self, statement):
        raise CodeGenerationError("Visiting unhandled statement %s" % statement)
    
    def visitData(self, data):
        #self.checkMark(data)
        pass
    
    def visitRem(self, rem):
        #self.checkMark(rem)
        pass
    
    def visitAllocateArray(self, allocator):
        logging.debug("Visiting %s", allocator)
        print allocator.dimensions
        assert len(allocator.dimensions) > 0
        symbol_node = findNode(allocator, hasSymbolTableLookup)
        symbol = symbol_node.symbolTable.lookup(allocator.identifier)
        assert symbol is not None
        assert symbol.storeEmitter is not None
        assert symbol.loadEmitter is not None
        assert symbol.type.isArray()
        element_type = symbol.type.elementType()
        assert element_type is not None
        
        # Check that the array hasn't already been allocated. We could
        # control this through a compiler option.
        if not self.__allow_redimension:
            symbol.loadEmitter(self.generator) # Push the array reference on to the stack
            begin_allocation = self.generator.DefineLabel()
            self.generator.Emit(OpCodes.Brfalse, begin_allocation) # TODO: Short branch # TODO: Short branch
            emitLdc_I4(self.generator, self.line_mapper.physicalToLogical(allocator.lineNum)) # Load logical line number onto the stack
            bad_dim_exception_ctor = clr.GetClrType(OwlRuntime.BadDimException).GetConstructor(System.Array[System.Type]([System.Int32]))
            assert bad_dim_exception_ctor
            self.generator.Emit(OpCodes.Newobj, bad_dim_exception_ctor) # BadDimException on the stack
            self.generator.Emit(OpCodes.Throw)
            self.generator.MarkLabel(begin_allocation)
        
        num_dims = len(allocator.dimensions)
        assert num_dims > 0
        if num_dims == 1:
            allocator.dimensions[0].accept(self)
            self.generator.Emit(OpCodes.Newarr, cts.mapType(element_type))
        else:
            ctor_args = []     
            for dimension in allocator.dimensions:
                dimension.accept(self)
                ctor_args.append(cts.typeof(System.Int32))    
            ctor = cts.symbolType(symbol).GetConstructor(System.Array[System.Type](ctor_args))
            self.generator.Emit(OpCodes.Newobj, ctor)
        symbol.storeEmitter(self.generator)    
    
    def visitAssignment(self, assignment):
        logging.debug("Visiting %s", assignment)
        #self.checkMark(assignment)
        # The code for generating the rvalue may need to be interleaved
        # with the code for generating the lvalue, in cases where the
        # lvalue is an assignment to an array element or an indirection
        # operator.  To handle these cases, we store a reference ot the
        # rvalue in this visitor and generate the lvalue.  We expect
        # the lvalue generator to also generate the code for the rvalue at
        # the appropriate point, and then set the stored rvalue in the
        # visitor to None. 
        
        def generateRValue(self=self, r_value=assignment.rValue):
            r_value.accept(self) # Store the rvalue
        
        self.__pending_rvalue = generateRValue
        assignment.lValue.accept(self) # Store the top of the stack into the lValue
        assert self.__pending_rvalue is None # Check that the rvalue has been used
                
    def visitVariable(self, variable):
        logging.debug("Visiting %s", variable)
        symbol = self.symbolFromVariable(variable)
        logging.debug(repr(symbol))
            
        # If this is an l-value take the rvalue from the top of the stack, and assign it,
        # otherwise read from that value    
        if variable.isLValue:
            assert self.__pending_rvalue is not None
            # Generate the code for the rvalue
            self.generatePendingRValue()
            # Store in the lvalue
            #  Lookup in the symbol table
            symbol.storeEmitter(self.generator)
        else:
            symbol.loadEmitter(self.generator)
    
    def visitIndexer(self, indexer):
        logging.debug("Visiting %s", indexer)
        symbol = self.symbolFromVariable(indexer)
        logging.debug(repr(indexer))
        
        num_dims = len(indexer.indices)
        assert num_dims > 0
        if num_dims == 1:
            # If this is an l-value take the rvalue from the top of the stack, and assign it,
            # otherwise read from that value    
            if indexer.isLValue:
                assert self.__pending_rvalue is not None
                symbol.loadEmitter(self.generator)    # Push array reference on the stack
                indexer.indices[0].accept(self)       # Push array index on the stack
                self.generatePendingRValue()          # Push the element value on the stack
                emitStelem_T(self.generator, cts.mapType(symbol.type.elementType())) # Store element   
            else:
                symbol.loadEmitter(self.generator)    # Push array reference on the stack
                indexer.indices[0].accept(self)       # Push array index on the stack
                emitLdelem_T(self.generator, cts.mapType(symbol.type.elementType())) # Load element
        else:
            # If this is an l-value take the rvalue from the top of the stack, and assign it,
            # otherwise read from that value    
            if indexer.isLValue:
                symbol.loadEmitter(self.generator) # Push array reference on the stack
                for index in indexer.indices:
                    index.accept(self)             # Push array index on the stack
                self.generatePendingRValue()       # Push the element value on the stack
                self.generator.Emit(OpCodes.Call, cts.symbolType(symbol).GetMethod("Set"))
            else:
                symbol.loadEmitter(self.generator) # Push array reference on the stack
                for index in indexer.indices:
                    index.accept(self)             # Push array index on the stack
                self.generator.Emit(OpCodes.Call, cts.symbolType(symbol).GetMethod("Get"))
                                            
    def visitLiteralString(self, literal_string):
        logging.debug("Visiting %s", literal_string)
        logging.debug("value = %s", literal_string.value)
        self.generator.Emit(OpCodes.Ldstr, literal_string.value)
        
    def visitCast(self, cast):
        logging.debug("Visiting %s", cast)
        # Get the value onto the stack
        cast.value.accept(self)
        
        # TODO: Use multimethods in here : http://www.artima.com/weblogs/viewpost.jsp?thread=101605
        # 
        # Convert - Int32 can be exactly converted to Double
        if cast.sourceType == IntegerOwlType():
            if cast.targetType == FloatOwlType():
                self.generator.Emit(OpCodes.Conv_R8)
                return
            if cast.targetType == ByteOwlType():
                # TODO: Are BBC BASIC bytes signed, or unsigned?
                # Should we truncate the value here to 0-255 ?
                return
            if cast.targetType == ObjectOwlType():
                self.generator.Emit(OpCodes.Box, cts.mapType(IntegerOwlType()))
                return
        elif cast.sourceType == ByteOwlType():
            if cast.targetType == FloatOwlType():
                self.generator.Emit(OpCodes.Conv_R8)
                return
            if cast.targetType == IntegerOwlType():
                # TODO: Is this correct?
                pass
            if cast.targetType == ObjectOwlType():
                self.generator.Emit(OpCodes.Box, cts.mapType(IntegerOwlType()))
                return
        elif cast.sourceType == FloatOwlType():
            if cast.targetType == IntegerOwlType():
                self.generator.Emit(OpCodes.Conv_Ovf_I4)
                return
            if cast.targetType == AddressOwlType():
                self.generator.Emit(OpCodes.Conv_Ovf_I)
                return
            if cast.targetType == ByteOwlType():
                # TODO: Are BBC BASIC bytes signed, or unsigned?
                self.generator.Emit(OpCodes.Conv_Ovf_I4)
                return
            if cast.targetType == ObjectOwlType():
                self.generator.Emit(OpCodes.Box, cts.mapType(IntegerOwlType()))
                return
        elif cast.sourceType == ObjectOwlType():
            if cast.targetType == StringOwlType():
                self.generator.Emit(OpCodes.Castclass, cts.mapType(StringOwlType()))
                return
            else:
                self.generator.Emit(OpCodes.Unbox, cts.mapType(cast.targetType))
                self.generator.Emit(OpCodes.Ldobj, cts.mapType(cast.targetType))
                return
            
        errors.internal("Unsupported cast from %s to %s" % (cast.sourceType, cast.targetType))
                
    def visitLiteralInteger(self, literal_integer):
        logging.debug("Visiting %s", literal_integer)
        logging.debug("value = %s", literal_integer.value)
        emitLdc_I4(self.generator, literal_integer.value)
    
    def visitLiteralFloat(self, literal_float):
        logging.debug("Visiting %s", literal_float)
        logging.debug("value = %s", literal_float.value)
        self.generator.Emit(OpCodes.Ldc_R8, literal_float.value)
    
    def visitVdu(self, vdu):
        logging.debug("Visiting %s", vdu)
        #self.checkMark(vdu)
        assert hasattr(vdu.bytes, '__getitem__')
        assert hasattr(vdu.bytes, '__len__')
        
        # TODO: For long lists of VDU items it may be cheaper to
        # assemble an array of bytes and then make one call
        for item in vdu.bytes:
            item.accept(self)
        
    def visitVduItem(self, item):
        item.item.accept(self) # Value on the stack
        # Convert to a byte or short as appropriate
        if item.length == 1 or item.length == 9:
            self.generator.Emit(OpCodes.Conv_I1)
            arg_type = System.Byte # TODO: Signed or unsigned?
        elif item.length == 2:
            self.generator.Emit(OpCodes.Conv_I2)
            arg_type = System.Int16 # TODO: Signed or unsigned?
        vdu_method = self.basic_commands_type.GetMethod('Vdu', System.Array[System.Type]([cts.typeof(arg_type)]))
        self.generator.Emit(OpCodes.Call, vdu_method)
        if item.length == 9:
            self.generator.Emit(OpCodes.Call, self.basicCommandMethod('VduFlush'))
    
    def visitCls(self, cls):
        logging.debug("Visiting %s", cls)
        #self.checkMark(cls)
        self.generator.Emit(OpCodes.Call, self.basicCommandMethod('Cls'))
    
    def visitDefineProcedure(self, defproc):
        logging.debug("Visiting %s", defproc)
        if self.__cil_debug:
            self.generator.Emit(OpCodes.Nop)
         
    def visitDefineFunction(self, deffn):
        logging.debug("Visiting %s", deffn)
        if self.__cil_debug:
            self.generator.Emit(OpCodes.Nop)
                  
    def visitCallProcedure(self, call_proc):
        logging.debug("Visiting %s", call_proc)
        logging.debug("name = %s", call_proc.name)
        #self.checkMark(call_proc)
        
        proc_method_info = self.lookupMethod(call_proc.name)
        
        for actual_parameter in call_proc.actualParameters:
            actual_parameter.accept(self)
        
        self.generator.Emit(OpCodes.Call, proc_method_info)
    
    def visitReturnFromProcedure(self, endproc):
        logging.debug("Visiting %s", endproc)
        # TODO: Must not be used from within an exception handler
        #self.checkMark(endproc)
        self.generator.Emit(OpCodes.Ret)
    
    def visitUserFunc(self, user_func):
        logging.debug("Visiting %s", user_func)
        logging.debug("name = %s", user_func.name)
        
        user_func_method_info = self.lookupMethod(user_func.name)
        
        for actual_parameter in user_func.actualParameters:
            actual_parameter.accept(self)
        
        self.generator.Emit(OpCodes.Call, user_func_method_info)
    
    def visitReturnFromFunction(self, func):
        logging.debug("Visiting %s", func)
        #self.checkMark(func)
        # TODO: Must not be used from within an exception handler
        func.returnValue.accept(self)
        self.generator.Emit(OpCodes.Ret)
       
    def visitRestore(self, restore):
        # TODO: Can we RESTORE to lines which don't contain DATA?
        logging.debug("Visiting %s", restore)
        logging.debug("target_logical_line = %s", restore.targetLogicalLine)
        #self.checkMark(restore)
        # Lookup the data pointer value for this line number
        self.generator.Emit(OpCodes.Ldsfld, self.assembly_generator.data_line_number_map_field)         # Load the dictionary onto the stack
        restore.targetLogicalLine.accept(self) # Push the line number onto the stack
        get_item_method_info = cts.int_int_dictionary_type.GetMethod('get_Item')
        self.generator.Emit(OpCodes.Call, get_item_method_info) # Call get_Item and the put the new data pointer result on the stack
        emitLdc_I4(self.generator, 1)
        self.generator.Emit(OpCodes.Sub) # Subtract 1, because READ will pre-increment the data index
        self.generator.Emit(OpCodes.Stsfld, self.assembly_generator.data_index_field)
    
    def visitRepeat(self, repeat):
        logging.debug("Visiting %s", repeat)
        #self.checkMark(repeat)
        repeat.label = self.generator.DefineLabel()
        self.generator.MarkLabel(repeat.label)
        if self.__cil_debug:
            self.generator.Emit(OpCodes.Nop)
        
    def visitUntil(self, until):
        logging.debug("Visiting %s", until)
        #self.checkMark(until)
        if len(until.loopBackEdges) != 0:
            assert len(until.loopBackEdges) == 1
            # Correlated NEXT
            repeat = representative(until.loopBackEdges)
            logging.debug("UNTIL correlates with %s", repeat)
            until.condition.accept(self)            # Push the condition onto the stack
            self.generator.Emit(OpCodes.Brfalse, repeat.label)  # Branch if false # TODO: Short branch?
        else:
            # Non-correlated UNTIL
            errors.internal("TODO: Non-correlated UNTIL")
        
    def visitForToStep(self, for_to_step):
        # TODO: Future optimizations
        # - if STEP is a constant we can simplify the test depending on its sign
        # - if the values are ints we can convert the type of the counter to an int
        # - if last is a constant its worth convert <= last into < last + 1 or the
        #   reverse, if we know the sign of step
        
        # TODO: Could probably hit most common cases STEP == +1 with completely different
        #       code gen FOR i% = 0 TO 9
        
        logging.debug("Visiting %s", for_to_step)
        #self.checkMark(for_to_step)
        
        # Load the initial counter value onto the stack
        for_to_step.first.accept(self)

        # Store in the loop counter variable
        name = for_to_step.identifier.identifier
        logging.debug("counter identifier = %s", name)
        counter_symbol = for_to_step.symbolTable.lookup(name)
        counter_type = cts.symbolType(counter_symbol)
        assert counter_symbol is not None
        logging.debug(repr(counter_symbol))
        counter_symbol.storeEmitter(self.generator)
        
        # Evaluate the last value and store in an unnamed local
        last_value_local = self.generator.DeclareLocal(counter_type)
        for_to_step.last.accept(self)
        self.generator.Emit(OpCodes.Stloc, last_value_local)
        
        # Evaluate the step value and store in an unnamed local
        step_value_local = self.generator.DeclareLocal(counter_type)
        for_to_step.step.accept(self)
        self.generator.Emit(OpCodes.Stloc, step_value_local)
                        
        # The loop body goes in here - later, but first...
        loop_body_label = self.generator.DefineLabel()
        self.generator.MarkLabel(loop_body_label)
        
        # Define a function (closure) which can be called later to generate
        # the code for the corresponding NEXT statements
        def correspondingNext():
            # Increment the counter
            counter_symbol.loadEmitter(self.generator)              # Load the counter
            self.generator.Emit(OpCodes.Ldloc, step_value_local)    # Load the STEP value
            self.generator.Emit(OpCodes.Add)                        # Add
            counter_symbol.storeEmitter(self.generator)             # Load the counter # Store the counter
            
            # Check the sign of the step value
            self.generator.Emit(OpCodes.Ldloc, step_value_local) # Load the STEP value
            emitLdc_T(self.generator, 0, counter_type)           # Push zero on the stack
            
            positive_step_label = self.generator.DefineLabel()   
            self.generator.Emit(OpCodes.Bgt, positive_step_label)      # if step > 0 jump to positive_step_label # TODO: Short branch?
            
            loop_back_label = self.generator.DefineLabel()
            
            # step is negative - implement >= as NOT <
            counter_symbol.loadEmitter(self.generator)              # Load the counter
            self.generator.Emit(OpCodes.Ldloc, last_value_local)    # Load the last value
            self.generator.Emit(OpCodes.Clt)                        # Compare less-than
            emitLdc_I4(self.generator, 0)                           # Load 0
            self.generator.Emit(OpCodes.Ceq)                        # Compare equal
            self.generator.Emit(OpCodes.Br, loop_back_label) # TODO: Short branch? 
            
            # step is positive - implement <= as NOT >
            self.generator.MarkLabel(positive_step_label)
            counter_symbol.loadEmitter(self.generator)              # Load the counter
            self.generator.Emit(OpCodes.Ldloc, last_value_local)    # Load the last value
            self.generator.Emit(OpCodes.Cgt)                        # Compare greater-than
            emitLdc_I4(self.generator, 0)                           # Load 0
            self.generator.Emit(OpCodes.Ceq)                        # Compare equal
            
            # loop back if not finished
            self.generator.MarkLabel(loop_back_label)
            self.generator.Emit(OpCodes.Brtrue, loop_body_label)
        
        # Attach the closure to the for_to_step object for later use
        for_to_step.generateNext = correspondingNext
    
    def visitNext(self, next):
        logging.debug("Visiting %s", next)
        #self.checkMark(next)
        if  len(next.loopBackEdges) != 0:
            assert len(next.loopBackEdges) == 1
            # Correlated NEXT
            for_to_step = representative(next.loopBackEdges)
            logging.debug("NEXT correlates with %s", for_to_step)
            for_to_step.generateNext()
        else:
            # Non-correlated NEXT
            errors.internal("TODO: Non-correlated NEXT")
       
    def visitReadFunc(self, read_func):
        # Determine the type of the value and dispatch appropriately
        # Read the DATA, evaluate the expression in the context of the
        # value required, and place the value of the stack.
        logging.debug("Visiting %s", read_func)
        # TODO: Convert IndexOutOfRangeException to NoDataException
        # Get the DATA as a string
        self.generator.Emit(OpCodes.Ldsfld, self.assembly_generator.data_field) # Load the DATA array onto the stack
        self.generator.Emit(OpCodes.Ldsfld, self.assembly_generator.data_index_field) # Load the DATA index onto the stack
        emitLdc_I4(self.generator, 1)    # Load 1 onto the stack
        self.generator.Emit(OpCodes.Add) # Increment
        self.generator.Emit(OpCodes.Dup) # Duplicate the incremented DATA index
        self.generator.Emit(OpCodes.Stsfld, self.assembly_generator.data_index_field) # Store the incremented DATA index
        self.generator.Emit(OpCodes.Ldelem_Ref) # Push the DATA element (a string) onto the stack

        # DEBUG
        #self.generator.Emit(OpCodes.Dup)
        #print_method = self.basic_commands_type.GetMethod("Print", System.Array[System.Type]([cts.mapType(StringOwlType())]))
        #self.generator.Emit(OpCodes.Call, print_method)
        #self.generator.Emit(OpCodes.Call, self.basicCommandMethod('NewLine'))
        # END DEBUG

        # TODO: Convert to the required type
        system_convert_type = clr.GetClrType(System.Convert)
        
        if read_func.actualType == ByteOwlType():
            conversion_method = system_convert_type.GetMethod("ToByte", System.Array[System.Type]([clr.GetClrType(str)]))
        elif read_func.actualType == IntegerOwlType():
            conversion_method = system_convert_type.GetMethod("ToInt32", System.Array[System.Type]([clr.GetClrType(str)]))
        elif read_func.actualType == FloatOwlType():
            conversion_method = system_convert_type.GetMethod("ToDouble", System.Array[System.Type]([clr.GetClrType(str)]))
        else:
            conversion_method = None
        # TODO: etc
        # TODO: Should handle conversion failures gracefully. How does BBC BASIC do this?
        
        if conversion_method:
            self.generator.Emit(OpCodes.Call, conversion_method)
        
    def visitDyadicByteIndirection(self, dyadic):
        logging.debug("Visiting %s", dyadic)
        # If this is an l-value take the value from the top of the stack, and assign it
        # as a byte to the location, otherwise read from that value
        if dyadic.isLValue:
            # Check that there is a pending rvalue waiting to be written
            assert self.__pending_rvalue is not None
            # Pop the byte on top of the stack and write to the location
            logging.debug("Dyadic byte indirection l-value")
            # Are we writing to a block or directly into memory?
            if dyadic.base.formalType == AddressOwlType():
                # Writing directly into address space
                # Push the array representing our faked address space onto the stack
                memory_getter = self.memory_map_type.GetMethod("get_Memory")
                self.generator.Emit(OpCodes.Call, memory_getter)
                
                dyadic.base.accept(self)  # Push the base address onto the stack
                dyadic.offset.accept(self) # Push the offset onto the stack
                self.generator.Emit(OpCodes.Add) # Add base to offset
                
                # Get the value on the stack here
                self.generatePendingRValue()
                
                self.generator.Emit(OpCodes.Stelem_I1) # Store into the array
                
            elif dyadic.base.formalType == ByteArrayOwlType(): # TODO: Check for rank == 1
                # Writing into a byte array
                # TODO: get the array onto the stack
                logging.critical("TODO: Dyadic byte indirection array l-value")
                pass
            # TODO: Index and write into the array
        else:
            # Read from the location and push onto the stack
            logging.debug("Dyadic byte indirection r-value")
            # Are we reading from a block or directly from memory?
            if dyadic.base.formalType == AddressOwlType():
                # Reading directly from address space
                # Push the array representing our faked address space onto the stack
                memory_getter = self.memory_map_type.GetMethod("get_Memory")
                self.generator.Emit(OpCodes.Call, memory_getter)
                
                dyadic.base.accept(self)  # Push the base address onto the stack
                dyadic.offset.accept(self) # Push the offset onto the stack
                self.generator.Emit(OpCodes.Add) # Add base to offset
                
                self.generator.Emit(OpCodes.Ldelem_I1) # Store into the array
            else:
                logging.critical("TODO: Dyadic byte indirection array r-value") 
        
    def visitPrint(self, print_stmt):
        logging.debug("Visiting %s", print_stmt)
        #self.checkMark(print_stmt)
        # Convert each print item into a call to the runtime library
        logging.debug("print list = %s", str(print_stmt.printList))
        suppress_newline = False
        
        if print_stmt.printList is not None:
            for print_item in print_stmt.printList:
                item = print_item.item
                item.accept(self)
                if not isinstance(item, PrintManipulator):
                    print_method = self.basic_commands_type.GetMethod("Print", System.Array[System.Type]([cts.mapType(item.actualType)]))
                    self.generator.Emit(OpCodes.Call, print_method)
                
            if len(print_stmt.printList) > 0:
                last_item = print_stmt.printList[-1].item
                if isinstance(last_item, PrintManipulator) and last_item.manipulator == ';':
                    suppress_newline = True
                    
        if not suppress_newline:
            self.generator.Emit(OpCodes.Call, self.basicCommandMethod('NewLine'))
    
    def visitInput(self, input):
        logging.debug("Visiting %s", input)
        #self.checkMark(input)
        # Convert each input item int a call to the runtime library
        logging.debug("input list = %s", str(input.inputList))
        self.__query = True
        items = input.inputList
        if items is not None:
            print items
            while len(items) > 0:
                item = items.pop(0).item
                if not isinstance(item, Variable):
                    print "Input Item = ", item
                    item.accept(self)
                    if isinstance(item, LiteralString):
                        self.__query = False
                        print_method = self.basic_commands_type.GetMethod("Print", System.Array[System.Type]([cts.mapType(item.actualType)]))
                        self.generator.Emit(OpCodes.Call, print_method)
                else:
                    variables = [item]
                    while len(items) > 0 and isinstance(items[0], Variable):
                        item = items.pop(0).item
                        variables.append(item)
                    # Set up the function call to input
                    emitLdc_I4(self.generator, 1 if self.__query else 0) # Push __query on the stack
                    emitLdc_I4(self.generator, len(variables)) # Push the number of variables onto the stack
                    self.generator.Emit(OpCodes.Newarr, clr.GetClrType(System.Type)) # Array of Types on the stack
                    
                    var_types = (cts.symbolType(self.symbolFromVariable(var)) for var in variables)
                    for i, type in enumerate(var_types):
                        self.generator.Emit(OpCodes.Dup) # Array on the stack # TODO: Load local
                        emitLdc_I4(self.generator, i)    # Index on the stack
                        self.generator.Emit(OpCodes.Ldtoken, type) # Type token on the stack
                        get_type_from_handle_method = self.type_type.GetMethod("GetTypeFromHandle", System.Array[System.Type]([clr.GetClrType(System.RuntimeTypeHandle)]))
                        self.generator.Emit(OpCodes.Call, get_type_from_handle_method) # Type on the stack
                        self.generator.Emit(OpCodes.Stelem_Ref) # Store in the array
                    
                    # Call the function
                    self.generator.Emit(OpCodes.Call, self.basicCommandMethod('Input')) # Queue on the stack
                    # Store the queue in a local
                    if self.__queue_builder is None:
                        self.__queue_builder = self.generator.DeclareLocal(clr.GetClrType(self.object_queue_type))
                    self.generator.Emit(OpCodes.Stloc, self.__queue_builder)
                    
                    # Dequeue the results into the variables
                    dequeue_method = self.object_queue_type.GetMethod("Dequeue")
                    for variable in variables:
                        def generateRValue(self=self, variable=variable):
                            self.generator.Emit(OpCodes.Ldloc, self.__queue_builder) # Load queue local
                            self.generator.Emit(OpCodes.Call, dequeue_method)
                            cts_type = cts.symbolType(self.symbolFromVariable(variable))
                            if cts_type.IsValueType:
                                self.generator.Emit(OpCodes.Unbox, cts_type)
                            else:
                                self.generator.Emit(OpCodes.Castclass, cts.mapType(StringOwlType()))
                        self.__pending_rvalue = generateRValue
                        variable.accept(self)
                        assert self.__pending_rvalue is None
                                                
    def visitInputManipulator(self, node):
        logging.debug("Visiting %s", node)
        manipulator = node.manipulator
        logging.debug("manipulator = %s", manipulator)
        # TODO: This is likely to result in a lot of redundant function calls, so we
        #       should be smarter about only making those calls which are necessary
        if manipulator == "'":
            self.generator.Emit(OpCodes.Call, self.basicCommandMethod('NewLine'))
            self.__query = False
        elif manipulator == ",":
            self.__query = True
        elif manipulator == ";":
            self.__query = True

    def visitTabH(self, tabh):
        logging.debug("Visiting %s", tabh) 
        tabh.xCoord.accept(self)                                           # Get the horizontal tab value onto the stack
        self.generator.Emit(OpCodes.Call, self.basicCommandMethod('TabH')) # Call the runtime library
        
    def visitTabXY(self, tabxy):
        logging.debug("Visiting %s", tabxy)
        tabxy.xCoord.accept(self)
        tabxy.yCoord.accept(self)
        self.generator.Emit(OpCodes.Call, self.basicCommandMethod('TabXY'))
    
    # TODO: This code for converting manipulators into function calls should happen earlier
    #       since it is independent of the back-end
                                
    def visitFormatManipulator(self, node):
        logging.debug("Visiting %s", node)
        manipulator = node.manipulator
        logging.debug("manipulator = %s", manipulator)
        # TODO: This is likely to result in a lot of redundant function calls, so we
        #       should be smarter about only making those calls which are necessary
        if manipulator == "~":
            self.generator.Emit(OpCodes.Call, self.basicCommandMethod('HexFormat'))
        elif manipulator == "'":
            self.generator.Emit(OpCodes.Call, self.basicCommandMethod('NewLine'))
        elif manipulator == ",":
            self.generator.Emit(OpCodes.Call, self.basicCommandMethod('RightJustifyNumerics'))
            self.generator.Emit(OpCodes.Call, self.basicCommandMethod('DecFormat'))
            self.generator.Emit(OpCodes.Call, self.basicCommandMethod('CompleteField'))
        elif manipulator == ";":
            self.generator.Emit(OpCodes.Call, self.basicCommandMethod('DisableRightJustifyNumerics'))
            self.generator.Emit(OpCodes.Call, self.basicCommandMethod('DecFormat'))
                    
    def visitSpc(self, spc):
        logging.debug("Visiting %s", spc)
        spc.spaces.accept(self)
        self.generator.Emit(OpCodes.Call, self.basicCommandMethod('Spc'))
    
    def visitGetFunc(self, get):
        "GET - read a character from the console"
        logging.debug("Visiting %s", get)
        self.generator.Emit(OpCodes.Call, self.basicCommandMethod('Get'))
              
    def visitEnd(self, end):      
        logging.debug("Visiting %s", end)
        #self.checkMark(end)
        # If we are emitting code in Main, then just return,
        # otherwise throw an EndException
        if "MAIN" in end.entryPoints:
            self.generator.Emit(OpCodes.Ret)
        else:
            emitLdc_I4(self.generator, self.line_mapper.physicalToLogical(end.lineNum)) # Load logical line number onto the stack
            end_exception_ctor = clr.GetClrType(OwlRuntime.EndException).GetConstructor(System.Array[System.Type]([System.Int32]))
            assert end_exception_ctor
            self.generator.Emit(OpCodes.Newobj, end_exception_ctor) # EndException on the stack
            self.generator.Emit(OpCodes.Throw)
    
    def visitUnaryMinus(self, unary_minus):
        logging.debug("Visiting %s", unary_minus)
        # TODO: Deal with unknown types (e.g. Object)
        unary_minus.factor.accept(self)
        self.generator.Emit(OpCodes.Neg)
    
    def visitPlus(self, plus):
        logging.debug("Visiting %s", plus)
        # TODO: Deal with unknown types (e.g. Object)
        # TODO: Factor out for BinaryNumericOperators
        plus.lhs.accept(self)
        plus.rhs.accept(self)
        self.generator.Emit(OpCodes.Add)
    
    def visitMinus(self, minus):
        logging.debug("Visiting %s", minus)
        # TODO: Deal with unknown types (e.g. Object)
        # TODO: Factor out for BinaryNumericOperators
        minus.lhs.accept(self)
        minus.rhs.accept(self)
        self.generator.Emit(OpCodes.Sub)
    
    def visitMultiply(self, multiply):
        logging.debug("Visiting %s", multiply)
        # TODO: Deal with unknown types (e.g. Object)
        # TODO: Factor out for BinaryNumericOperators
        multiply.lhs.accept(self)
        multiply.rhs.accept(self)
        self.generator.Emit(OpCodes.Mul)
    
    def visitDivide(self, divide):
        logging.debug("Visiting %s", divide)
        # TODO: Deal with unknown types (e.g. Object)
        # TODO: Factor out for BinaryNumericOperators
        divide.lhs.accept(self)
        divide.rhs.accept(self)
        self.generator.Emit(OpCodes.Div)
    
    def visitPower(self, power):
        logging.debug("Visiting %s", power)
        # TODO: Deal with unknown types (e.g. Object)
        # TODO: Factor out for BinaryNumericOperators
        power.lhs.accept(self)
        power.rhs.accept(self)
        if binaryTypeMatch(power, IntegerOwlType(), IntegerOwlType()):
            power_method = self.basicCommandOverloadedMethod('Pow', IntegerOwlType(), IntegerOwlType())
        else:
            power_method = self.basicCommandOverloadedMethod('Pow', FloatOwlType(), FloatOwlType())
        self.generator.Emit(OpCodes.Call, power_method)
    
    def visitAnd(self, op):
        # TODO: Deal with unknown types (e.g. Object)
        logging.debug("Visiting %s", op)
        op.lhs.accept(self)
        op.rhs.accept(self)
        self.generator.Emit(OpCodes.And)
        
    def visitOr(self, op):
        # TODO: Deal with unknown types (e.g. Object)
        logging.debug("Visiting %s", op)
        op.lhs.accept(self)
        op.rhs.accept(self)
        self.generator.Emit(OpCodes.Or)    
           
    def visitEor(self, op):
        # TODO: Deal with unknown types (e.g. Object)
        logging.debug("Visiting %s", op)
        op.lhs.accept(self)
        op.rhs.accept(self)
        self.generator.Emit(OpCodes.Xor)
        
    def visitNot(self, op):
        op.factor.accept(self)
        # TODO: Deal with unknown types (e.g. Object)
        self.generator.Emit(OpCodes.Not)
           
    def visitEqual(self, operator):
        logging.debug("Visiting %s", operator)
        operator.lhs.accept(self) # Lhs on the stack
        operator.rhs.accept(self) # Rhs on the stack
        
        if binaryTypeMatch(operator, NumericOwlType(), NumericOwlType()):
            self.generator.Emit(OpCodes.Ceq)
            self.convertClrToOwlBool()
        elif binaryTypeMatch(operator, StringOwlType(), StringOwlType()):
            string_equals_method = self.string_type.GetMethod("Equals", System.Array[System.Type]([cts.mapType(StringOwlType()),
                                                                                                   cts.mapType(StringOwlType())]))
            self.generator.Emit(OpCodes.Call, string_equals_method) 
            self.convertClrToOwlBool()
        elif binaryTypeMatch(operator, ObjectOwlType(), OwlType()) or \
             binaryTypeMatch(operator, OwlType(), ObjectOwlType()):
            equal_method = self.basic_commands_type.GetMethod("Equal",
                                                              System.Array[System.Type]([cts.mapType(operator.lhs.actualType),
                                                                                         cts.mapType(operator.rhs.actualType)]))
            self.generator.Emit(OpCodes.Call, equal_method)
            
    def visitNotEqual(self, operator):
        logging.debug("Visiting %s", operator)
        operator.lhs.accept(self) # Lhs on the stack
        operator.rhs.accept(self) # Rhs on the stack
        
        if binaryTypeMatch(operator, NumericOwlType(), NumericOwlType()):
            self.generator.Emit(OpCodes.Ceq)
            emitLdc_I4(self.generator, 1) # 0 ==> -1, 1 ==> 0
            self.generator.Emit(OpCodes.Sub)
        elif binaryTypeMatch(operator, StringOwlType(), StringOwlType()):
            string_equals_method = self.string_type.GetMethod("Equals", System.Array[System.Type]([cts.mapType(StringOwlType()),
                                                                                                    cts.mapType(StringOwlType())]))
            self.generator.Emit(OpCodes.Call, string_equals_method)
            emitLdc_I4(self.generator, 1) # 0 ==> -1, 1 ==> 0
            self.generator.Emit(OpCodes.Sub)
        elif binaryTypeMatch(operator, ObjectOwlType(), OwlType()) or \
             binaryTypeMatch(operator, OwlType(), ObjectOwlType()):
            equal_method = self.basic_commands_type.GetMethod("NotEqual",
                                                              System.Array[System.Type]([cts.mapType(operator.lhs.actualType),
                                                                                         cts.mapType(operator.rhs.actualType)]))
            self.generator.Emit(OpCodes.Call, equal_method)

    def visitLessThan(self, operator):
        logging.debug("Visiting %s", operator)
        operator.lhs.accept(self) # Lhs on the stack
        operator.rhs.accept(self) # Rhs on the stack
        
        if binaryTypeMatch(operator, NumericOwlType(), NumericOwlType()):
            self.generator.Emit(OpCodes.Clt)
            self.convertClrToOwlBool()
        elif binaryTypeMatch(operator, StringOwlType(), StringOwlType()):
            string_equals_method = self.string_type.GetMethod("Compare", System.Array[System.Type]([cts.mapType(StringOwlType()),
                                                                                                   cts.mapType(StringOwlType())]))
            self.generator.Emit(OpCodes.Call, string_equals_method)
            # Convert -1 => -1, 0 => 0, +1 => 0
            emitLdc_I4(self.generator, -1)
            self.generator.Emit(OpCodes.Ceq)
            self.convertClrToOwlBool()
        elif binaryTypeMatch(operator, ObjectOwlType(), OwlType()) or \
             binaryTypeMatch(operator, OwlType(), ObjectOwlType()):
            logging.critical("Unsupported less-than operand types")

    def visitLessThanEqual(self, operator):
        logging.debug("Visiting %s", operator)
        operator.lhs.accept(self) # Lhs on the stack
        operator.rhs.accept(self) # Rhs on the stack
        if binaryTypeMatch(operator, NumericOwlType(), NumericOwlType()):
            self.generator.Emit(OpCodes.Cgt)
            emitLdc_I4(self.generator, 0)
            self.generator.Emit(OpCodes.Ceq)
            self.convertClrToOwlBool()
        elif binaryTypeMatch(operator, StringOwlType(), StringOwlType()):
            string_equals_method = self.string_type.GetMethod("Compare", System.Array[System.Type]([cts.mapType(StringOwlType()),
                                                                                                   cts.mapType(StringOwlType())]))
            self.generator.Emit(OpCodes.Call, string_equals_method)
            # Convert -1 => -1, 0 => -1, +1 => 0
            emitLdc_I4(self.generator, 1)
            self.generator.Emit(OpCodes.Ceq)
            emitLdc_I4(self.generator, 1)
            self.generator.Emit(OpCodes.Sub)
            
        elif binaryTypeMatch(operator, ObjectOwlType(), OwlType()) or \
             binaryTypeMatch(operator, OwlType(), ObjectOwlType()):
            logging.critical("Unsupported less-than operand types")

    def visitGreaterThan(self, operator):
        logging.debug("Visiting %s", operator)
        operator.lhs.accept(self) # Lhs on the stack
        operator.rhs.accept(self) # Rhs on the stack
        
        if binaryTypeMatch(operator, NumericOwlType(), NumericOwlType()):
            self.generator.Emit(OpCodes.Cgt)
            self.convertClrToOwlBool()
        elif binaryTypeMatch(operator, StringOwlType(), StringOwlType()):
            string_equals_method = self.string_type.GetMethod("Compare", System.Array[System.Type]([cts.mapType(StringOwlType()),
                                                                                                   cts.mapType(StringOwlType())]))
            self.generator.Emit(OpCodes.Call, string_equals_method)
            # Convert -1 => 0, 0 => 0, +1 => -1
            emitLdc_I4(self.generator, +1)
            self.generator.Emit(OpCodes.Ceq)
            self.convertClrToOwlBool()
        elif binaryTypeMatch(operator, ObjectOwlType(), OwlType()) or \
             binaryTypeMatch(operator, OwlType(), ObjectOwlType()):
            logging.critical("Unsupported greater-than operand types")

    def visitGreaterThanEqual(self, operator):
        logging.debug("Visiting %s", operator)
        operator.lhs.accept(self) # Lhs on the stack
        operator.rhs.accept(self) # Rhs on the stack
        
        if binaryTypeMatch(operator, NumericOwlType(), NumericOwlType()):
            self.generator.Emit(OpCodes.Clt)
            emitLdc_I4(self.generator, 0)
            self.generator.Emit(OpCodes.Ceq)
            self.convertClrToOwlBool()
        elif binaryTypeMatch(operator, StringOwlType(), StringOwlType()):
            string_equals_method = self.string_type.GetMethod("Compare", System.Array[System.Type]([cts.mapType(StringOwlType()),
                                                                                                   cts.mapType(StringOwlType())]))
            self.generator.Emit(OpCodes.Call, string_equals_method)
            # Convert -1 => 0, 0 => -1, +1 => -1
            emitLdc_I4(self.generator, -1)
            self.generator.Emit(OpCodes.Ceq)
            emitLdc_I4(self.generator, 1)
            self.generator.Emit(OpCodes.Sub)
            
        elif binaryTypeMatch(operator, ObjectOwlType(), OwlType()) or \
             binaryTypeMatch(operator, OwlType(), ObjectOwlType()):
            logging.critical("Unsupported greater-than operand types")

    def visitIf(self, if_stmt):
        logging.debug("Visiting %s", if_stmt)
        #self.checkMark(if_stmt)
        if_stmt.condition.accept(self) # Condition on the stack
        assert if_stmt.trueClause is not None
        first_true_stmt = if_stmt.trueClause[0] 
        
        # Find the target statement for the negative (ELSE) case, which is
        # either the ELSE clause or just the following statement if there is
        # no else clause
        outEdges = set(if_stmt.outEdges)
        outEdges.discard(first_true_stmt)
        assert len(outEdges) == 1
        representative(outEdges)
        first_false_stmt = representative(outEdges)
        if if_stmt.falseClause:
            assert if_stmt.falseClause[0] is first_false_stmt
        # Usually (always?) only one of the following calls will result in a generated branch
        # Whether we branch to the trueClause, the falseClause or both depends of the
        # ordering of the basic blocks
        this_block_ordinal = if_stmt.block.topological_order
        true_block_ordinal = first_true_stmt.block.topological_order
        false_block_ordinal = first_false_stmt.block.topological_order
        
        if true_block_ordinal == this_block_ordinal + 1:
            # The true block immediately succeeds this block
            # Branch on the negative case
            self.generator.Emit(OpCodes.Brfalse, first_false_stmt.block.label)
            # Fall through to the true block
        elif false_block_ordinal == this_block_ordinal + 1:
            # The false block immediately succeeds this block
            # Branch on the positive case
            self.generator.Emit(OpCodes.Brtrue, first_true_stmt.block.label)
            # Fall through to the false block
        else:
            # Neither the true block nor the false block immediately succeed this block
            # Conditionally branch on the true case
            self.generator.Emit(OpCodes.Brtrue, first_true_stmt.block.label)
            self.generator.Emit(OpCodes.Br, first_false_stmt.block.label)
            # Unconditionally branch on the false case 
    
    def visitOnGoto(self, ongoto):
        logging.debug("Visiting %s", ongoto)
        #self.checkMark(ongoto)
        # Build the jump table
        # TODO: There is some duplication here with the flowgraph visitor
        jump_table = []
        for target_statement in ongoto.targetStatements:
            jump_table.append(target_statement.block.label)
            
        ongoto.switch.accept(self) # Integer on the stack
        self.generator.Emit.Overloads[OpCode, System.Array[Label]](OpCodes.Switch, System.Array[Label](jump_table))
        if ongoto.outOfRangeStatement is not None:
            self.generator.Emit(OpCodes.Br, ongoto.outOfRangeStatement.block.label)
        else:
            on_range_exception_ctor = clr.GetClrType(OwlRuntime.OnRangeException).GetConstructor(System.Array[System.Type]([]))
            assert on_range_exception_ctor
            self.generator.Emit(OpCodes.Newobj, on_range_exception_ctor) # OnRangeException on the stack
            self.generator.Emit(OpCodes.Throw)
            
    def visitLocal(self, local):
        logging.debug("Visiting %s", local)
        #self.checkMark(local)
        if self.__cil_debug:
            self.generator.Emit(OpCodes.Nop)
        
    def visitGoto(self, goto):
        logging.debug("Visiting %s", goto)
        #self.checkMark(goto)
        # No code needs to be generated for GOTO statements here, so the
        # routine which generates code for transferring control from the end
        # of a basic block with out-degree one will do it.
        if self.__cil_debug:
            self.generator.Emit(OpCodes.Nop)
            
    def visitGcol(self, gcol):
        logging.debug("Visiting %s", gcol)
        gcol.mode.accept(self)
        gcol.logicalColour.accept(self)
        if gcol.tint is not None:
            gcol.tint.accept(self)
            gcol_method = self.basicCommandMethod("GcolTint")
        else:
            gcol_method = self.basicCommandMethod("Gcol")
        self.generator.Emit(OpCodes.Call, gcol_method)
            
    def visitAscFunc(self, asc):
        logging.debug("Visiting %s", asc)
        asc.factor.accept(self)
        asc_method = self.basicCommandMethod("Asc")
        self.generator.Emit(OpCodes.Call, asc_method)

    def visitAbsFunc(self, abs):
        logging.debug("Visiting %s", abs)
        abs.factor.accept(self)
        abs_method = getMethod(self.math_type, "Abs", abs.factor.actualType)
        self.generator.Emit(OpCodes.Call, abs_method)
    
    def visitChrStrFunc(self, chr):
        logging.debug("Visiting %s", chr)
        chr.factor.accept(self)
        chr_method = self.basicCommandMethod("Chr")
        self.generator.Emit(OpCodes.Call, chr_method)
        
    def visitRndFunc(self, rnd):
        logging.debug("Visiting %s", rnd)
        if rnd.option is None:
            # Return a four-byte random signed integer between -2147483648 and +2147483647
            self.generator.Emit(OpCodes.Call, self.basicCommandOverloadedMethod("Rnd"))
        else:
            rnd.option.accept(self)
            self.generator.Emit(OpCodes.Call, self.basicCommandOverloadedMethod("Rnd", IntegerOwlType()))
                      
    def visitInstrFunc(self, instr):
        logging.debug("Visiting %s", instr)
        instr.source.accept(self)
        instr.subString.accept(self)
        if instr.startPosition is not None:
            instr.startPosition.accept(self)
            instr_method = self.basicCommandMethod("InstrAt")
        else:
            instr_method = self.basicCommandMethod("Instr")
        self.generator.Emit(OpCodes.Call, instr_method)
    
    def visitLenFunc(self, len_func):
        logging.debug("Visiting %s", len_func)
        len_func.factor.accept(self)
        string_count_method = getMethod(self.string_type, "get_Length")
        self.generator.Emit(OpCodes.Call, string_count_method)
        
    def visitSgnFunc(self, sgn):
        logging.debug("Visiting %s", sgn)
        sgn.factor.accept(self)
        sgn_method = getMethod(self.math_type, "Sign", sgn.factor.actualType)
        self.generator.Emit(OpCodes.Call, sgn_method)
        
    def visitSqrFunc(self, sqr):
        logging.debug("Visiting %s", sqr)
        sqr.factor.accept(self)
        sqr_method = self.basicCommandMethod("Sqr")
        self.generator.Emit(OpCodes.Call, sqr_method)
    
    def visitTrueFunc(self, true):
        emitLdc_I4(self.generator, -1)
        
    def visitFalseFunc(self, false):
        emitLdc_I4(self.generator, 0)
        
    def visitConcatenate(self, concat):
        logging.debug("Visiting %s", concat)
        concat.lhs.accept(self)
        concat.rhs.accept(self)
        string_concat_method = getMethod(self.string_type, "Concat", StringOwlType(), StringOwlType())
        self.generator.Emit(OpCodes.Call, string_concat_method)
        
    def visitLeftStrFunc(self, left_str):
        logging.debug("Visiting %s", left_str)
        left_str.source.accept(self)  # String the the stack
        if left_str.length is not None:
            left_str.length.accept(self)  # Length on the stack
            method = self.basicCommandOverloadedMethod("LeftStr", StringOwlType(), IntegerOwlType())
        else:
            method = self.basicCommandOverloadedMethod("LeftStr", StringOwlType())
        self.generator.Emit(OpCodes.Call, method)
                    
    def visitMidStrFunc(self, mid_str):
        logging.debug("Visiting %s", mid_str)
        mid_str.source.accept(self) # String on the stack
        mid_str.position.accept(self) # 1-based index on stack
        if mid_str.length is not None:
            mid_str.length.accept(self) # length on the stack
            method = self.basicCommandOverloadedMethod("MidStr", StringOwlType(), IntegerOwlType(), IntegerOwlType())
        else:
            method = self.basicCommandOverloadedMethod("MidStr", StringOwlType(), IntegerOwlType())
        self.generator.Emit(OpCodes.Call, method)

    def visitRightStrFunc(self, right_str):
        logging.debug("Visiting %s", right_str)
        right_str.source.accept(self) # String on the stack        
        if right_str.length is not None:
            right_str.length.accept(self)
            method = self.basicCommandOverloadedMethod("RightStr", StringOwlType(), IntegerOwlType())
        else:
            method = self.basicCommandOverloadedMethod("RightStr", StringOwlType())
        self.generator.Emit(OpCodes.Call, method)
        
    def visitPosFunc(self, pos):
        logging.debug("Visiting %s", pos)
        pos_method = self.basicCommandMethod("Pos")
        self.generator.Emit(OpCodes.Call, pos_method)
        
    def visitMode(self, mode):
        logging.debug("Visiting %s", mode)
        #self.checkMark(mode)
        assert mode.number is not None
        # TODO: Extended MODE syntax not yet supported
        mode.number.accept(self)
        mode_method = self.basicCommandMethod("Mode")
        self.generator.Emit(OpCodes.Call, mode_method)
    
    def visitPlot(self, plot):
        if plot.relative:
            assert plot.mode is None
            # PLOT BY x, y is equivalent to PLOT 65, x, y - BB4W only
            emitLdc_I4(self.generator, 65)
        elif plot.mode is None:
            assert plot.relative is None
            # PLOT x,y is equivalent to PLOT 69, x, y
            emitLdc_I4(self.generator, 69)   
        else:
            assert plot.mode is not None
            plot.mode.accept(self)
        plot.xCoord.accept(self)
        plot.yCoord.accept(self)    
        plot_method = self.basicCommandMethod("Plot")
        self.generator.Emit(OpCodes.Call, plot_method)
        
    def visitLongJump(self, long_jump):
        logging.debug("Visiting %s", long_jump)
        #self.checkMark(long_jump)
        long_jump.targetLogicalLine.accept(self) # Target line on the stack
        long_jump_exception_ctor = clr.GetClrType(OwlRuntime.LongJumpException).GetConstructor(System.Array[System.Type]([System.Int32]))
        assert long_jump_exception_ctor
        self.generator.Emit(OpCodes.Newobj, long_jump_exception_ctor) # LongJumpException on the stack
        self.generator.Emit(OpCodes.Throw)
    
    def visitRaise(self, raise_stmt):
        logging.debug("Visiting %s", raise_stmt)
        #self.checkMark(raise_stmt)
        emitLdc_I4(self.generator, self.line_mapper.physicalToLogical(raise_stmt.lineNum)) # Source line on the stack
        exception_type = getattr(OwlRuntime, raise_stmt.type)
        exception_ctor = clr.GetClrType(exception_type).GetConstructor(System.Array[System.Type]([System.Int32]))
        assert exception_ctor
        self.generator.Emit(OpCodes.Newobj, exception_ctor) # LongJumpException on the stack
        self.generator.Emit(OpCodes.Throw)
        
    def visitIntFunc(self, int_func):
        logging.debug("Visiting %s", int_func)
        int_func.factor.accept(self)
        floor_method = getMethod(self.math_type, "Floor", int_func.factor.actualType)
        self.generator.Emit(OpCodes.Call, floor_method)
        self.generator.Emit(OpCodes.Conv_Ovf_I4)
        
    def visitEvalFunc(self, eval_func):
        logging.debug("Visiting %s", eval_func)
        eval_func.factor.accept(self) # String to be EVALed on the stack
        self.generator.Emit(OpCodes.Ldtoken, self.type_builder) # Push the type of the module we are compiling on the stack
        get_type_from_handle_method = self.type_type.GetMethod("GetTypeFromHandle", System.Array[System.Type]([clr.GetClrType(System.RuntimeTypeHandle)]))
        self.generator.Emit(OpCodes.Call, get_type_from_handle_method) # Type on the stack
        self.generator.Emit(OpCodes.Call, self.basicCommandMethod("Eval"))

    def visitTimeValue(self, time_value):
        logging.debug("Visiting %s", time_value)
        get_time_method = self.basicCommandMethod("get_Time")
        self.generator.Emit(OpCodes.Call, get_time_method)
        
                                                                                