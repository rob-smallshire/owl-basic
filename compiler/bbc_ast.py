# Abstract Syntax Tree for BBC# Basic

import logging
import re

from ast_meta import *
from bbc_types import *
from cfg_vertex import *
    
class AstStatement(AstNode, CfgVertex):
    formal_type = TypeOption(VoidType)
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
    counter = Node(formalType=IntegerType)
    
class Channel(AstStatement):
    channel = Node(formalType=IntegerType)

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
    size       = Node(formalType=IntegerType)

class Assignment(AstStatement):
    l_value = Node()
    r_value = Node()
    
class Increment(AstStatement):
    l_value = Node()
    r_value = Node()

class Decrement(AstStatement):
    l_value = Node()
    r_value = Node()

class Bput(AstStatement):
    channel = Node(formalType=ChannelType)
    data    = Node(formalType=IntegerType)
    # TODO: Whether newline is True or False depends on
    #       the type of data.  If data is a number,
    #       we default to False, if data is a string we
    #       default to True.
    newline = BoolOption(False)

class Call(AstStatement):
    address = Node()    # TODO: PtrType?
    parameters = Node() # TODO: Needs handling in grammar
    
class Circle(AstStatement):
    x_coord = Node(formalType=IntegerType)
    y_coord = Node(formalType=IntegerType)
    radius  = Node(formalType=IntegerType)
    fill    = BoolOption(False)

class Cls(AstStatement):
    pass

class Clg(AstStatement):
    pass

class Colour(AstStatement):
    colour = Node(formalType=IntegerType)
    tint   = Node(formalType=IntegerType)

class Palette(AstStatement):
    physical_colour = Node(formalType=IntegerType)
    logical_colour  = Node(formalType=IntegerType)
    red             = Node(formalType=IntegerType)
    green           = Node(formalType=IntegerType)
    blue            = Node(formalType=IntegerType)

class Case(AstStatement):
    condition    = Node(ScalarType)
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
    channel = Node(formalType=ChannelType)

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
    return_value = Node(formalType=ScalarType) # TODO: Can functions return arrays 

class DefineProcedure(DefinitionStatement):
    "DEF PROC"
    pass

class ReturnFromProcedure(AstStatement):
    pass

class ForToStep(AstStatement):
    identifier = Node()
    first      = Node(formalType=NumericType)
    last       = Node(formalType=NumericType)
    step       = Node(formalType=NumericType)

class Next(AstStatement):
    identifiers = Node()

class Draw(AstStatement):
    "DRAW"
    x_coord = Node(formalType=IntegerType, description="The x co-ordinate")
    y_coord = Node(formalType=IntegerType, description="The y co-ordinate")
    relative = BoolOption(False)

class Ellipse(AstStatement):
    x_coord    = Node(formalType=IntegerType)
    y_coord    = Node(formalType=IntegerType)
    semi_major = Node(formalType=IntegerType)
    semi_minor = Node(formalType=IntegerType)
    radians    = Node(formalType=IntegerType)
    fill       = BoolOption(False)

class GenerateError(AstStatement):
    number      = Node(formalType=IntegerType)
    description = Node(formalType=StringType)
    
class ReturnError(AstStatement):
    number      = Node(formalType=IntegerType)
    description = Node(formalType=StringType)      

class End(AstStatement):
    pass

class Envelope(AstStatement):
    n                 = Node(formalType=IntegerType)
    t                 = Node(formalType=IntegerType)
    pitch1            = Node(formalType=IntegerType)
    pitch2            = Node(formalType=IntegerType)
    pitch3            = Node(formalType=IntegerType)
    num_steps_1       = Node(formalType=IntegerType)
    num_steps_2       = Node(formalType=IntegerType)
    num_steps_3       = Node(formalType=IntegerType)
    amplitude_attack  = Node(formalType=IntegerType)
    amplitude_decay   = Node(formalType=IntegerType)
    amplitude_sustain = Node(formalType=IntegerType)
    amplitude_release = Node(formalType=IntegerType)
    target_attack     = Node(formalType=IntegerType)
    target_decay      = Node(formalType=IntegerType)

class Fill(AstStatement):
    x_coord = Node(formalType=IntegerType)
    y_coord = Node(formalType=IntegerType)
    relative = BoolOption(False)

