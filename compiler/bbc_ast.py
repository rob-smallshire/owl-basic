# Abstract Syntax Tree for BBC# Basic

import logging
import re

from ast_meta import *
    
class AstStatement(AstNode):
    type = VoidType
        
class Program(AstNode):
    type = None
    statement_list = Node()

class Statement(AstStatement):
    type = None
    body = Node()
            
class StatementList(AstNode):
    type = None
    statements = [Node()]

    def prepend(self, statement):
        self.statements.insert(0, statement)

    def append(self, statement):
        self.statements.append(statement)
        
class Beats(AstStatement):
    counter = Node(type=IntegerType)
    
class Channel(AstStatement):
    channel = Node(type=IntegerType)

class Dim(AstStatement):
    items = Node()
    
class DimList(AstNode):
    type = None
    items = [Node()]
    
    def append(self, node):
        self.items.append(node)

class AllocateArray(AstNode):
    identifier = Node()
    dimensions = Node()
    
class AllocateBlock(AstNode):
    identifier = Node()
    size       = Node(type = IntegerType)

class Assignment(AstStatement):
    l_value = Node()
    r_value = Node()
    
class Increment(AstStatement):
    l_value = Node()
    r_value = Node()

class Decrement(AstStatement):
    l_value = Node()
    r_value = Node()

class Bput(AstNode):
    channel = Node(type=ChannelType)
    data    = Node(type=IntegerType)
    # TODO: Whether newline is True or False depends on
    #       the type of datan.  If data is a number,
    #       we default to False, if data is a string we
    #       default to True.
    newline = BoolOption(False)

class Call(AstStatement):
    address = Node()    # TODO: AddressType?
    parameters = Node() # TODO: Needs handling in grammar
    
class Circle(AstStatement):
    x_coord = Node(type=IntegerType)
    y_coord = Node(type=IntegerType)
    radius  = Node(type=IntegerType)
    fill    = BoolOption(False)

class Cls(AstStatement):
    pass

class Clg(AstStatement):
    pass

class Colour(AstStatement):
    colour = Node(type=IntegerType)
    tint   = Node(type=IntegerType)

class Palette(AstStatement):
    physical_colour = Node(type=IntegerType)
    logical_colour  = Node(type=IntegerType)
    red             = Node(type=IntegerType)
    green           = Node(type=IntegerType)
    blue            = Node(type=IntegerType)

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
    channel = Node(type=ChannelType)

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
    formalParameters = Node()

class ReturnFromFunction(AstStatement):
    return_value = Node(type=ScalarType) # TODO: Can functions return arrays 

class DefineProcedure(AstStatement):
    name = StringOption()
    formalParameters = Node()

class ReturnFromProcedure(AstStatement):
    pass

class ForToStep(AstStatement):
    identifer = Node()
    first     = Node(type=NumericType)
    last      = Node(type=NumericType)
    step      = Node(type=NumericType)

class Next(AstStatement):
    identifers = Node()

class Draw(AstStatement):
    x_coord = Node(type=IntegerType)
    y_coord = Node(type=IntegerType)
    relative = BoolOption(False)

class Ellipse(AstStatement):
    x_coord    = Node(type=IntegerType)
    y_coord    = Node(type=IntegerType)
    semi_major = Node(type=IntegerType)
    semi_minor = Node(type=IntegerType)
    radians    = Node(type=IntegerType)
    fill       = BoolOption(False)

class GenerateError(AstStatement):
    number      = Node(type=IntegerType)
    description = Node(type=StringType)
    
class ReturnError(AstStatement):
    number      = Node(type=IntegerType)
    description = Node(type=StringType)      

class End(AstStatement):
    pass

class Envelope(AstStatement):
    n                 = Node(type=IntegerType)
    t                 = Node(type=IntegerType)
    pitch1            = Node(type=IntegerType)
    pitch2            = Node(type=IntegerType)
    pitch3            = Node(type=IntegerType)
    num_steps_1       = Node(type=IntegerType)
    num_steps_2       = Node(type=IntegerType)
    num_steps_3       = Node(type=IntegerType)
    amplitude_attack  = Node(type=IntegerType)
    amplitude_decay   = Node(type=IntegerType)
    amplitude_sustain = Node(type=IntegerType)
    amplitude_release = Node(type=IntegerType)
    target_attack     = Node(type=IntegerType)
    target_decay      = Node(type=IntegerType)

