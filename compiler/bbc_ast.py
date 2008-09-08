# Abstract Syntax Tree for BBC# Basic

import logging
import re

from ast_meta import *
from bbc_types import *
    
class AstStatement(AstNode):
    formal_type = TypeOption(VoidType)
    actual_type = formal_type
        
class Program(AstNode):
    #formal_type = TypeOption(None)
    statements = Node()

class Statement(AstStatement):
    #formal_type = TypeOption(None)
    body = Node()
            
class StatementList(AstNode):
    formal_type = TypeOption(None)
    statements = [Node()]

    def prepend(self, statement):
        self.statements.insert(0, statement)

    def append(self, statement):
        self.statements.append(statement)
        
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
    #       the type of datan.  If data is a number,
    #       we default to False, if data is a string we
    #       default to True.
    newline = BoolOption(False)

class Call(AstStatement):
    address = Node()    # TODO: AddressType?
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
    # TODO: How to we represent the data list?
    data = StringOption()

    def parse(self, data):
        "Parse the text following a DATA statement into items"
        # Break the data into fields
        raw_items = re.findall(r'(?:\s*"((?:[^"]+|"")*)"(?!")\s*)|([^,]+)', data)
        items = []
        for i, (quoted, unquoted) in enumerate(raw_items):
            if quoted:
                item = quoted.replace('""', '"')
            else:
                item = unquoted.lstrip()
                # If its the last item on the line, strip trailing space
                if i == len(raw_items) - 1:
                    item = item.rstrip()
            items.append(item)
        return items

class DefineFunction(MarkerStatement):
    name = StringOption()
    formal_parameters = Node()

class ReturnFromFunction(AstStatement):
    return_value = Node(formalType=ScalarType) # TODO: Can functions return arrays 

class DefineProcedure(MarkerStatement):
    name = StringOption()
    formal_parameters = Node()

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

class Move(AstStatement):
    "MOVE"
    x_coord = Node(formalType=IntegerType, description="The x co-ordinate")
    y_coord = Node(formalType=IntegerType, description="The y co-ordinate")
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
    manipulator = StringOption()

class PrintFile(AstStatement):
    channel = Node(formalType=ChannelType)
    items = Node()

class CallProcedure(AstStatement):
    name = StringOption()
    actual_parameters = Node()

class Quit(AstStatement):
    # TODO: Iyonix BASIC support exit value
    pass

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
    writables = Node()
    
class Report(AstStatement):
    pass

class Repeat(MarkerStatement):
    pass

class Restore(AstStatement):
    target_logical_line = Node(formalType=IntegerType)

class Sound(AstStatement):
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

class TabH(AstNode):
    x_coord = Node(formalType=IntegerType)

class TabXY(AstNode):
    x_coord = Node(formalType=IntegerType)
    y_coord = Node(formalType=IntegerType)

class Tempo(AstStatement):
    rate = Node(formalType=IntegerType)

class Tint(AstStatement):
    option = Node(formalType=IntegerType)
    tint   = Node(formalType=IntegerType)

class Spc(AstNode):
    spaces = Node(formalType=IntegerType)

class VariableList(AstNode):
    variables = [Node()]

    def append(self, variable):
        self.variables.append(variable)

class Variable(AstNode):
    identifier = StringOption()

class WritableList(AstNode):
    writables = [Node()]

    def append(self, writable):
        self.writables.append(writable)

class Array(AstNode):
    identifier = StringOption()

class Indexer(AstNode):
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

class UnaryIndirection(AstNode):
    expression = Node(formalType=AddressType)

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

class DyadicIndirection(AstNode):
    base   = Node(formalType=AddressType)
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
    pass

class Minus(BinaryNumericOperator):
    pass

class Multiply(BinaryNumericOperator):
    pass

class Divide(BinaryNumericOperator):
    pass

class Power(BinaryNumericOperator):
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
    pass

class NotEqual(RelationalOperator):
    pass

class LessThan(RelationalOperator):
    pass

class LessThanEqual(RelationalOperator):
    pass

class GreaterThan(RelationalOperator):
    pass

class GreaterThanEqual(RelationalOperator):
    pass