class Gcol(AstStatement):
    mode           = Node(formalType=IntegerType)
    logical_colour = Node(formalType=IntegerType)
    tint           = Node(formalType=IntegerType)

class Goto(AstStatement):
    target_logical_line = Node(formalType=IntegerType)

class OnGoto(AstStatement):
    switch = Node(formalType=IntegerType)
    target_logical_lines = Node()
    out_of_range_clause = Node()

class Gosub(AstStatement):
    target_logical_line = Node(formalType=IntegerType)

class Return(AstStatement):
    pass

class Input(AstStatement):
    # TODO: Needs updating for all INPUT syntax including INPUT LINE
    input_list = Node()
    input_line = BoolOption(False)

class InputFile(AstStatement):
    channel = Node(formalType=ChannelType)
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
    filename = Node(formalType=StringType)

class If(AstStatement):
    condition = Node(formalType=IntegerType)
    true_clause = Node()
    false_clause = Node()

class LoadLibrary(AstStatement):
    filename = Node(formalType=StringType)

class Local(AstStatement):
    variables = Node()

class Mandel(AstStatement):
    "MANDEL"
    i_coord = Node(formalType=FloatType, description="The i coordinate")
    j_coord = Node(formalType=FloatType, description="The j coordinate")

class Move(AstStatement):
    "MOVE"
    x_coord = Node(formalType=IntegerType, description="The x coordinate")
    y_coord = Node(formalType=IntegerType, description="The y coordinate")
    relative = BoolOption(False)

class Mode(AstStatement):
    "MODE"
    number         = Node(formalType=IntegerType)
    width          = Node(formalType=IntegerType)
    height         = Node(formalType=IntegerType)
    bits_per_pixel = Node(formalType=IntegerType)
    frame_rate     = Node(formalType=IntegerType) 

class Mouse(AstStatement):
    "MOUSE"
    x_coord = Node(formalType=IntegerType)
    y_coord = Node(formalType=IntegerType)
    buttons = Node(formalType=IntegerType)
    time    = Node(formalType=IntegerType)

class MouseStep(AstStatement):
    "MOUSE STEP"
    x_coeff = Node(formalType=NumericType)
    y_coeff = Node(formalType=NumericType)

class MouseColour(AstStatement):
    logicalColour = Node(formalType=IntegerType)
    red = Node(formalType=IntegerType)
    green = Node(formalType=IntegerType)
    blue = Node(formalType=IntegerType)

class MousePosition(AstStatement):
    "MOUSE TO"
    x_coord     = Node(formalType=IntegerType)
    y_coord     = Node(formalType=IntegerType)
    moveMouse   = BoolOption(True)
    movePointer = BoolOption(True)

class MousePointer(AstStatement):
    shape       = Node(formalType=IntegerType)
    
class MouseRectangleOn(AstStatement):
    "MOUSE RECTANGLE"
    left   = Node(formalType=IntegerType)
    bottom = Node(formalType=IntegerType)
    right  = Node(formalType=IntegerType)
    top    = Node(formalType=IntegerType)
    
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
    x_coord = Node(formalType=IntegerType)
    y_coord = Node(formalType=IntegerType)

class Oscli(AstStatement):
    "OSCLI"
    command = Node(formalType=StringType)

class Plot(AstStatement):
    "PLOT"
    mode    = Node(formalType=IntegerType)
    x_coord = Node(formalType=IntegerType)
    y_coord = Node(formalType=IntegerType)
    relative = BoolOption(False)

class Point(AstStatement):
    x_coord = Node(formalType=IntegerType)
    y_coord = Node(formalType=IntegerType)
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
    channel = Node(formalType=ChannelType)
    items = Node()

class CallProcedure(AstStatement):
    "PROC"
    name = StringOption()
    actual_parameters = Node()

class Private(AstStatement):
    variables = Node()

class Quit(AstStatement):
    "QUIT"
    code = Node(formalType=IntegerType)

class Rectangle(AstStatement):
    x_coord = Node(formalType=IntegerType)
    y_coord = Node(formalType=IntegerType)
    width   = Node(formalType=IntegerType)
    height  = Node(formalType=IntegerType) # None ==> square
    fill    = BoolOption(False)

