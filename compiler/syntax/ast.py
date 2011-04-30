# Abstract Syntax Tree for BBC# Basic

import logging
import re

from ast_meta import AstNode, Node
from options import (TypeOption, IntegerOption, StringOption, BoolOption,
                     FloatOption)
from cfg_vertex import CfgVertex
from typing.type_system import (VoidOwlType, IntegerOwlType, ChannelOwlType,
                                ScalarOwlType, NumericOwlType, StringOwlType,
                                FloatOwlType, AddressOwlType, ByteOwlType,
                                PendingOwlType, ArrayOwlType, ObjectOwlType)
    
class AstStatement(AstNode, CfgVertex):
    formal_type = TypeOption(VoidOwlType())
    actual_type = formal_type
    start_line = IntegerOption() # One-based line number for source level debugging
    end_line = IntegerOption()   # One-based line number for source level debugging
    start_pos = IntegerOption() # Zero-based file offset
    end_pos = IntegerOption()   # Zero-based file offset
    start_column = IntegerOption() # One based column number for source level debugging
    end_column = IntegerOption() # One based column number for source level debugging
        
class Program(AstNode):
    #formal_type = TypeOption(None)
    statements = Node()
            
class StatementList(AstNode):
    formal_type = TypeOption(None)
    statements = [Node()]

    def prepend(self, statement):
        self.statements.insert(0, statement)

    def append(self, statement):
        self.statements.append(statement)
        
    def extend(self, statement_list):
        self.statements.extend(statement_list.statements)
        
class MarkerStatement(AstStatement):
    following_statement = Node()
        
class Beats(AstStatement):
    counter = Node(formalType=IntegerOwlType())
    
class Channel(AstStatement):
    channel = Node(formalType=IntegerOwlType())

class Dim(AstStatement):
    items = Node()
    
class DimList(AstNode):
    formal_type = TypeOption(None)
    items = [Node()]
    
    def append(self, node):
        self.items.append(node)

class AllocateArray(AstStatement):
    identifier = StringOption()
    dimensions = Node()
    
class AllocateBlock(AstStatement):
    identifier = Node()
    size       = Node(formalType=IntegerOwlType())

class Assignment(AstStatement):
    l_value = Node()
    r_value = Node()

class ScalarAssignment(Assignment):
    pass

class ArrayAssignment(Assignment):
    pass

class Increment(AstStatement):
    l_value = Node()
    r_value = Node()

class Decrement(AstStatement):
    l_value = Node()
    r_value = Node()

class Bput(AstStatement):
    channel = Node(formalType=ChannelOwlType())
    data    = Node(formalType=IntegerOwlType())
    # TODO: Whether newline is True or False depends on
    #       the type of data.  If data is a number,
    #       we default to False, if data is a string we
    #       default to True.
    newline = BoolOption(False)

class Call(AstStatement):
    address = Node()    # TODO: AddressOwlType()?
    parameters = Node() # TODO: Needs handling in grammar
    
class Circle(AstStatement):
    x_coord = Node(formalType=IntegerOwlType())
    y_coord = Node(formalType=IntegerOwlType())
    radius  = Node(formalType=IntegerOwlType())
    fill    = BoolOption(False)

class Cls(AstStatement):
    pass

class Clg(AstStatement):
    pass

class Colour(AstStatement):
    colour = Node(formalType=IntegerOwlType())
    tint   = Node(formalType=IntegerOwlType())

class Palette(AstStatement):
    physical_colour = Node(formalType=IntegerOwlType())
    logical_colour  = Node(formalType=IntegerOwlType())
    red             = Node(formalType=IntegerOwlType())
    green           = Node(formalType=IntegerOwlType())
    blue            = Node(formalType=IntegerOwlType())

class Case(AstStatement):
    condition    = Node(ScalarOwlType())
    when_clauses = Node()
    
class WhenClauseList(AstNode):
    clauses = [Node()]
    
    def append(self, when_clause):
        self.clauses.append(when_clause)

class WhenClause(AstNode):
    matches = Node()
    statements = Node()
    
class OtherwiseClause(AstNode):
    statements = Node()

class Close(AstStatement):
    channel = Node(formalType=ChannelOwlType())

class Data(AstStatement):
    data = StringOption()
    
