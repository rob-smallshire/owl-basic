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
from bbc_ast import *
from ast_utils import findNode
import cts
import errors
from emitters import *
from symbol_tables import hasSymbolTableLookup

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
        
        # Pending rvalue - used using generation of assignment statements
        self.__pending_rvalue = None
        
        # Get the type of OwnRuntime.BasicCommand so we can retrieve methods
        self.basic_commands_type = clr.GetClrType(OwlRuntime.BasicCommands)
        self.memory_map_type = clr.GetClrType(OwlRuntime.MemoryMap)
        self.string_type = clr.GetClrType(System.String)
        self.console_type = clr.GetClrType(System.Console)
        self.generator = self.method_builder.GetILGenerator()
        self.generator.Emit(OpCodes.Nop) # Every method needs at least one OpCode

        node = entry_point_node
        while True:
            node = node.accept(self)
            if node is None:
                break
            
        if isinstance(entry_point_node, DefineFunction):
            emitLdc_I4(self.generator, 0)
            self.generator.Emit(OpCodes.Ret) # Functions must return something

    def generatePendingRValue(self):
        assert self.__pending_rvalue
        self.__pending_rvalue.accept(self)
        self.__pending_rvalue = None

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
    
    def convertClrToOwlBool(self):
        '''
        Convert the CLR bool value on the stack (0 or 1) to an OWL BASIC
        integer on the stack (0 or -1)
        '''
        self.generator.Emit(OpCodes.Neg)
    
    def visitAstNode(self, node):
        raise CodeGenerationError("Visiting unhandled node %s" % node)
    
    def visitAstStatement(self, statement):
        raise CodeGenerationError("Visiting unhandled statement %s" % statement)
    
    def visitData(self, data):
        return self.successorOf(data)
        
    def successorOf(self, node):
        assert(len(node.outEdges) <= 1)
        if len(node.outEdges) == 0:
            return None
        return node.outEdges[0]
        
    def visitAssignment(self, assignment):
        logging.debug("Visiting %s", assignment)
        # The code for generating the rvalue may need to be interleaved
        # with the code for generating the lvalue, in cases where the
        # lvalue is an assignment to an array element or an indirection
        # operator.  To handle these cases, we store a reference ot the
        # rvalue in this visitor and generate the lvalue.  We expect
        # the lvalue generator to also generate the code for the rvalue at
        # the appropriate point, and then set the stored rvalue in the
        # visitor to None. 
        
        self.__pending_rvalue = assignment.rValue # Store the rvalue
        assignment.lValue.accept(self) # Store the top of the stack into the lValue
        assert self.__pending_rvalue is None # Check that the rvalue has been used
        return self.successorOf(assignment)
                
    def visitVariable(self, variable):
        logging.debug("Visiting %s", variable)
        name = variable.identifier
        logging.debug("identifier = %s", name)
        symbol_node = findNode(variable, hasSymbolTableLookup)
        symbol = symbol_node.symbolTable.lookup(name)
        assert symbol is not None
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
        if cast.sourceType is IntegerType:
            if cast.targetType is FloatType:
                self.generator.Emit(OpCodes.Conv_R8)
                return
        elif cast.sourceType is FloatType:
            if cast.targetType is IntegerType:
                self.generator.Emit(OpCodes.Conv_Ovf_I4)
                return
            if cast.targetType is PtrType:
                self.generator.Emit(OpCodes.Conv_Ovf_I)
                return
            
        errors.internal("Unsupported cast from %s to %s" % (cast.sourceType, cast.targetType))
                
    def visitLiteralInteger(self, literal_integer):
        logging.debug("Visiting %s", literal_integer)
        logging.debug("value = %s", literal_integer.value)
        emitLdc_I4(self.generator, literal_integer.value)
    
    def visitVdu(self, vdu):
        logging.debug("Visiting %s", vdu)
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
            logging.internal("TODO: Unhandled multiple item VDU")
            return None
        return self.successorOf(vdu)
    
    def visitCls(self, cls):
        logging.debug("Visiting %s", cls)
        self.generator.Emit(OpCodes.Call, self.basicCommandMethod('Cls'))
        return self.successorOf(cls)
    
    def visitDefineProcedure(self, defproc):
        logging.debug("Visiting %s", defproc)
        # Generate the 
                  
    def visitCallProcedure(self, call_proc):
        logging.debug("Visiting %s", call_proc)
        logging.debug("name = %s", call_proc.name)
        
        # TODO: Call the procedure
        proc_method_info = self.lookupMethod(call_proc.name)
        print proc_method_info
        # TODO: Push the procedure call arguments onto the stack
        for actual_parameter in call_proc.actualParameters:
            actual_parameter.accept(self)
        
        self.generator.Emit(OpCodes.Call, proc_method_info)
        return self.successorOf(call_proc)
        
    def visitRestore(self, restore):
        # TODO: Can we RESTORE to lines which don't contain DATA?
        logging.debug("Visiting %s", restore)
        logging.debug("target_logical_line = %s", restore.targetLogicalLine)
        # Lookup the data pointer value for this line number
        self.generator.Emit(OpCodes.Ldsfld, self.assembly_generator.data_line_number_map_field)         # Load the dictionary onto the stack
        restore.targetLogicalLine.accept(self) # Push the line number onto the stack
        get_item_method_info = cts.int_int_dictionary_type.GetMethod('get_Item')
        self.generator.Emit(OpCodes.Call, get_item_method_info) # Call get_Item and the put the new data point result on the stack
        self.generator.Emit(OpCodes.Stsfld, self.assembly_generator.data_index_field)
        return self.successorOf(restore)
    
    def visitRepeat(self, repeat):
        logging.debug("Visiting = %s", repeat)
        repeat.label = self.generator.DefineLabel()
        self.generator.MarkLabel(repeat.label)
        return self.successorOf(repeat)
        
    def visitUntil(self, until):
        logging.debug("Visiting ", until)
        if len(until.backEdges) != 0:
            assert len(until.backEdges) == 1
            # Correlated NEXT
            repeat = until.backEdges[0]
            logging.debug("UNTIL correlates with %s", repeat)
            until.condition.accept(self)            # Push the condition onto the stack
            self.generator.Emit(OpCodes.Brfalse_S, repeat.label)  # Branch if false
        else:
            # Non-correlated UNTIL
            errors.internal("TODO: Non-correlated UNTIL")
            
        return self.successorOf(until)    
        
    def visitForToStep(self, for_to_step):
        # TODO: Future optimizations
        # - if STEP is a constant we can simplify the test depending on its sign
        # - if the values are ints we can convert the type of the counter to an int
        # - if last is a constant its worth convert <= last into < last + 1 or the
        #   reverse, if we know the sign of step
        
        # TODO: Could probably hit most common cases STEP == +1 with completely different
        #       code gen FOR i% = 0 TO 9
        
        logging.debug("Visiting %s", for_to_step)

        # Load the initial counter value onto the stack
        for_to_step.first.accept(self)

        # Store in the loop counter variable
        name = for_to_step.identifier.identifier
        logging.debug("counter identifier = %s", name)
        counter_symbol = for_to_step.symbolTable.lookup(name)
        assert counter_symbol is not None
        logging.debug(repr(counter_symbol))
        counter_symbol.storeEmitter(self.generator)
        
        # Evaluate the last value and store in an unnamed local
        last_value_local = self.generator.DeclareLocal(cts.symbolType(counter_symbol))
        for_to_step.last.accept(self)
        self.generator.Emit(OpCodes.Stloc, last_value_local)
        
        # Evaluate the step value and store in an unnamed local
        step_value_local = self.generator.DeclareLocal(cts.symbolType(counter_symbol))
        for_to_step.step.accept(self)
        self.generator.Emit(OpCodes.Stloc, step_value_local)
                        
        # The loop body goes in here - later, but first...
        loop_body_label = self.generator.DefineLabel()
        self.generator.MarkLabel(loop_body_label)
        
        # Define a function (closure) which can be called later to generate
        # the code for the corresponding NEXT statements
        def correspondingNext():
            # Increment the counter
            self.generator.Emit(OpCodes.Ldloc, step_value_local)    # Load the STEP value
            counter_symbol.loadEmitter(self.generator)              # Load the counter
            self.generator.Emit(OpCodes.Add)                        # Add
            counter_symbol.storeEmitter(self.generator)             # Load the counter # Store the counter
            
            # Check the sign of the step value
            self.generator.Emit(OpCodes.Ldloc, step_value_local) # Load the STEP value
            emitLdc_I4(self.generator, 0)                        # Push zero on the stack
            
            positive_step_label = self.generator.DefineLabel()   
            self.generator.Emit(OpCodes.Bgt_S, positive_step_label)      # if step > 0 jump to positive_step_label
            
            # step is negative - implement >= as NOT <
            counter_symbol.loadEmitter(self.generator)              # Load the counter
            self.generator.Emit(OpCodes.Ldloc, last_value_local)    # Load the last value
            self.generator.Emit(OpCodes.Clt)                        # Compare less-than
            self.generator.Emit(OpCodes.Not)                        # Not 
            
            loop_back_label = self.generator.DefineLabel()
            self.generator.Emit(OpCodes.Br_S, loop_back_label)
            
            # step is positive - implement <= as NOT >
            self.generator.MarkLabel(positive_step_label)
            counter_symbol.loadEmitter(self.generator)              # Load the counter
            self.generator.Emit(OpCodes.Ldloc, last_value_local)    # Load the last value
            self.generator.Emit(OpCodes.Cgt)                        # Compare greater-than
            self.generator.Emit(OpCodes.Not)                        # Not 
            
            # loop back if not finished
            self.generator.MarkLabel(loop_back_label)
            self.generator.Emit(OpCodes.Brtrue, loop_body_label)
        
        # Attach the closure to the for_to_step object for later use
        for_to_step.generateNext = correspondingNext
        return self.successorOf(for_to_step)
    
    def visitNext(self, next):
        logging.debug("Visiting %s", next)
        if  len(next.backEdges) != 0:
            assert len(next.backEdges) == 1
            # Correlated NEXT
            for_to_step = next.backEdges[0]
            logging.debug("NEXT correlates with %s", for_to_step)
            for_to_step.generateNext()
        else:
            # Non-correlated NEXT
            errors.internal("TODO: Non-correlated NEXT")
        return self.successorOf(next)
         
    
    def visitReadFunc(self, read_func):
        # Determine the type of the value and dispatch appropriately
        # Read the DATA, evaluate the expression in the context of the
        # value required, and place the value of the stack.
        logging.debug("Visiting %s", read_func)
        # TODO: Convert IndexOutOfRangeException to NoDataException
        # Get the DATA as a string
        self.generator.Emit(OpCodes.Ldsfld, self.assembly_generator.data_field) # Load the DATA array onto the stack
        self.generator.Emit(OpCodes.Ldsfld, self.assembly_generator.data_index_field) # Load the DATA index onto the stack
        self.generator.Emit(OpCodes.Dup) # Duplicate the DATA index
        emitLdc_I4(self.generator, 1)    # Load 1 onto the stack
        self.generator.Emit(OpCodes.Add) # Increment
        self.generator.Emit(OpCodes.Stsfld, self.assembly_generator.data_index_field) # Store the incremented DATA index
        self.generator.Emit(OpCodes.Ldelem_Ref) # Push the DATA element (a string) onto the stack

        # TODO: Convert to the required type
        system_convert_type = clr.GetClrType(System.Convert)
        if read_func.actualType is ByteType:
            conversion_method = system_convert_type.GetMethod("ToByte", System.Array[System.Type]([clr.GetClrType(str)]))
        elif read_func.actualType is IntegerType:
            conversion_method = system_convert_type.GetMethod("ToInt32", System.Array[System.Type]([clr.GetClrType(str)]))
        elif read_func.actualType is FloatType:
            conversion_method = system_convert_type.GetMethod("ToDouble", System.Array[System.Type]([clr.GetClrType(str)]))
        else:
            conversion_method = None
        # TODO: etc
        
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
            print dyadic.base.formalType
            if dyadic.base.formalType is PtrType:
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
                
            elif dyadic.base.formalType is ByteArrayType:
                # Writing into a byte array
                # TODO: get the array onto the stack
                pass
            # TODO: Index and write into the array
        else:
            # Read from the location and push onto the stack
            logging.critical("TODO: Dyadic byte indirection r-value")
            # Are we reading from a block or directly from memory?
        
    def visitPrint(self, print_stmt):
        logging.debug("Visiting %s", print_stmt)
        # Convert each print item into a call to the runtime library
        logging.debug("print list = %s", print_stmt.printList)
        suppress_newline = False
        
        if print_stmt.printList is not None:
            for print_item in print_stmt.printList:
                item = print_item.item
                item.accept(self)
                if not isinstance(item, PrintManipulator):
                    print item
                    print item.formalType
                    print item.actualType
                    print_method = self.basic_commands_type.GetMethod("Print", System.Array[System.Type]([cts.mapType(item.actualType)]))
                    self.generator.Emit(OpCodes.Call, print_method)
                
            if len(print_stmt.printList) > 0:
                last_item = print_stmt.printList[-1].item
                if isinstance(last_item, PrintManipulator) and last_item.manipulator == ';':
                    suppress_newline = True
                    
        if not suppress_newline:
            self.generator.Emit(OpCodes.Call, self.basicCommandMethod('NewLine'))
            
        return self.successorOf(print_stmt)
                   
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
        # TODO throw an exception signalling END and modify the main method
        # to catch this exception and exit gracefully
        logging.critical("TODO: Throw an EndException")
        return self.successorOf(end)
    
    def visitUnaryMinus(self, unary_minus):
        logging.debug("Visiting %s", unary_minus)
        unary_minus.factor.accept(self)
        self.generator.Emit(OpCodes.Neg)
    
    def visitMultiply(self, multiply):
        logging.debug("Visiting %s", multiply)
        # TODO: Deal with unknown types (e.g. Object)
        # TODO: Factor out for BinaryNumericOperators
        multiply.lhs.accept(self)
        multiply.rhs.accept(self)
        self.generator.Emit(OpCodes.Mul)
                    
    def visitEqual(self, operator):
        logging.debug("Visiting %s", operator)
        operator.lhs.accept(self) # Lhs on the stack
        operator.rhs.accept(self) # Rhs on the stack
        
        if binaryTypeMatch(operator, NumericType, NumericType):
            self.generator.Emit(OpCodes.Ceq)
            self.convertClrToOwlBool()
        elif binaryTypeMatch(operator, StringType, StringType):
            string_equals_method = self.string_type.GetMethod("Equals", System.Array[System.Type]([cts.mapType(StringType),
                                                                                                   cts.mapType(StringType)]))
            self.generator.Emit(OpCodes.Call, string_equals_method) 
            self.convertClrToOwlBool()
        elif binaryTypeMatch(operator, ObjectType, Type) or \
             binaryTypeMatch(operator, Type, ObjectType):
            equal_method = self.basic_commands_type.GetMethod("Equal",
                                                              System.Array[System.Type]([cts.mapType(operator.lhs.actualType),
                                                                                         cts.mapType(operator.rhs.actualType)]))
            self.generator.Emit(OpCodes.Call, equal_method)
            
    def visitNotEqual(self, operator):
        logging.debug("Visiting %s", operator)
        operator.lhs.accept(self) # Lhs on the stack
        operator.rhs.accept(self) # Rhs on the stack
        
        if binaryTypeMatch(operator, NumericType, NumericType):
            self.generator.Emit(OpCodes.Ceq)
            emitLdc_I4(self.generator, 1) # 0 ==> -1, 1 ==> 0
            self.generator.Emit(OpCodes.Sub)
        elif binaryTypeMatch(operator, StringType, StringType):
            self.generator.Emit(OpCodes.Call, "String.Equals")
            emitLdc_I4(self.generator, 1) # 0 ==> -1, 1 ==> 0
            self.generator.Emit(OpCodes.Sub)
        elif binaryTypeMatch(operator, ObjectType, Type) or \
             binaryTypeMatch(operator, Type, ObjectType):
            equal_method = self.basic_commands_type.GetMethod("NotEqual",
                                                              System.Array[System.Type]([cts.mapType(operator.lhs.actualType),
                                                                                         cts.mapType(operator.rhs.actualType)]))
            self.generator.Emit(OpCodes.Call, equal_method)
        
        
         
        