class RectangleBlit(AstStatement):
    x_coord_source = Node(formalType=IntegerType)
    y_coord_source = Node(formalType=IntegerType)
    width          = Node(formalType=IntegerType)
    height         = Node(formalType=IntegerType) # None ==> square
    x_coord_target = Node(formalType=IntegerType)
    y_coord_target = Node(formalType=IntegerType)

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
    target_logical_line = Node(formalType=IntegerType)

class Sound(AstStatement):
    "SOUND"
    channel   = Node(formalType=IntegerType)
    amplitude = Node(formalType=IntegerType)
    pitch     = Node(formalType=IntegerType)
    duration  = Node(formalType=IntegerType)
    
class Mute(AstStatement):
    mute = BoolOption(False)

class Swap(AstStatement):
    identifier1 = StringOption()
    identifier2 = StringOption()

class Stop(AstStatement):
    pass

class Stereo(AstStatement):
    channel =  Node(formalType=IntegerType)
    position = Node(formalType=IntegerType)

class Sys(AstStatement):
    routine          = Node()
    actual_parameters = Node()
    return_values     = Node()
    flags            = Node()

class Tab(PrintManipulator):
    pass

class TabH(Tab):
    x_coord = Node(formalType=IntegerType)

class TabXY(Tab):
    x_coord = Node(formalType=IntegerType)
    y_coord = Node(formalType=IntegerType)

class Tempo(AstStatement):
    rate = Node(formalType=IntegerType)

class Tint(AstStatement):
    option = Node(formalType=IntegerType)
    tint   = Node(formalType=IntegerType)

class Spc(PrintManipulator):
    spaces = Node(formalType=IntegerType)

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
    item = Node(formalType=IntegerType)
    length = IntegerOption(default=1)
    
class While(AstStatement):
    condition = Node(formalType=IntegerType)

class Endwhile(AstStatement):
    pass

class Width(AstStatement):
    line_width = Node(formalType=IntegerType)

class Wait(AstStatement):
    centiseconds = Node(formalType=IntegerType)

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
    factor = Node(formalType=NumericType)
    
class UnaryPlus(UnaryNumericOperator):
    pass
    
class UnaryMinus(UnaryNumericOperator):
    pass

class UnaryIndirection(Value):
    expression = Node(formalType=PtrType)

class UnaryByteIndirection(UnaryIndirection):
    formal_type = TypeOption(ByteType)
    actual_type = formal_type
    
class UnaryIntegerIndirection(UnaryIndirection):
    formal_type = TypeOption(IntegerType)
    actual_type = formal_type

class UnaryStringIndirection(UnaryIndirection):
    formal_type = TypeOption(StringType)
    actual_type = formal_type

class UnaryFloatIndirection(UnaryIndirection):
    formal_type = TypeOption(FloatType)
    actual_type = formal_type

class DyadicIndirection(Value):
    base   = Node(formalType=PtrType)
    offset = Node(formalType=IntegerType)

class DyadicByteIndirection(DyadicIndirection):
    formal_type = TypeOption(ByteType)
    actual_type = formal_type

class DyadicIntegerIndirection(DyadicIndirection):
    formal_type = TypeOption(IntegerType)
    actual_type = formal_type
    
class Not(AstNode):
    "NOT"
    formal_type = TypeOption(IntegerType)
    actual_type = formal_type
    factor = Node(formalType=IntegerType)

class BinaryOperator(AstNode):
    lhs = Node()
    rhs = Node()

class BinaryNumericOperator(BinaryOperator):
    lhs = Node(formalType=NumericType)
    rhs = Node(formalType=NumericType)

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
    formal_type = TypeOption(IntegerType)
    actual_type = formal_type
    lhs = Node(formalType=IntegerType)
    rhs = Node(formalType=IntegerType)

class IntegerDivide(BinaryIntegerOperator):
    pass

class IntegerModulus(BinaryIntegerOperator):
    pass

class RelationalOperator(BinaryOperator):
    formal_type = TypeOption(IntegerType)
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
    formal_type = TypeOption(NumericType)
    factor = Node(formalType=NumericType)

class EndValue(Value):
    "END"
    formal_type = TypeOption(IntegerType)
    expression = Node()

class ExtValue(Value):
    "EXT"
    formal_type = TypeOption(IntegerType)
    channel = Node()