class Fill(AstStatement):
    x_coord = Node(type=IntegerType)
    y_coord = Node(type=IntegerType)
    relative = BoolOption(False)

class Gcol(AstStatement):
    mode          = Node(type=IntegerType)
    logicalColour = Node(type=IntegerType)
    tint          = Node(type=IntegerType)

class Goto(AstStatement):
    line = Node(type=IntegerType)

class Gosub(AstStatement):
    line = Node(type=IntegerType)

class Return(AstStatement):
    pass

class Install(AstStatement):
    filename = Node(type=StringType)

class If(AstStatement):
    condition = Node()
    true_clause = Node()
    false_clause = Node()

class LoadLibrary(AstStatement):
    filename = Node(type=StringType)

class Move(AstStatement):
    x_coord = Node(type=IntegerType)
    y_coord = Node(type=IntegerType)
    relative = BoolOption(False)

class Mode(AstStatement):
    number         = Node(type=IntegerType)
    width          = Node(type=IntegerType)
    height         = Node(type=IntegerType)
    bits_per_pixel = Node(type=IntegerType)
    frame_rate     = Node(type=IntegerType) 

class Mouse(AstStatement):
    x_coord = Node(type=IntegerType)
    y_coord = Node(type=IntegerType)
    buttons = Node(type=IntegerType)
    time    = Node(type=IntegerType)

class MouseStep(AstStatement):
    x_coeff = Node(type=NumericType)
    y_coeff = Node(type=NumericType)

class MouseColour(AstStatement):
    logicalColour = Node(type=IntegerType)
    red = Node(type=IntegerType)
    green = Node(type=IntegerType)
    blue = Node(type=IntegerType)

class MousePosition(AstStatement):
    x_coord     = Node(type=IntegerType)
    y_coord     = Node(type=IntegerType)
    moveMouse   = BoolOption(True)
    movePointer = BoolOption(True)

class MousePointer(AstStatement):
    shape       = Node(type=IntegerType)
    
class MouseRectangleOn(AstStatement):
    left   = Node(type=IntegerType)
    bottom = Node(type=IntegerType)
    right  = Node(type=IntegerType)
    top    = Node(type=IntegerType)
    
class MouseRectangleOff(AstStatement):
    pass

class On(AstStatement):
    pass

class Off(AstStatement):
    pass

class Origin(AstStatement):
    x_coord = Node(type=IntegerType)
    y_coord = Node(type=IntegerType)

class Oscli(AstStatement):
    command = Node(type=StringType)

class Plot(AstStatement):
    mode    = Node(type=IntegerType)
    x_coord = Node(type=IntegerType)
    y_coord = Node(type=IntegerType)
    relative = BoolOption(False)

class Point(AstStatement):
    x_coord = Node(type=IntegerType)
    y_coord = Node(type=IntegerType)
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
    channel = Node(type=ChannelType)
    items = Node()

class CallProcedure(AstStatement):
    name = StringOption()
    actualParameters = Node()

class Quit(AstStatement):
    # TODO: Iyonix BASIC support exit value
    pass

class Rectangle(AstStatement):
    x_coord = Node(type=IntegerType)
    y_coord = Node(type=IntegerType)
    width   = Node(type=IntegerType)
    height  = Node(type=IntegerType) # None ==> square
    fill    = BoolOption(False)

class RectangleBlit(AstStatement):
    x_coord_source = Node(type=IntegerType)
    y_coord_source = Node(type=IntegerType)
    width          = Node(type=IntegerType)
    height         = Node(type=IntegerType) # None ==> square
    x_coord_target = Node(type=IntegerType)
    y_coord_target = Node(type=IntegerType)

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
    channel = Node(type=IntegerType)
    amplitude = Node(type=IntegerType)
    pitch = Node(type=IntegerType)
    duration = Node(type=IntegerType)
    
class Mute(AstStatement):
    mute = BoolOption(False)

class Swap(AstStatement):
    identifier1 = StringOption()
    identifier2 = StringOption()

class Stop(AstStatement):
    pass