class Rem(AstStatement):
    data = StringOption()

class DefinitionStatement(MarkerStatement):
    name = StringOption()
    formal_parameters = Node()

class DefineFunction(DefinitionStatement):
    "DEF FN"
    return_type = TypeOption(None) # Used to store the return type

class ReturnFromFunction(AstStatement):
    return_value = Node(formalType=ScalarOwlType()) # TODO: Can functions return arrays 

class DefineProcedure(DefinitionStatement):
    "DEF PROC"
    pass

class ReturnFromProcedure(AstStatement):
    pass

class ForToStep(AstStatement):
    identifier = Node()
    first      = Node(formalType=NumericOwlType())
    last       = Node(formalType=NumericOwlType())
    step       = Node(formalType=NumericOwlType())

class Next(AstStatement):
    identifiers = Node()

class Draw(AstStatement):
    "DRAW"
    x_coord = Node(formalType=IntegerOwlType(), description="The x co-ordinate")
    y_coord = Node(formalType=IntegerOwlType(), description="The y co-ordinate")
    relative = BoolOption(False)

class Ellipse(AstStatement):
    x_coord    = Node(formalType=IntegerOwlType())
    y_coord    = Node(formalType=IntegerOwlType())
    semi_major = Node(formalType=IntegerOwlType())
    semi_minor = Node(formalType=IntegerOwlType())
    radians    = Node(formalType=IntegerOwlType())
    fill       = BoolOption(False)

class GenerateError(AstStatement):
    number      = Node(formalType=IntegerOwlType())
    description = Node(formalType=StringOwlType())
    
class ReturnError(AstStatement):
    number      = Node(formalType=IntegerOwlType())
    description = Node(formalType=StringOwlType())      

class End(AstStatement):
    pass

class Envelope(AstStatement):
    n                 = Node(formalType=IntegerOwlType())
    t                 = Node(formalType=IntegerOwlType())
    pitch1            = Node(formalType=IntegerOwlType())
    pitch2            = Node(formalType=IntegerOwlType())
    pitch3            = Node(formalType=IntegerOwlType())
    num_steps_1       = Node(formalType=IntegerOwlType())
    num_steps_2       = Node(formalType=IntegerOwlType())
    num_steps_3       = Node(formalType=IntegerOwlType())
    amplitude_attack  = Node(formalType=IntegerOwlType())
    amplitude_decay   = Node(formalType=IntegerOwlType())
    amplitude_sustain = Node(formalType=IntegerOwlType())
    amplitude_release = Node(formalType=IntegerOwlType())
    target_attack     = Node(formalType=IntegerOwlType())
    target_decay      = Node(formalType=IntegerOwlType())

class Fill(AstStatement):
    x_coord = Node(formalType=IntegerOwlType())
    y_coord = Node(formalType=IntegerOwlType())
    relative = BoolOption(False)

class Gcol(AstStatement):
    mode           = Node(formalType=IntegerOwlType())
    logical_colour = Node(formalType=IntegerOwlType())
    tint           = Node(formalType=IntegerOwlType())

class Goto(AstStatement):
    target_logical_line = Node(formalType=IntegerOwlType())

class OnGoto(AstStatement):
    switch = Node(formalType=IntegerOwlType())
    target_logical_lines = Node()
    out_of_range_clause = Node()

class Gosub(AstStatement):
    target_logical_line = Node(formalType=IntegerOwlType())

class Return(AstStatement):
    pass

class Input(AstStatement):
    # TODO: Needs updating for all INPUT syntax including INPUT LINE
    input_list = Node()
    input_line = BoolOption(False)

class InputFile(AstStatement):
    channel = Node(formalType=ChannelOwlType())
    items = Node()

class InputList(AstNode):
    items = [Node()]

    def append(self, item):
        self.items.append(item)

class InputItem(AstNode):
    item = Node()

class InputManipulator(AstNode):
    manipulator = StringOption()

class Install(AstStatement):
    filename = Node(formalType=StringOwlType())

class If(AstStatement):
    condition = Node(formalType=IntegerOwlType())
    true_clause = Node()
    false_clause = Node()

class LoadLibrary(AstStatement):
    filename = Node(formalType=StringOwlType())

