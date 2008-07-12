# Abstract Syntax Tree for BBC# Basic

import logging
import re

from ast_meta import *
    
class AstStatement(AstNode):
    pass
        
class Program(AstNode):
    statement_list = Node()

class Statement(AstStatement):
    body = Node()
            
class StatementList(AstNode):
    statements = [Node()]

    def prepend(self, statement):
        self.statements.insert(0, statement)

    def append(self, statement):
        self.statements.append(statement)
        
class Beats(AstStatement):
    counter = Node(type=IntegerType)
    
class Channel(AstStatement):
    channel = Node(type=IntegerType)

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
    
class Circle(AstNode):
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
    return_value = Node()

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

class UnaryMinus(AstNode):
    expression = Node(type=NumericType)

class UnaryByteIndirection(AstNode):
    expression = Node(type=IntegerType)

class UnaryIntegerIndirection(AstNode):
    expression = Node(type=IntegerType)

class UnaryStringIndirection(AstNode):
    expression = Node(type=IntegerType)

class UnaryFloatIndirection(AstNode):
    expression = Node(type=IntegerType)

class DyadicByteIndirection(AstNode):
    base   = Node()
    offset = Node()

class DyadicIntegerIndirection(AstNode):
    base  = Node()
    offset = Node()

class Not(AstNode):
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

class EndValue(AstNode):
    expression = Node()

class ExtValue(AstNode):
    channel = Node()

class HimemValue(AstNode):
    pass

class LomemValue(AstNode):
    pass

class PageValue(AstNode):
    pass

class TimeValue(AstNode):
    pass

class TimeStrValue(AstNode):
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
    factor = Node()

class AdvalFunc(AstNode):
    factor = Node()

class AscFunc(AstNode):
    factor = Node()

class AsnFunc(AstNode):
    factor = Node()

class AtnFunc(AstNode):
    factor = Node()

class BeatFunc(AstNode):
    pass

class BeatsFunc(AstNode):
    pass

class BgetFunc(AstNode):
    channel = Node()

class ChrStrFunc(AstNode):
    factor = Node()

class CosFunc(AstNode):
    radians = Node()

class CountFunc(AstNode):
    pass

class DegFunc(AstNode):
    radians = Node()

class DimensionsFunc(AstNode):
    array = Node()

class DimensionSizeFunc(AstNode):
    array = Node()
    dimension = Node()

class EofFunc(AstNode):
    channel = Node()

class ErlFunc(AstNode):
    pass

class ErrFunc(AstNode):
    pass

class ExpFunc(AstNode):
    factor = Node()

class FalseFunc(AstNode):
    pass

class GetFunc(AstNode):
    pass

class GetStrFunc(AstNode):
    pass

class Get_strFileFunc(AstNode):
    channel = Node(type=ChannelType)

class InkeyFunc(AstNode):
    factor = Node(type = IntegerType)

class InkeyStrFunc(AstNode):
    factor = Node(type=IntegerType)

class IntFunc(AstNode):
    factor = Node(type=NumericType)

class LeftStrFunc(AstNode):
    source = Node()
    length = Node(type=IntegerType)

class LenFunc(AstNode):
    factor = Node(type=StringType)

class LnFunc(AstNode):
    factor = Node(type=NumericType)

class LogFunc(AstNode):
    factor = Node(type=NumericType)

class MidStrFunc(AstNode):
    source   = Node()
    position = Node(type=IntegerType)
    length   = Node(type=IntegerType)
    
class ModeFunc(AstNode):
    pass

class OpeninFunc(AstNode):
    filename = Node(type=StringType)

class OpenoutFunc(AstNode):
    filename = Node(type=StringType)

class OpenupFunc(AstNode):
    filename = Node(type=StringType)

class PosFunc(AstNode):
    pass

class PiFunc(AstNode):
    pass

class PointFunc(AstNode):
    x_coord = Node(type=IntegerType)
    y_coord = Node(type=IntegerType)

class RadFunc(AstNode):
    degrees = Node(type=NumericType)

class RightStrFunc(AstNode):
    source = Node()
    length = Node(type=IntegerType)

class RndFunc(AstNode):
    option = Node(type=IntegerType)

class SinFunc(AstNode):
    radians = Node(type=NumericType)

class SgnFunc(AstNode):
    factor = Node(type=NumericType)

class SqrFunc(AstNode):
    factor = Node(type=NumericType)

class StrStringFunc(AstNode):
    base   = IntegerOption(10)
    factor = Node(type=NumericType)

class Sum(AstNode):
    array = Node()

class SumLenFunc(AstNode):
    array = Node()

class TanFunc(AstNode):
    factor = Node(type=NumericType)

class TempoFunc(AstNode):
    pass

class TintFunc(AstNode):
    xCoord = Node(type=IntegerType)
    yCoord = Node(type=IntegerType)
    
class TopFunc(AstNode):
    pass

class TrueFunc(AstNode):
    pass

class ValFunc(AstNode):
    factor = Node(type=StringType)

class VposFunc(AstNode):
    pass

class WidthFunc(AstNode):
    pass

class LiteralString(AstNode):
    value = StringOption()

class LiteralInteger(AstNode):
    value = IntegerOption()

class LiteralFloat(AstNode):
    value = FloatOption()