class Stereo(AstStatement):
    channel =  Node(type=IntegerType)
    position = Node(type=IntegerType)

class Sys(AstStatement):
    routine          = Node()
    actualParameters = Node()
    returnValues     = Node()
    flags            = Node()

class TabH(AstNode):
    x_coord = Node(type=IntegerType)

class TabXY(AstNode):
    x_coord = Node(type=IntegerType)
    y_coord = Node(type=IntegerType)

class Tempo(AstStatement):
    rate = Node(type=IntegerType)

class Tint(AstStatement):
    option = Node(type=IntegerType)
    tint   = Node(type=IntegerType)

class Spc(AstNode):
    spaces = Node(type=IntegerType)

class VariableList(AstNode):
    variables = [Node()]

    def append(self, variable):
        self.variables.append(variable)

class Variable(AstNode):
    identifier = StringOption()

class Array(AstNode):
    identifer = StringOption()

class Indexer(AstNode):
    identifer = StringOption()
    index = Node()

class Until(AstStatement):
    condition = Node()

class Voices(AstStatement):
    number_of_voices = Node()

class Vdu(AstStatement):
    codes = Node()

class VduList(AstNode):
    items = [Node()]

    def append(self, item):
        self.items.append(item)

class VduItem(AstNode):
    item = Node()
    separator = StringOption()
    
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
    expression = Node(type=NumericType)
    #type = TypeOf(expression)

class UnaryMinus(AstNode):
    expression = Node(type=NumericType)
    #type = TypeOf(expression)

class UnaryByteIndirection(AstNode):
    type = IntegerType
    expression = Node(type=IntegerType)

class UnaryIntegerIndirection(AstNode):
    type = IntegerType
    expression = Node(type=IntegerType)

class UnaryStringIndirection(AstNode):
    type = StringType
    expression = Node(type=IntegerType)

class UnaryFloatIndirection(AstNode):
    type = FloatType
    expression = Node(type=IntegerType)

class DyadicByteIndirection(AstNode):
    type = IntegerType
    base   = Node()
    offset = Node()

class DyadicIntegerIndirection(AstNode):
    type = IntegerType
    base  = Node()
    offset = Node()

class Not(AstNode):
    type = IntegerType
    factor = Node()

class BinaryOperator(AstNode):
    lhs = Node()
    rhs = Node()

class Plus(BinaryOperator):
    pass

class Minus(BinaryOperator):
    pass

class Multiply(BinaryOperator):
    pass

class Divide(BinaryOperator):
    pass

class MatrixMultiply(BinaryOperator):
    pass

class IntegerDivide(BinaryOperator):
    pass

class IntegerModulus(BinaryOperator):
    pass

class Power(BinaryOperator):
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
    #type = TypeOf(factor)

class EndValue(AstNode):
    type = IntegerType
    expression = Node()

class ExtValue(AstNode):
    type = IntegerType
    channel = Node()

class HimemValue(AstNode):
    type = IntegerType
    pass

class LomemValue(AstNode):
    type = IntegerType
    pass

class PageValue(AstNode):
    type = IntegerType
    pass

class TimeValue(AstNode):
    type = IntegerType
    pass

class TimeStrValue(AstNode):
    type = StringType
    pass

class PtrValue(AstNode):
    channel = Node()

class MidStrLValue(AstNode):
    target = Node()
    position = Node(type=IntegerType)
    length = Node(type=IntegerType)
    
class RightStrLValue(AstNode):
    target = Node()
    length = Node(type=IntegerType)

class LeftStrLValue(AstNode):
    target = Node()
    length = Node(type=IntegerType)
    
class AcsFunc(AstNode):
    type = FloatType
    factor = Node()

class AdvalFunc(AstNode):
    type = IntegerType
    factor = Node()

class AscFunc(AstNode):
    type = IntegerType
    factor = Node(type=StringType)

class AsnFunc(AstNode):
    type = FloatType
    factor = Node()

class AtnFunc(AstNode):
    type = FloatType
    factor = Node()

class BeatFunc(AstNode):
    type = IntegerType

class BeatsFunc(AstNode):
    type = IntegerType

class BgetFunc(AstNode):
    type = IntegerType
    channel = Node()

class ChrStrFunc(AstNode):
    type = StringType
    factor = Node()