class Local(AstStatement):
    variables = Node()

class Mandel(AstStatement):
    "MANDEL"
    i_coord = Node(formalType=FloatOwlType(), description="The i coordinate")
    j_coord = Node(formalType=FloatOwlType(), description="The j coordinate")

class Move(AstStatement):
    "MOVE"
    x_coord = Node(formalType=IntegerOwlType(), description="The x coordinate")
    y_coord = Node(formalType=IntegerOwlType(), description="The y coordinate")
    relative = BoolOption(False)

class Mode(AstStatement):
    "MODE"
    number         = Node(formalType=IntegerOwlType())
    width          = Node(formalType=IntegerOwlType())
    height         = Node(formalType=IntegerOwlType())
    bits_per_pixel = Node(formalType=IntegerOwlType())
    frame_rate     = Node(formalType=IntegerOwlType()) 

class Mouse(AstStatement):
    "MOUSE"
    x_coord = Node(formalType=IntegerOwlType())
    y_coord = Node(formalType=IntegerOwlType())
    buttons = Node(formalType=IntegerOwlType())
    time    = Node(formalType=IntegerOwlType())

class MouseStep(AstStatement):
    "MOUSE STEP"
    x_coeff = Node(formalType=NumericOwlType())
    y_coeff = Node(formalType=NumericOwlType())

class MouseColour(AstStatement):
    logicalColour = Node(formalType=IntegerOwlType())
    red = Node(formalType=IntegerOwlType())
    green = Node(formalType=IntegerOwlType())
    blue = Node(formalType=IntegerOwlType())

class MousePosition(AstStatement):
    "MOUSE TO"
    x_coord     = Node(formalType=IntegerOwlType())
    y_coord     = Node(formalType=IntegerOwlType())
    moveMouse   = BoolOption(True)
    movePointer = BoolOption(True)

class MousePointer(AstStatement):
    shape       = Node(formalType=IntegerOwlType())
    
class MouseRectangleOn(AstStatement):
    "MOUSE RECTANGLE"
    left   = Node(formalType=IntegerOwlType())
    bottom = Node(formalType=IntegerOwlType())
    right  = Node(formalType=IntegerOwlType())
    top    = Node(formalType=IntegerOwlType())
    
class MouseRectangleOff(AstStatement):
    pass

class On(AstStatement):
    "ON"
    pass

class Off(AstStatement):
    "OFF"
    pass

class Origin(AstStatement):
    "ORIGIN"
    x_coord = Node(formalType=IntegerOwlType())
    y_coord = Node(formalType=IntegerOwlType())

class Oscli(AstStatement):
    "OSCLI"
    command = Node(formalType=StringOwlType())

class Plot(AstStatement):
    "PLOT"
    mode    = Node(formalType=IntegerOwlType())
    x_coord = Node(formalType=IntegerOwlType())
    y_coord = Node(formalType=IntegerOwlType())
    relative = BoolOption(False)

class Point(AstStatement):
    x_coord = Node(formalType=IntegerOwlType())
    y_coord = Node(formalType=IntegerOwlType())
    relative = BoolOption(False)
    
class Print(AstStatement):
    print_list = Node()

class PrintList(AstNode):
    items = [Node()]

    def append(self, item):
        self.items.append(item)

class PrintItem(AstNode):
    item = Node()

class PrintManipulator(AstNode):
    pass

class FormatManipulator(PrintManipulator):
    manipulator = StringOption()

class PrintFile(AstStatement):
    channel = Node(formalType=ChannelOwlType())
    items = Node()

class CallProcedure(AstStatement):
    "PROC"
    name = StringOption()
    actual_parameters = Node()

class Private(AstStatement):
    variables = Node()

class Quit(AstStatement):
    "QUIT"
    code = Node(formalType=IntegerOwlType())

class Rectangle(AstStatement):
    x_coord = Node(formalType=IntegerOwlType())
    y_coord = Node(formalType=IntegerOwlType())
    width   = Node(formalType=IntegerOwlType())
    height  = Node(formalType=IntegerOwlType()) # None ==> square
    fill    = BoolOption(False)