class HimemValue(Value):
    formal_type = TypeOption(IntegerType)

class LomemValue(Value):
    formal_type = TypeOption(IntegerType)

class PageValue(Value):
    formal_type = TypeOption(IntegerType)
    pass

class TimeValue(Value):
    formal_type = TypeOption(IntegerType)
    pass

class TimeStrValue(Value):
    formal_type = TypeOption(StringType)
    pass

class PtrValue(Value):
    channel = Node(formalType=ChannelType)

class MidStrLValue(Value):
    target = Node(nodeType=Variable, formalType=StringType) # TODO: This needs to constrained by the type checker to be a Variable : nodeType=Variable ?
    position = Node(formalType=IntegerType)
    length = Node(formalType=IntegerType)
    
class RightStrLValue(Value):
    target = Node(nodeType=Variable, formalType=StringType) # TODO: This needs to constrained by the type checker to be a Variable : nodeType=Variable ?
    length = Node(formalType=IntegerType)

class LeftStrLValue(Value):
    target = Node(nodeType=Variable, formalType=StringType)
    length = Node(formalType=IntegerType)

class UnaryNumericFunc(AstNode):
    formal_type = TypeOption(FloatType)
    actual_type = formal_type
    factor = Node(formalType=NumericType, description="The parameter")    

class UserFunc(AstNode):
    formal_type = TypeOption(PendingType)
    actual_type = formal_type
    name = StringOption()
    actual_parameters = Node()
    
class AcsFunc(UnaryNumericFunc):
    "ACS"

class AdvalFunc(AstNode):
    "ADVAL"
    formal_type = TypeOption(IntegerType)
    actual_type = formal_type
    factor = Node(formalType=IntegerType)

class AscFunc(AstNode):
    "ASC"
    formal_type = TypeOption(IntegerType)
    actual_type = formal_type
    factor = Node(formalType=StringType)
    
class AsnFunc(UnaryNumericFunc):
    "ASN"

class AtnFunc(UnaryNumericFunc):
    "ATN"

class BeatFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    actual_type = formal_type

class BeatsFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    actual_type = formal_type

class BgetFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    actual_type = formal_type
    channel = Node()

class ChrStrFunc(AstNode):
    formal_type = TypeOption(StringType)
    actual_type = formal_type
    factor = Node(formalType=IntegerType)

class CosFunc(UnaryNumericFunc):
    "COS"

class CountFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    actual_type = formal_type

class DegFunc(UnaryNumericFunc):
    "DEG"

class DimensionsFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    actual_type = formal_type
    array = Node(nodeType=Variable, formalType=Array)

class DimensionSizeFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    actual_type = formal_type
    array = Node(nodeType=Variable, formalType=Array)
    dimension = Node(formalType=IntegerType)

class EofFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    actual_type = formal_type
    channel = Node(formalType=ChannelType)

class ErlFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    actual_type = formal_type

class ErrFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    actual_type = formal_type

class EvalFunc(AstNode):
    "EVAL"
    formal_type = TypeOption(ScalarType)
    actual_type = formal_type
    factor = Node(formalType=StringType)
    
class ExpFunc(UnaryNumericFunc):
    "EXP"

class FalseFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    actual_type = formal_type

class GetFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    actual_type = formal_type

class GetStrFunc(AstNode):
    formal_type = TypeOption(StringType)
    actual_type = formal_type

class GetStrFileFunc(AstNode):
    formal_type = TypeOption(StringType)
    channel = Node(formalType=ChannelType)

class InkeyFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    actual_type = formal_type
    factor = Node(formalType=IntegerType)

class InkeyStrFunc(AstNode):
    formal_type = TypeOption(StringType)
    actual_type = formal_type
    factor = Node(formalType=IntegerType)

class InstrFunc(AstNode):
    "INSTR"
    formal_type = TypeOption(IntegerType)
    actual_type = formal_type
    source         = Node(formalType=StringType)
    sub_string     = Node(formalType=StringType)
    start_position = Node(formalType=IntegerType)

class IntFunc(AstNode):
    "INT"
    formal_type = TypeOption(IntegerType)
    actual_type = formal_type
    factor = Node(formalType=FloatType)