class CosFunc(AstNode):
    type = FloatType
    radians = Node()

class CountFunc(AstNode):
    type = IntegerType

class DegFunc(AstNode):
    type = FloatType
    radians = Node(type=NumericType)

class DimensionsFunc(AstNode):
    type = IntegerType
    array = Node()

class DimensionSizeFunc(AstNode):
    type = IntegerType
    array = Node()
    dimension = Node(type=IntegerType)

class EofFunc(AstNode):
    type = IntegerType
    channel = Node(type=ChannelType)

class ErlFunc(AstNode):
    type = IntegerType

class ErrFunc(AstNode):
    type = IntegerType

class ExpFunc(AstNode):
    type = FloatType
    factor = Node(type=NumericType)

class FalseFunc(AstNode):
    type = IntegerType

class GetFunc(AstNode):
    type = IntegerType

class GetStrFunc(AstNode):
    type = StringType

class GetStrFileFunc(AstNode):
    type = StringType
    channel = Node(type=ChannelType)

class InkeyFunc(AstNode):
    type = IntegerType
    factor = Node(type = IntegerType)

class InkeyStrFunc(AstNode):
    type = StringType
    factor = Node(type=IntegerType)

class IntFunc(AstNode):
    type = IntegerType
    factor = Node(type=NumericType)

class LeftStrFunc(AstNode):
    type = StringType
    source = Node()
    length = Node(type=IntegerType)

class LenFunc(AstNode):
    type = IntegerType
    factor = Node(type=StringType)

class LnFunc(AstNode):
    type = FloatType
    factor = Node(type=NumericType)

class LogFunc(AstNode):
    type = FloatType
    factor = Node(type=NumericType)

class MidStrFunc(AstNode):
    type = StringType
    source   = Node()
    position = Node(type=IntegerType)
    length   = Node(type=IntegerType)
    
class ModeFunc(AstNode):
    type = IntegerType

class OpeninFunc(AstNode):
    type = ChannelType
    filename = Node(type=StringType)

class OpenoutFunc(AstNode):
    type = ChannelType
    filename = Node(type=StringType)

class OpenupFunc(AstNode):
    type = ChannelType
    filename = Node(type=StringType)

class PosFunc(AstNode):
    type = IntegerType

class PiFunc(AstNode):
    type = FloatType

class PointFunc(AstNode):
    type = IntegerType
    x_coord = Node(type=IntegerType)
    y_coord = Node(type=IntegerType)

class RadFunc(AstNode):
    type = FloatType
    degrees = Node(type=NumericType)

class RightStrFunc(AstNode):
    type = StringType
    source = Node()
    length = Node(type=IntegerType)

class RndFunc(AstNode):
    type = NumericType
    option = Node(type=IntegerType)

class SinFunc(AstNode):
    type = FloatType
    radians = Node(type=NumericType)

class SgnFunc(AstNode):
    type = IntegerType
    factor = Node(type=NumericType)

class SqrFunc(AstNode):
    type = FloatType
    factor = Node(type=NumericType)

class StrStringFunc(AstNode):
    type = StringType
    base   = IntegerOption(10)
    factor = Node(type=NumericType)

class Sum(AstNode):
    type = IntegerType
    array = Node(type=ArrayType)

class SumLenFunc(AstNode):
    type = IntegerType
    array = Node(type=ArrayType)

class TanFunc(AstNode):
    type = FloatType
    factor = Node(type=NumericType)

class TempoFunc(AstNode):
    type = IntegerType

class TintFunc(AstNode):
    type = IntegerType
    xCoord = Node(type=IntegerType)
    yCoord = Node(type=IntegerType)
    
class TopFunc(AstNode):
    type = IntegerType

class TrueFunc(AstNode):
    type = IntegerType

class ValFunc(AstNode):
    type = NumericType
    factor = Node(type=StringType)

class VposFunc(AstNode):
    type = IntegerType

class WidthFunc(AstNode):
    type = IntegerType

class LiteralString(AstNode):
    type = StringType
    value = StringOption()

class LiteralInteger(AstNode):
    type = IntegerType
    value = IntegerOption()

class LiteralFloat(AstNode):
    type = FloatType
    value = FloatOption()