class RectangleBlit(AstStatement):
    x_coord_source = Node(formalType=IntegerOwlType())
    y_coord_source = Node(formalType=IntegerOwlType())
    width          = Node(formalType=IntegerOwlType())
    height         = Node(formalType=IntegerOwlType()) # None ==> square
    x_coord_target = Node(formalType=IntegerOwlType())
    y_coord_target = Node(formalType=IntegerOwlType())

class CopyRectangle(RectangleBlit):
    pass
    
class MoveRectangle(RectangleBlit):
    pass
    
class SwapRectangle(RectangleBlit):
    pass

class Read(AstStatement):
    "READ"
    writables = Node()
    
class Report(AstStatement):
    "REPORT"
    pass

class Repeat(MarkerStatement):
    "REPEAT"
    pass

class Restore(AstStatement):
    "RESTORE"
    target_logical_line = Node(formalType=IntegerOwlType())

class Run(AstStatement):
    "RUN"
    pass

class Sound(AstStatement):
    "SOUND"
    channel   = Node(formalType=IntegerOwlType())
    amplitude = Node(formalType=IntegerOwlType())
    pitch     = Node(formalType=IntegerOwlType())
    duration  = Node(formalType=IntegerOwlType())
    
class Mute(AstStatement):
    mute = BoolOption(False)

class Swap(AstStatement):
    identifier1 = StringOption()
    identifier2 = StringOption()

class Stop(AstStatement):
    pass

class Stereo(AstStatement):
    channel =  Node(formalType=IntegerOwlType())
    position = Node(formalType=IntegerOwlType())

class Sys(AstStatement):
    routine          = Node()
    actual_parameters = Node()
    return_values     = Node()
    flags            = Node()

class Tab(PrintManipulator):
    pass

class TabH(Tab):
    x_coord = Node(formalType=IntegerOwlType())

class TabXY(Tab):
    x_coord = Node(formalType=IntegerOwlType())
    y_coord = Node(formalType=IntegerOwlType())

class Tempo(AstStatement):
    rate = Node(formalType=IntegerOwlType())

class Tint(AstStatement):
    option = Node(formalType=IntegerOwlType())
    tint   = Node(formalType=IntegerOwlType())

class Spc(PrintManipulator):
    spaces = Node(formalType=IntegerOwlType())

class VariableList(AstNode):
    variables = [Node()]

    def append(self, variable):
        self.variables.append(variable)

class Value(AstNode):
    is_l_value = BoolOption(False)

class Variable(Value):
    identifier = StringOption()

class WritableList(AstNode):
    writables = [Node()]

    def append(self, writable):
        self.writables.append(writable)

class Array(AstNode):
    identifier = StringOption()

class Indexer(Value):
    identifier = StringOption()
    indices = Node()

class Until(AstStatement):
    condition = Node()

class Voices(AstStatement):
    number_of_voices = Node()

class Vdu(AstStatement):
    bytes = Node()

class VduList(AstNode):
    items = [Node()]

    def append(self, item):
        self.items.append(item)

class VduItem(AstNode):
    item = Node(formalType=IntegerOwlType())
    length = IntegerOption(default=1)
    
class While(AstStatement):
    condition = Node(formalType=IntegerOwlType())

class Endwhile(AstStatement):
    pass

class Width(AstStatement):
    line_width = Node(formalType=IntegerOwlType())

class Wait(AstStatement):
    centiseconds = Node(formalType=IntegerOwlType())

class ExpressionList(AstNode):
    expressions = [Node()]
    
    def append(self, expr):
        self.expressions.append(expr)

class ActualArgList(AstNode):
    arguments = [Node()]
    
    def append(self, arg):
        self.arguments.append(arg)

class FormalArgList(AstNode):
    arguments = [Node()]

    def append(self, arg):
        self.arguments.append(arg)

class FormalArgument(AstNode):
    argument = Node()

class FormalReferenceArgument(AstNode):
    argument = Node()

class UnaryNumericOperator(AstNode):
    factor = Node(formalType=NumericOwlType())
    
class UnaryPlus(UnaryNumericOperator):
    pass
    
class UnaryMinus(UnaryNumericOperator):
    pass

class UnaryIndirection(Value):
    expression = Node(formalType=AddressOwlType())

class UnaryByteIndirection(UnaryIndirection):
    formal_type = TypeOption(ByteOwlType())
    actual_type = formal_type
    
