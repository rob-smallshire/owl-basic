# Abstract Syntax Tree for BBC# Basic

import logging
import re

from ast_meta import *
    
class AstStatement(AstNode):
    formal_type = TypeOption(VoidType)
    pass
        
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

class AllocateArray(AstNode):
    identifier = StringOption()
    dimensions = Node()
    
class AllocateBlock(AstNode):
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
    data = Node(ScalarType)

    def __init__(self, data):
        super(Data, self).__init__()
        # TODO: Create the correct node types here
        self.data = self.parse(data)

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

class DefineFunction(AstStatement):
    name = StringOption()
    formal_parameters = Node()

class ReturnFromFunction(AstStatement):
    return_value = Node(formalType=ScalarType) # TODO: Can functions return arrays 

class DefineProcedure(AstStatement):
    name = StringOption()
    formal_parameters = Node()

class ReturnFromProcedure(AstStatement):
    pass

class ForToStep(AstStatement):
    identifer = Node()
    first     = Node(formalType=NumericType)
    last      = Node(formalType=NumericType)
    step      = Node(formalType=NumericType)

class Next(AstStatement):
    identifers = Node()

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
    mode          = Node(formalType=IntegerType)
    logicalColour = Node(formalType=IntegerType)
    tint          = Node(formalType=IntegerType)

class Goto(AstStatement):
    line = Node(formalType=IntegerType)

class Gosub(AstStatement):
    line = Node(formalType=IntegerType)

class Return(AstStatement):
    pass

class Install(AstStatement):
    filename = Node(formalType=StringType)

class If(AstStatement):
    condition = Node()
    true_clause = Node()
    false_clause = Node()

class LoadLibrary(AstStatement):
    filename = Node(formalType=StringType)

class Move(AstStatement):
    "MOVE"
    x_coord = Node(formalType=IntegerType, description="The x co-ordinate")
    y_coord = Node(formalType=IntegerType, description="The y co-ordinate")
    relative = BoolOption(False)

class Mode(AstStatement):
    number         = Node(formalType=IntegerType)
    width          = Node(formalType=IntegerType)
    height         = Node(formalType=IntegerType)
    bits_per_pixel = Node(formalType=IntegerType)
    frame_rate     = Node(formalType=IntegerType) 

class Mouse(AstStatement):
    x_coord = Node(formalType=IntegerType)
    y_coord = Node(formalType=IntegerType)
    buttons = Node(formalType=IntegerType)
    time    = Node(formalType=IntegerType)

class MouseStep(AstStatement):
    x_coeff = Node(formalType=NumericType)
    y_coeff = Node(formalType=NumericType)

class MouseColour(AstStatement):
    logicalColour = Node(formalType=IntegerType)
    red = Node(formalType=IntegerType)
    green = Node(formalType=IntegerType)
    blue = Node(formalType=IntegerType)

class MousePosition(AstStatement):
    x_coord     = Node(formalType=IntegerType)
    y_coord     = Node(formalType=IntegerType)
    moveMouse   = BoolOption(True)
    movePointer = BoolOption(True)

class MousePointer(AstStatement):
    shape       = Node(formalType=IntegerType)
    
class MouseRectangleOn(AstStatement):
    left   = Node(formalType=IntegerType)
    bottom = Node(formalType=IntegerType)
    right  = Node(formalType=IntegerType)
    top    = Node(formalType=IntegerType)
    
class MouseRectangleOff(AstStatement):
    pass

class On(AstStatement):
    pass

class Off(AstStatement):
    pass

class Origin(AstStatement):
    x_coord = Node(formalType=IntegerType)
    y_coord = Node(formalType=IntegerType)

class Oscli(AstStatement):
    command = Node(formalType=StringType)

class Plot(AstStatement):
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
    
class Report(AstStatement):
    pass

class Repeat(AstStatement):
   pass

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

class Array(AstNode):
    identifer = StringOption()

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
    item = Node()
    length = IntegerOption()
    
class While(AstStatement):
    condition = Node()

class Endwhile(AstStatement):
    pass

class Width(AstStatement):
    line_width = Node()

class Wait(AstStatement):
    centiseconds = Node()

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

class UnaryPlus(AstNode):
    expression = Node(formalType=NumericType)

class UnaryMinus(AstNode):
    expression = Node(formalType=NumericType)

class UnaryByteIndirection(AstNode):
    formal_type = TypeOption(IntegerType)
    expression = Node(formalType=IntegerType)

class UnaryIntegerIndirection(AstNode):
    formal_type = TypeOption(IntegerType)
    expression = Node(formalType=IntegerType)

class UnaryStringIndirection(AstNode):
    formal_type = TypeOption(StringType)
    expression = Node(formalType=IntegerType)

class UnaryFloatIndirection(AstNode):
    formal_type = TypeOption(FloatType)
    expression = Node(formalType=IntegerType)

class DyadicByteIndirection(AstNode):
    formal_type = TypeOption(IntegerType)
    base   = Node()
    offset = Node()

class DyadicIntegerIndirection(AstNode):
    formal_type = TypeOption(IntegerType)
    base  = Node()
    offset = Node()

class Not(AstNode):
    formal_type = TypeOption(IntegerType)
    factor = Node()

class BinaryNumericOperator(AstNode):
    lhs = Node(formalType=NumericType)
    rhs = Node(formalType=NumericType)

class Plus(BinaryNumericOperator):
    "add"
    pass

class Minus(BinaryNumericOperator):
    pass