class LeftStrFunc(AstNode):
    formal_type = TypeOption(StringType)
    actual_type = formal_type
    source = Node()
    length = Node(formalType=IntegerType)

class LenFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    actual_type = formal_type
    factor = Node(formalType=StringType)

class LnFunc(UnaryNumericFunc):
    "LN"

class LogFunc(UnaryNumericFunc):
    "LOG"

class MidStrFunc(AstNode):
    formal_type = TypeOption(StringType)
    actual_type = formal_type
    source   = Node(formalType=StringType)
    position = Node(formalType=IntegerType)
    length   = Node(formalType=IntegerType)
    
class ModeFunc(AstNode):
    formal_type = TypeOption(IntegerType)

class OpeninFunc(AstNode):
    formal_type = TypeOption(ChannelType)
    filename = Node(formalType=StringType)

class OpenoutFunc(AstNode):
    formal_type = TypeOption(ChannelType)
    filename = Node(formalType=StringType)

class OpenupFunc(AstNode):
    formal_type = TypeOption(ChannelType)
    filename = Node(formalType=StringType)

class PosFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    actual_type = formal_type

class PiFunc(AstNode):
    formal_type = TypeOption(FloatType)
    actual_type = formal_type

class PointFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    x_coord = Node(formalType=IntegerType)
    y_coord = Node(formalType=IntegerType)

class QuitFunc(AstNode):
    "QUIT"
    formal_type = TypeOption(IntegerType)
    actual_type = formal_type
    
class RadFunc(UnaryNumericFunc):
    "RAD"

class ReadFunc(AstNode):
    "READ"
    formal_type = TypeOption(ScalarType)
    actual_type = formal_type

class RightStrFunc(AstNode):
    formal_type = TypeOption(StringType)
    actual_type = formal_type
    source = Node(formalType=StringType)
    length = Node(formalType=IntegerType)

class RndFunc(AstNode):
    "RND"
    # A minor change from BBC BASIC. In BBC BASIC RND(x) can return
    # either a float or integer.  In OWL BASIC we always return a
    # 64-bit float.
    formal_type = TypeOption(FloatType) 
    actual_type = formal_type
    option = Node(formalType=IntegerType)

class SinFunc(UnaryNumericFunc):
    "SIN"

class SgnFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    actual_type = formal_type
    factor = Node(formalType=NumericType)

class SqrFunc(UnaryNumericFunc):
    "SQR"

class StrStringFunc(AstNode):
    formal_type = TypeOption(StringType)
    actual_type = formal_type
    base   = IntegerOption(10)
    factor = Node(formalType=NumericType)

class Sum(AstNode):
    formal_type = TypeOption(IntegerType)
    array = Node(formalType=ArrayType)

class SumLenFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    array = Node(formalType=ArrayType)

class TanFunc(UnaryNumericFunc):
    "TAN"

class TempoFunc(AstNode):
    formal_type = TypeOption(IntegerType)

class TintFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    xCoord = Node(formalType=IntegerType)
    yCoord = Node(formalType=IntegerType)
    
class TopFunc(AstNode):
    formal_type = TypeOption(IntegerType)

class TrueFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    actual_type = formal_type

class ValFunc(AstNode):
    formal_type = TypeOption(NumericType)
    factor = Node(formalType=StringType)

class VposFunc(AstNode):
    formal_type = TypeOption(IntegerType)

class WidthFunc(AstNode):
    formal_type = TypeOption(IntegerType)

class Line(AstStatement):
    x1_coord = Node(formalType=IntegerType)
    y1_coord = Node(formalType=IntegerType)
    x2_coord = Node(formalType=IntegerType)
    y2_coord = Node(formalType=IntegerType)

class LiteralString(AstNode):
    actual_type = TypeOption(StringType)
    value = StringOption()

class LiteralInteger(AstNode):
    actual_type = TypeOption(IntegerType)
    value = IntegerOption()

class LiteralFloat(AstNode):
    actual_type = TypeOption(FloatType)
    value = FloatOption()

# Implicit AST nodes
class Concatenate(AstNode):
    formal_type = TypeOption(StringType)
    actual_type = formal_type
    lhs = Node(formalType=StringType)
    rhs = Node(formalType=StringType)

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
    target_logical_line = Node(formalType=IntegerType)