class UnaryIntegerIndirection(UnaryIndirection):
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type

class UnaryStringIndirection(UnaryIndirection):
    formal_type = TypeOption(StringOwlType())
    actual_type = formal_type

class UnaryFloatIndirection(UnaryIndirection):
    formal_type = TypeOption(FloatOwlType())
    actual_type = formal_type

class DyadicIndirection(Value):
    base   = Node(formalType=AddressOwlType())
    offset = Node(formalType=IntegerOwlType())

class DyadicByteIndirection(DyadicIndirection):
    formal_type = TypeOption(ByteOwlType())
    actual_type = formal_type

class DyadicIntegerIndirection(DyadicIndirection):
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type
    
class Not(AstNode):
    "NOT"
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type
    factor = Node(formalType=IntegerOwlType())

class BinaryOperator(AstNode):
    lhs = Node()
    rhs = Node()

class BinaryNumericOperator(BinaryOperator):
    lhs = Node(formalType=NumericOwlType())
    rhs = Node(formalType=NumericOwlType())

class Plus(BinaryNumericOperator):
    "+"
    pass

class Minus(BinaryNumericOperator):
    "-"
    pass

class Multiply(BinaryNumericOperator):
    "*"
    pass

class Divide(BinaryNumericOperator):
    "/"
    pass

class Power(BinaryNumericOperator):
    "^"
    pass

class MatrixMultiply(BinaryOperator):
    pass

class BinaryIntegerOperator(BinaryOperator):
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type
    lhs = Node(formalType=IntegerOwlType())
    rhs = Node(formalType=IntegerOwlType())

class IntegerDivide(BinaryIntegerOperator):
    pass

class IntegerModulus(BinaryIntegerOperator):
    pass

class RelationalOperator(BinaryOperator):
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type

class Equal(RelationalOperator):
    "="
    pass

class NotEqual(RelationalOperator):
    "<>"
    pass

class LessThan(RelationalOperator):
    "<"
    pass

class LessThanEqual(RelationalOperator):
    "<="
    pass

class GreaterThan(RelationalOperator):
    ">"
    pass

class GreaterThanEqual(RelationalOperator):
    "<"
    pass

class ShiftLeft(BinaryIntegerOperator):
    "<<"
    pass

class ShiftRight(BinaryIntegerOperator):
    ">>"
    pass

class ShiftRightUnsigned(BinaryIntegerOperator):
    "<<<"
    pass

class And(BinaryIntegerOperator):
    "AND"
    pass

class Or(BinaryIntegerOperator):
    "OR"
    pass

class Eor(BinaryIntegerOperator):
    "EOR"
    pass

class AbsFunc(AstNode):
    "ABS"
    formal_type = TypeOption(NumericOwlType())
    factor = Node(formalType=NumericOwlType())

class EndValue(Value):
    "END"
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type
    expression = Node()

class ExtValue(Value):
    "EXT"
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type
    channel = Node()

class HimemValue(Value):
    formal_type = TypeOption(IntegerOwlType()) # TODO: AddressOwlType ?
    actual_type = formal_type

class LomemValue(Value):
    formal_type = TypeOption(IntegerOwlType()) # TODO: AddressOwlType ?
    actual_type = formal_type

class PageValue(Value):
    formal_type = TypeOption(IntegerOwlType()) # TODO: AddressOwlType ?
    actual_type = formal_type

class TimeValue(Value):
    formal_type = TypeOption(IntegerOwlType()) 
    actual_type = formal_type

class TimeStrValue(Value):
    formal_type = TypeOption(StringOwlType())
    actual_type = formal_type

class PtrValue(Value):
    channel = Node(formalType=ChannelOwlType())
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type

class MidStrLValue(Value):
    target = Node(nodeType=Variable, formalType=StringOwlType()) # TODO: This needs to constrained by the type checker to be a Variable : nodeType=Variable ?
    position = Node(formalType=IntegerOwlType())
    length = Node(formalType=IntegerOwlType())
    
class RightStrLValue(Value):
    target = Node(nodeType=Variable, formalType=StringOwlType()) # TODO: This needs to constrained by the type checker to be a Variable : nodeType=Variable ?
    length = Node(formalType=IntegerOwlType())