class ShiftLeft(BinaryIntegerOperator):
    pass

class ShiftRight(BinaryIntegerOperator):
    pass

class ShiftRightUnsigned(BinaryIntegerOperator):
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
    factor = Node(formalType=NumericType)

class EndValue(AstNode):
    formal_type = TypeOption(IntegerType)
    expression = Node()

class ExtValue(AstNode):
    formal_type = TypeOption(IntegerType)
    channel = Node()

class HimemValue(AstNode):
    formal_type = TypeOption(IntegerType)

class LomemValue(AstNode):
    formal_type = TypeOption(IntegerType)

class PageValue(AstNode):
    formal_type = TypeOption(IntegerType)
    pass

class TimeValue(AstNode):
    formal_type = TypeOption(IntegerType)
    pass

class TimeStrValue(AstNode):
    formal_type = TypeOption(StringType)
    pass

class PtrValue(AstNode):
    channel = Node(formalType=ChannelType)

class MidStrLValue(AstNode):
    target = Node(nodeType=Variable, formalType=StringType) # TODO: This needs to constrained by the type checker to be a Variable : nodeType=Variable ?
    position = Node(formalType=IntegerType)
    length = Node(formalType=IntegerType)
    
class RightStrLValue(AstNode):
    target = Node(nodeType=Variable, formalType=StringType) # TODO: This needs to constrained by the type checker to be a Variable : nodeType=Variable ?
    length = Node(formalType=IntegerType)

class LeftStrLValue(AstNode):
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
    formal_type = TypeOption(IntegerType)
    factor = Node(formalType=IntegerType)

class AscFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    actual_type = formal_type
    factor = Node(formalType=StringType)
    
class AsnFunc(UnaryNumericFunc):
    "ASN"

class AtnFunc(UnaryNumericFunc):
    "ATN"

class BeatFunc(AstNode):
    formal_type = TypeOption(IntegerType)

class BeatsFunc(AstNode):
    formal_type = TypeOption(IntegerType)

class BgetFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    channel = Node()

class ChrStrFunc(AstNode):
    formal_type = TypeOption(StringType)
    actual_type = formal_type
    factor = Node(formalType=IntegerType)

class CosFunc(UnaryNumericFunc):
    "COS"

class CountFunc(AstNode):
    formal_type = TypeOption(IntegerType)

class DegFunc(UnaryNumericFunc):
    "DEG"

class DimensionsFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    array = Node(nodeType=Variable, formalType=Array)

class DimensionSizeFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    array = Node(nodeType=Variable, formalType=Array)
    dimension = Node(formalType=IntegerType)

class EofFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    channel = Node(formalType=ChannelType)

class ErlFunc(AstNode):
    formal_type = TypeOption(IntegerType)

class ErrFunc(AstNode):
    formal_type = TypeOption(IntegerType)

class ExpFunc(UnaryNumericFunc):
    "EXP"

class FalseFunc(AstNode):
    formal_type = TypeOption(IntegerType)

class GetFunc(AstNode):
    formal_type = TypeOption(IntegerType)

class GetStrFunc(AstNode):
    formal_type = TypeOption(StringType)

class GetStrFileFunc(AstNode):
    formal_type = TypeOption(StringType)
    channel = Node(formalType=ChannelType)

class InkeyFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    factor = Node(formalType=IntegerType)

class InkeyStrFunc(AstNode):
    formal_type = TypeOption(StringType)
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
    factor = Node(formalType=StringType)

class LnFunc(UnaryNumericFunc):
    "LN"

class LogFunc(UnaryNumericFunc):
    "LOG"

class MidStrFunc(AstNode):
    formal_type = TypeOption(StringType)
    actual_type = formal_type
    source   = Node()
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

class RadFunc(UnaryNumericFunc):
    "RAD"

class RightStrFunc(AstNode):
    formal_type = TypeOption(StringType)
    actual_type = formal_type
    source = Node(formalType=StringType)
    length = Node(formalType=IntegerType)

class RndFunc(AstNode):
    formal_type = TypeOption(NumericType)
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
    "Implict Conversion"
    formal_type = TypeOption()
    source_type = TypeOption()
    target_type = TypeOption()
    value = Node()
    