class Multiply(BinaryNumericOperator):
    pass

class Divide(BinaryNumericOperator):
    pass

class Power(BinaryNumericOperator):
    pass

class BinaryOperator(AstNode):
    lhs = Node()
    rhs = Node()

class MatrixMultiply(BinaryOperator):
    pass

class BinaryIntegerOperator(BinaryOperator):
    lhs = Node(formalType=IntegerType)
    rhs = Node(formalType=IntegerType)

class IntegerDivide(BinaryOperator):
    pass

class IntegerModulus(BinaryOperator):
    pass

class RelationalOperator(BinaryOperator):
    pass

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

class ShiftLeft(BinaryOperator):
    pass

class ShiftRight(BinaryOperator):
    pass

class ShiftRightUnsigned(BinaryOperator):
    pass

class And(BinaryOperator):
    pass

class Or(BinaryOperator):
    pass

class Eor(BinaryOperator):
    pass

class AbsFunc(AstNode):
    factor = Node()

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
    channel = Node()

class MidStrLValue(AstNode):
    target = Node()
    position = Node(formalType=IntegerType)
    length = Node(formalType=IntegerType)
    
class RightStrLValue(AstNode):
    target = Node()
    length = Node(formalType=IntegerType)

class LeftStrLValue(AstNode):
    target = Node()
    length = Node(formalType=IntegerType)
    
class AcsFunc(AstNode):
    formal_type = TypeOption(FloatType)
    factor = Node()

class AdvalFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    factor = Node()

class AscFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    factor = Node(formalType=StringType)

class AsnFunc(AstNode):
    formal_type = TypeOption(FloatType)
    factor = Node()

class AtnFunc(AstNode):
    formal_type = TypeOption(FloatType)
    factor = Node()

class BeatFunc(AstNode):
    formal_type = TypeOption(IntegerType)

class BeatsFunc(AstNode):
    formal_type = TypeOption(IntegerType)

class BgetFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    channel = Node()

class ChrStrFunc(AstNode):
    formal_type = TypeOption(StringType)
    factor = Node()

class CosFunc(AstNode):
    formal_type = TypeOption(FloatType)
    radians = Node()

class CountFunc(AstNode):
    formal_type = TypeOption(IntegerType)

class DegFunc(AstNode):
    formal_type = TypeOption(FloatType)
    radians = Node(formalType=NumericType)

class DimensionsFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    array = Node()

class DimensionSizeFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    array = Node()
    dimension = Node(formalType=IntegerType)

class EofFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    channel = Node(formalType=ChannelType)

class ErlFunc(AstNode):
    formal_type = TypeOption(IntegerType)

class ErrFunc(AstNode):
    formal_type = TypeOption(IntegerType)

class ExpFunc(AstNode):
    formal_type = TypeOption(FloatType)
    factor = Node(formalType=NumericType)

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

class IntFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    factor = Node(formalType=NumericType)

class LeftStrFunc(AstNode):
    formal_type = TypeOption(StringType)
    source = Node()
    length = Node(formalType=IntegerType)

class LenFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    factor = Node(formalType=StringType)

class LnFunc(AstNode):
    formal_type = TypeOption(FloatType)
    factor = Node(formalType=NumericType)

class LogFunc(AstNode):
    formal_type = TypeOption(FloatType)
    factor = Node(formalType=NumericType)

class MidStrFunc(AstNode):
    formal_type = TypeOption(StringType)
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

class PiFunc(AstNode):
    formal_type = TypeOption(FloatType)

class PointFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    x_coord = Node(formalType=IntegerType)
    y_coord = Node(formalType=IntegerType)

class RadFunc(AstNode):
    formal_type = TypeOption(FloatType)
    degrees = Node(formalType=NumericType)

class RightStrFunc(AstNode):
    formal_type = TypeOption(StringType)
    source = Node()
    length = Node(formalType=IntegerType)

class RndFunc(AstNode):
    formal_type = TypeOption(NumericType)
    option = Node(formalType=IntegerType)

class SinFunc(AstNode):
    formal_type = TypeOption(FloatType)
    radians = Node(formalType=NumericType)

class SgnFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    factor = Node(formalType=NumericType)

class SqrFunc(AstNode):
    formal_type = TypeOption(FloatType)
    factor = Node(formalType=NumericType)

class StrStringFunc(AstNode):
    formal_type = TypeOption(StringType)
    base   = IntegerOption(10)
    factor = Node(formalType=NumericType)

class Sum(AstNode):
    formal_type = TypeOption(IntegerType)
    array = Node(formalType=ArrayType)

class SumLenFunc(AstNode):
    formal_type = TypeOption(IntegerType)
    array = Node(formalType=ArrayType)

class TanFunc(AstNode):
    formal_type = TypeOption(FloatType)
    factor = Node(formalType=NumericType)

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

class LiteralString(AstNode):
    formal_type = TypeOption(StringType)
    value = StringOption()

class LiteralInteger(AstNode):
    formal_type = TypeOption(IntegerType)
    value = IntegerOption()

class LiteralFloat(AstNode):
    formal_type = TypeOption(FloatType)
    value = FloatOption()

# Implicit AST nodes
class Concatenate(AstNode):
    formal_type = TypeOption(StringType)
    lhs = Node(formalType=StringType)
    rhs = Node(formalType=StringType)

class Cast(AstNode):
    "Implict Conversion"
    source_type = TypeOption()
    target_type = TypeOption()
    value = Node()
    