class LeftStrLValue(Value):
    target = Node(nodeType=Variable, formalType=StringOwlType())
    length = Node(formalType=IntegerOwlType())

class UnaryNumericFunc(AstNode):
    formal_type = TypeOption(FloatOwlType())
    actual_type = formal_type
    factor = Node(formalType=NumericOwlType(), description="The parameter")    

class UserFunc(AstNode):
    formal_type = TypeOption(PendingOwlType())
    actual_type = formal_type
    name = StringOption()
    actual_parameters = Node()
    
class AcsFunc(UnaryNumericFunc):
    "ACS"

class AdvalFunc(AstNode):
    "ADVAL"
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type
    factor = Node(formalType=IntegerOwlType())

class AscFunc(AstNode):
    "ASC"
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type
    factor = Node(formalType=StringOwlType())
    
class AsnFunc(UnaryNumericFunc):
    "ASN"

class AtnFunc(UnaryNumericFunc):
    "ATN"

class BeatFunc(AstNode):
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type

class BeatsFunc(AstNode):
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type

class BgetFunc(AstNode):
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type
    channel = Node()

class ChrStrFunc(AstNode):
    formal_type = TypeOption(StringOwlType())
    actual_type = formal_type
    factor = Node(formalType=IntegerOwlType())

class CosFunc(UnaryNumericFunc):
    "COS"

class CountFunc(AstNode):
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type

class DegFunc(UnaryNumericFunc):
    "DEG"

class DimensionsFunc(AstNode):
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type
    array = Node(nodeType=Variable, formalType=Array)

class DimensionSizeFunc(AstNode):
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type
    array = Node(nodeType=Variable, formalType=Array)
    dimension = Node(formalType=IntegerOwlType())

class EofFunc(AstNode):
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type
    channel = Node(formalType=ChannelOwlType())

class ErlFunc(AstNode):
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type

class ErrFunc(AstNode):
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type

class EvalFunc(AstNode):
    "EVAL"
    formal_type = TypeOption(ObjectOwlType())
    actual_type = formal_type
    factor = Node(formalType=StringOwlType())
    
class ExpFunc(UnaryNumericFunc):
    "EXP"

class FalseFunc(AstNode):
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type

class GetFunc(AstNode):
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type

class GetStrFunc(AstNode):
    formal_type = TypeOption(StringOwlType())
    actual_type = formal_type

class GetStrFileFunc(AstNode):
    formal_type = TypeOption(StringOwlType())
    channel = Node(formalType=ChannelOwlType())

class InkeyFunc(AstNode):
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type
    factor = Node(formalType=IntegerOwlType())

class InkeyStrFunc(AstNode):
    formal_type = TypeOption(StringOwlType())
    actual_type = formal_type
    factor = Node(formalType=IntegerOwlType())

class InstrFunc(AstNode):
    "INSTR"
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type
    source         = Node(formalType=StringOwlType())
    sub_string     = Node(formalType=StringOwlType())
    start_position = Node(formalType=IntegerOwlType())

class IntFunc(AstNode):
    "INT"
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type
    factor = Node(formalType=FloatOwlType())

class LeftStrFunc(AstNode):
    formal_type = TypeOption(StringOwlType())
    actual_type = formal_type
    source = Node()
    length = Node(formalType=IntegerOwlType())

class LenFunc(AstNode):
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type
    factor = Node(formalType=StringOwlType())

class LnFunc(UnaryNumericFunc):
    "LN"

class LogFunc(UnaryNumericFunc):
    "LOG"

class MidStrFunc(AstNode):
    formal_type = TypeOption(StringOwlType())
    actual_type = formal_type
    source   = Node(formalType=StringOwlType())
    position = Node(formalType=IntegerOwlType())
    length   = Node(formalType=IntegerOwlType())
    
class ModeFunc(AstNode):
    formal_type = TypeOption(IntegerOwlType())

class OpeninFunc(AstNode):
    formal_type = TypeOption(ChannelOwlType())
    filename = Node(formalType=StringOwlType())

class OpenoutFunc(AstNode):
    formal_type = TypeOption(ChannelOwlType())
    filename = Node(formalType=StringOwlType())

class OpenupFunc(AstNode):
    formal_type = TypeOption(ChannelOwlType())
    filename = Node(formalType=StringOwlType())

class PosFunc(AstNode):
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type

class PiFunc(AstNode):
    formal_type = TypeOption(FloatOwlType())
    actual_type = formal_type

class PointFunc(AstNode):
    formal_type = TypeOption(IntegerOwlType())
    x_coord = Node(formalType=IntegerOwlType())
    y_coord = Node(formalType=IntegerOwlType())

class QuitFunc(AstNode):
    "QUIT"
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type
    
class RadFunc(UnaryNumericFunc):
    "RAD"

class ReadFunc(AstNode):
    "READ"
    formal_type = TypeOption(ScalarOwlType())
    actual_type = formal_type

class ReportStrFunc(AstNode):
    "REPORT$"
    formal_type = TypeOption(StringOwlType())
    actual_type = formal_type

class RightStrFunc(AstNode):
    formal_type = TypeOption(StringOwlType())
    actual_type = formal_type
    source = Node(formalType=StringOwlType())
    length = Node(formalType=IntegerOwlType())

class RndFunc(AstNode):
    "RND"
    # A minor change from BBC BASIC. In BBC BASIC RND(x) can return
    # either a float or integer.  In OWL BASIC we always return a
    # 64-bit float.
    formal_type = TypeOption(FloatOwlType()) 
    actual_type = formal_type
    option = Node(formalType=IntegerOwlType())

class SinFunc(UnaryNumericFunc):
    "SIN"

class SgnFunc(AstNode):
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type
    factor = Node(formalType=NumericOwlType())

class SqrFunc(UnaryNumericFunc):
    "SQR"

class StrStringFunc(AstNode):
    formal_type = TypeOption(StringOwlType())
    actual_type = formal_type
    base   = IntegerOption(10)
    factor = Node(formalType=NumericOwlType())

class Sum(AstNode):
    formal_type = TypeOption(IntegerOwlType())
    array = Node(formalType=ArrayOwlType())

class SumLenFunc(AstNode):
    formal_type = TypeOption(IntegerOwlType())
    array = Node(formalType=ArrayOwlType())

class TanFunc(UnaryNumericFunc):
    "TAN"

class TempoFunc(AstNode):
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type

class TintFunc(AstNode):
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type
    xCoord = Node(formalType=IntegerOwlType())
    yCoord = Node(formalType=IntegerOwlType())
    
class TopFunc(AstNode):
    formal_type = TypeOption(IntegerOwlType()) # TODO: AddressOwlType?
    actual_type = formal_type

class TrueFunc(AstNode):
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type

class ValFunc(AstNode):
    formal_type = TypeOption(FloatOwlType())
    actual_type = formal_type
    factor = Node(formalType=StringOwlType())

class VposFunc(AstNode):
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type

class WidthFunc(AstNode):
    formal_type = TypeOption(IntegerOwlType())
    actual_type = formal_type

class Line(AstStatement):
    x1_coord = Node(formalType=IntegerOwlType())
    y1_coord = Node(formalType=IntegerOwlType())
    x2_coord = Node(formalType=IntegerOwlType())
    y2_coord = Node(formalType=IntegerOwlType())

class LiteralString(AstNode):
    actual_type = TypeOption(StringOwlType())
    value = StringOption()

class LiteralInteger(AstNode):
    actual_type = TypeOption(IntegerOwlType())
    value = IntegerOption()

class LiteralFloat(AstNode):
    actual_type = TypeOption(FloatOwlType())
    value = FloatOption()

# Implicit AST nodes
class Concatenate(AstNode):
    formal_type = TypeOption(StringOwlType())
    actual_type = formal_type
    lhs = Node(formalType=StringOwlType())
    rhs = Node(formalType=StringOwlType())

class Cast(AstNode):
    "Implicit Conversion"
    formal_type = TypeOption()
    source_type = TypeOption()
    target_type = TypeOption()
    value = Node()
    
class Raise(AstStatement):
    "Raise exception"
    type = StringOption()
    
class LongJump(AstStatement):
    "Long jump"
    target_logical_line = Node(formalType=IntegerOwlType())

class StarCommand(AstStatement):
    command = StringOption()
