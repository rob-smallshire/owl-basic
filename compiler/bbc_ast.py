# Abstract Syntax Tree for BBC# Basic

import re

class AstNode(object):
    def __init__(self, *args, **kwargs):
        pass
    
class Program(AstNode):
    def __init__(self, statement_list, *args, **kwargs):
        self.statement_list = statement_list
        super(Program, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Program")
        self.statement_list.xml(writer)
        writer.WriteEndElement()

class Statement(AstNode):
    def __init__(self, body=None, *args, **kwargs):
        self.body = body
        super(Statement, self).__init__(*args, **kwargs)

    def xml(self, writer):
        writer.WriteStartElement("Statement")
        if self.body:
            self.body.xml(writer)
        writer.WriteEndElement()

class StatementList(AstNode):
    def __init__(self, first_statement=None, *args, **kwargs):
        self.statements = []
        if first_statement:
            self.statements.append(first_statement)
        super(StatementList, self).__init__(*args, **kwargs)
    
    def append(self, statement):
        self.statements.append(statement)

    def xml(self, writer):
        writer.WriteStartElement("StatementList")
        for statement in self.statements:
            if statement:
                statement.xml(writer)
        writer.WriteEndElement()

class Beats(AstNode):
    def __init__(self, expression, *args, **kwargs):
        self.expression = expression
        super(Beats, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Beats")
        self.expression.xml(writer)
        writer.WriteEndElement()

class Channel(AstNode):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr
        super(Channel, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Channel")
        self.expr.xml(writer)
        writer.WriteEndElement()

class Assignment(AstNode):
    def __init__(self, identifier, expression, *args, **kwargs):
        self.lvalue = identifier
        self.rvalue = expression
        super(Assignment, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Assignment")
        writer.WriteStartElement("LValue")
        self.lvalue.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("RValue")
        self.rvalue.xml(writer)
        writer.WriteEndElement()
        writer.WriteEndElement()

class Increment(AstNode):
    def __init__(self, identifier, expression, *args, **kwargs):
        self.lvalue = identifier
        self.rvalue = expression
        super(Increment, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Increment")
        writer.WriteStartElement("LValue")
        self.lvalue.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("RValue")
        self.rvalue.xml(writer)
        writer.WriteEndElement()
        writer.WriteEndElement()

class Decrement(AstNode):
    def __init__(self, identifier, expression, *args, **kwargs):
        self.lvalue = identifier
        self.rvalue = expression
        super(Decrement, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Decrement")
        writer.WriteStartElement("LValue")
        self.lvalue.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("RValue")
        self.rvalue.xml(writer)
        writer.WriteEndElement()
        writer.WriteEndElement()
        
class Bput(AstNode):
    def __init__(self, channel, expression, newline=False, *args, **kwargs):
        self.channel = channel
        self.expr = expression
        # TODO: Whether newline is True or False depends on
        #       the type of expression.  If expr is a number,
        #       we default to False, if expr is a string we
        #       default to True.
        self.newline = newline
        super(Bput, self).__init__(*args, **kwargs)

    def xml(self, writer):
        writer.WriteStartElement("Bput")
        self.channel.xml(writer)
        writer.WriteStartElement("Bytes")
        self.expr.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartAttribute("newline")
        writer.WriteString(str(self.newline))
        writer.WriteEndAttribute()
        writer.WriteEndElement()  
        
class Case(AstNode):
    def __init__(self, expr, when_list, *args, **kwargs):
        self.expr = expr
        self.when_list = when_list
        
    def xml(self, writer):
        writer.WriteStartElement("Case")
        writer.WriteStartElement("Test")
        self.expr.xml(writer)
        writer.WriteEndElement()
        self.when_list.xml(writer)
        writer.WriteEndElement()

class WhenClauseList(AstNode):
    def __init__(self, first_clause=None, *args, **kwargs):
        self.clauses = []
        if first_clause:
            self.clauses.append(first_clause)
        super(WhenClauseList, self).__init__(*args, **kwargs)
        
    def append(self, when_clause):
        self.clauses.append(when_clause)
        
    def xml(self, writer):
        writer.WriteStartElement("WhenClauseList")
        for clause in self.clauses:
            print self.clauses
            clause.xml(writer)
        writer.WriteEndElement()

class WhenClause(AstNode):
    def __init__(self, expr_list, statement_list, *args, **kwargs):
        self.expr_list = expr_list
        self.statement_list = statement_list
        super(WhenClause, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("WhenClause")
        print self.expr_list
        self.expr_list.xml(writer)
        self.statement_list.xml(writer)
        writer.WriteEndElement()

class OtherwiseClause(AstNode):
    def __init__(self, statement_list, *args, **kwargs):
        self.statement_list = statement_list
        super(OtherwiseClause, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("OtherwiseClause")
        self.statement_list.xml(writer)
        writer.WriteEndElement()

class Data(AstNode):
    def __init__(self, data, *args, **kwargs):
        self.items = self.parse(data)
        super(Data, self).__init__(*args, **kwargs)
    
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
        print items
        return items
        
        
    def xml(self, writer):
        writer.WriteStartElement("Data")
        for item in self.items:
            writer.WriteStartElement("Item")
            writer.WriteString(str(item))
            writer.WriteEndElement()
        writer.WriteEndElement()

class ForToStep(AstNode):
    def __init__(self, identifier, start, end, step, *args, **kwargs):
        self.identifier = identifier
        self.start = start
        self.end = end
        self.step = step
        super(ForToStep, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("For")
        writer.WriteStartElement("LValue")
        self.identifier.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("First")
        self.start.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("Last")
        self.end.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("Step")
        self.step.xml(writer)
        writer.WriteEndElement()
        writer.WriteEndElement()
    
class Next(AstNode):
    def __init__(self, var_list, *args, **kwargs):
        self.var_list = var_list
        super(Next, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Next")
        if self.var_list:
            self.var_list.xml(writer)
        writer.WriteEndElement()

class Draw(AstNode):
    def __init__(self, x, y, relative = False, *args, **kwargs):
        self.x = x
        self.y = y
        self.relative = relative
        super(Draw, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Draw")
        writer.WriteStartAttribute("relative")
        writer.WriteString(str(self.relative))
        writer.WriteEndAttribute()
        writer.WriteStartElement("X")
        self.x.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("Y")
        self.y.xml(writer)
        writer.WriteEndElement()
        writer.WriteEndElement()

class Ellipse(AstNode):
    def __init__(self, x, y, hrad, vrad, rotate=None, fill=False, *args, **kwargs):
        self.x = x
        self.y = y
        self.hrad = hrad
        self.vrad = vrad
        self.fill = fill
        self.rotate = rotate
        super(Ellipse, self).__init__(*args, **kwargs)
               
    def xml(self, writer):
        writer.WriteStartElement("Ellipse")
        writer.WriteStartAttribute("Fill")
        writer.WriteString(str(self.fill))
        writer.WriteEndAttribute()
        writer.WriteStartElement("X")
        self.x.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("Y")
        self.y.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("HRad")
        self.hrad.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("VRad")
        self.vrad.xml(writer)
        writer.WriteEndElement()
        if self.rotate:
            writer.WriteStartElement("Rotate")
            self.rotate.xml(writer)
            writer.WriteEndElement()
        writer.WriteEndElement()

class GenerateError(AstNode):
    def __init__(self, errNo, errDesc, *args, **kwargs):
        self.errNo = errNo
        self.errDesc = errDesc
        super(GenerateError, self).__init__(*args, **kwargs)

    def xml(self, writer):
        writer.WriteStartElement("Envelope")
        writer.WriteStartElement("N")
        self.n.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("T")
        self.t.xml(writer)
        writer.WriteEndElement()

class End(AstNode):
    def __init__(self, *args, **kwargs):
        super(End, self).__init__(args, kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("End")
        writer.WriteEndElement()

class Envelope(AstNode):
    def __init__(self, n, t, pitch1, pitch2, pitch3, pNum1, pNum2, pNum3, ampAttack, ampDecay, ampSustain, ampRelease, ala, ald, *args, **kwargs):
        self.n=n
        self.t=t
        self.pitch1 = pitch1
        self.pitch2 = pitch2
        self.pitch3 = pitch3
        self.pNum1 = pNum1
        self.pNum2 = pNum2
        self.pNum3 = pNum3
        self.ampAttack = ampAttack
        self.ampDecay = ampDecay
        self.ampSustain = ampSustain
        self.ampRelease = ampRelease
        self.ala = ala
        self.ald = ald
        super(Envelope, self).__init__(*args, **kwargs)
               
    def xml(self, writer):
        writer.WriteStartElement("Envelope")
        writer.WriteStartElement("N")
        self.n.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("T")
        self.t.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("Pitch1")
        self.pitch1.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("Pitch2")
        self.pitch2.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("Pitch3")
        self.pitch3.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("PNum1")
        self.pNum1.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("PNum2")
        self.pNum2.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("PNum3")
        self.pNum3.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("AmpAttack")
        self.ampAttack.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("AmpDecay")
        self.ampDecay.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("AmpSustain")
        self.ampSustain.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("AmpRelease")
        self.ampRelease.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("Ala")
        self.ala.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("Ald")
        self.ald.xml(writer)
        writer.WriteEndElement()
        writer.WriteEndElement()

class Fill(AstNode):
    def __init__(self, x, y, relative = False, *args, **kwargs):
        self.x = x
        self.y = y
        self.relative = relative
        super(Fill, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Fill")
        writer.WriteStartAttribute("relative")
        writer.WriteString(str(self.relative))
        writer.WriteEndAttribute()
        writer.WriteStartElement("X")
        self.x.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("Y")
        self.y.xml(writer)
        writer.WriteEndElement()
        writer.WriteEndElement()

class Gcol(AstNode):
    #arguments on this class are transposed in comparison to BBC Basic
    def __init__(self, col, mode=None, *args, **kwargs):
        self.mode = mode
        self.col = col
        super(Gcol, self).__init__(*args, **kwargs)
          
    def xml(self, writer):
        writer.WriteStartElement("Gcol")
        writer.WriteStartElement("Col")
        self.col.xml(writer)
        writer.WriteEndElement()
        if self.mode:
            writer.WriteStartElement("Mode")
            self.mode.xml(writer)
            writer.WriteEndElement()
        writer.WriteEndElement()

class Goto(AstNode):
    def __init__(self, line, *args, **kwargs):
        self.line = line
        super(Goto, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Goto")
        self.line.xml(writer)
        writer.WriteEndElement()

class Gosub(AstNode):
    def __init__(self, line, *args, **kwargs):
        self.line = line
        super(Gosub, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Gosub")
        self.line.xml(writer)
        writer.WriteEndElement()

class Install(AstNode):
    def __init__(self, expression, *args, **kwargs):
        self.expression = expression
        super(Install, self).__init__(*args, **kwargs)

    def xml(self, writer):
        writer.WriteStartElement("Install")
        writer.WriteStartElement("expression")
        self.expression.xml(writer)
        writer.WriteEndElement()
        writer.WriteEndElement()

class If(AstNode):
    def __init__(self, condition, true_clause, false_clause, *args, **kwargs):
        self.condition = expression
        self.true_clause = true_clause
        self.false_clause = false_clause
        super(If, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("If")
        writer.WriteStartElement("Condition")
        self.condition.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("TrueClause")
        self.true_clause.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("FalseClause")
        self.false_clause.xml(writer)
        writer.WriteEndElement()
        writer.WriteEndElement()

class AddLibrary(AstNode):
    def __init__(self, expression, *args, **kwargs):
        self.expression = expression
        super(AddLibrary, self).__init__(*args, **kwargs)

    def xml(self, writer):
        writer.WriteStartElement("Library")
        writer.WriteStartElement("expression")
        self.expression.xml(writer)
        writer.WriteEndElement()
        writer.WriteEndElement()

class Move(AstNode):
    def __init__(self, x, y, relative = False, *args, **kwargs):
        self.x = x
        self.y = y
        self.relative = relative
        super(Move, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Move")
        writer.WriteStartAttribute("relative")
        writer.WriteString(str(self.relative))
        writer.WriteEndAttribute()
        writer.WriteStartElement("X")
        self.x.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("Y")
        self.y.xml(writer)
        writer.WriteEndElement()
        writer.WriteEndElement()

class Mode(AstNode):
    def __init__(self, mode, *args, **kwargs):
        self.mode = mode
        super(Mode, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Mode")
        self.mode.xml(writer)
        writer.WriteEndElement()

class Mouse(AstNode):
    def __init__(self, x, y, b, t=None, *args, **kwargs):
        self.x = x
        self.y = y
        self.b = b
        self.t = t
        super(Mouse, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Mouse")
        writer.WriteStartElement("X")
        self.x.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("Y")
        self.y.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("Button")
        self.b.xml(writer)
        writer.WriteEndElement()
        if self.t:
            writer.WriteStartElement("Time")
            self.t.xml(writer)
            writer.WriteEndElement()            
        writer.WriteEndElement()

class MouseStep(AstNode):
    def __init__(self, x, y=None, *args, **kwargs):
        self.x = x
        self.y = y
        super(MouseStep, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("MouseStep")
        writer.WriteStartElement("X")
        self.x.xml(writer)
        writer.WriteEndElement()
        if self.y:
            writer.WriteStartElement("Y")
            self.y.xml(writer)
            writer.WriteEndElement()
        writer.WriteEndElement()

class MouseColour(AstNode):
    def __init__(self, attrib, r, g, b, *args, **kwargs):
        self.attrib = attrib
        self.r = r
        self.g = g
        self.b = b
        super(MouseColour, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("MouseColour")
        writer.WriteStartElement("Attrib")
        self.attrib.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("R")
        self.r.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("G")
        self.g.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("B")
        self.b.xml(writer)
        writer.WriteEndElement()            
        writer.WriteEndElement()

class MousePointer(AstNode):
    def __init__(self, toX=None, toY=None, pointer= None, off=None, *args, **kwargs):
        self.toX = toX
        self.toY = toY
        self.pointer = pointer
        self.off = off
        super(MousePointer, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("MousePointer")
        if self.toX:
            writer.WriteStartElement("ToX")
            self.toX.xml(writer)
            writer.WriteEndElement()
        if self.toY:
            writer.WriteStartElement("ToY")
            self.toY.xml(writer)
            writer.WriteEndElement()
        if self.pointer:
            writer.WriteStartElement("Type")
            self.pointer.xml(writer)
            writer.WriteEndElement()
        if self.off:
            writer.WriteStartElement("Off")
            #self.off.xml(writer)              #unsure if tag here is enough
            writer.WriteEndElement()            
        writer.WriteEndElement()

class MouseRectangle(AstNode):
    def __init__(self, left=None, bottom=None, width=None, height=None, off=None, *args, **kwargs):
        self.left = left
        self.bottom = bottom
        self.width = width
        self.height = height
        self.off = off
        super(MouseRectangle, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("MouseRectangle")
        if self.off:
           writer.WriteStartAttribute("OFF")
           writer.WriteString(str(self.off))
           writer.WriteEndAttribute()
        if self.left and self.bottom and self.width and self.height:
            writer.WriteStartElement("Left")
            self.left.xml(writer)
            writer.WriteEndElement()
            writer.WriteStartElement("Bottom")
            self.bottom.xml(writer)
            writer.WriteEndElement()
            writer.WriteStartElement("Width")
            self.width.xml(writer)
            writer.WriteEndElement()
            writer.WriteStartElement("Height")
            self.height.xml(writer)
            writer.WriteEndElement()            
        writer.WriteEndElement()
            
class Origin(AstNode):
    def __init__(self, x, y, *args, **kwargs):
        self.x = x
        self.y = y
        super(Origin, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Origin")
        writer.WriteStartElement("X")
        self.x.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("Y")
        self.y.xml(writer)
        writer.WriteEndElement()
        writer.WriteEndElement()

class Oscli(AstNode):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr
        super(Oscli, self).__init__(*args, **kwargs)

    def xml(self, writer):
        writer.WriteStartElement("Oscli")
        writer.WriteStartElement("expr")
        self.expr.xml(writer)
        writer.WriteEndElement()
        writer.WriteEndElement()

class Plot(AstNode):
    def __init__(self, x, y, mode=None, relative = False, *args, **kwargs):
        self.x = x
        self.y = y
        self.relative = relative
        self.mode = mode
        super(Plot, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Plot")
        writer.WriteStartAttribute("relative")
        writer.WriteString(str(self.relative))
        writer.WriteEndAttribute()
        writer.WriteStartElement("X")
        self.x.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("Y")
        self.y.xml(writer)
        writer.WriteEndElement()
        if self.mode:
            writer.WriteStartElement("Mode")
            self.mode.xml(writer)
            writer.WriteEndElement()            
        writer.WriteEndElement()

class Point(AstNode):
    def __init__(self, x, y, by=None, *args, **kwargs):
        self.x = x
        self.y = y
        self.by = by
        super(Point, self).__init__(*args, **kwargs)

    def xml(self, writer):
        writer.WriteStartElement("Point")
        if self.by:
            writer.WriteStartAttribute("PointType")
            writer.WriteString(str(self.by))
            writer.WriteEndAttribute()
        writer.WriteStartElement("x")
        self.x.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("y")
        self.y.xml(writer)
        writer.WriteEndElement()
        writer.WriteEndElement()


class Print(AstNode):
    def __init__(self, print_list=None, *args, **kwargs):
        self.print_list = print_list
        super(Print, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Print")
        if self.print_list:
            self.print_list.xml(writer)
        writer.WriteEndElement()

class PrintList(AstNode):
    def __init__(self, first_item=None, *args, **kwargs):
        self.print_items = []
        if first_item:
            self.print_items.append(first_item)
        super(PrintList, self).__init__(*args, **kwargs)
    
    def append(self, item):
        self.print_items.append(item)
        
    def xml(self, writer):
        writer.WriteStartElement("PrintList")
        for item in self.print_items:
            item.xml(writer)
        writer.WriteEndElement()

class PrintItem(AstNode):
    def __init__(self, item=None, *args, **kwargs):
        self.item = item
        super(PrintItem, self).__init__(*args, **kwargs)

    def xml(self, writer):
        writer.WriteStartElement("PrintItem")
        self.item.xml(writer)
        writer.WriteEndElement()

class PrintManipulator(AstNode):
    def __init__(self, manip, *args, **kwargs):
        self.manip = manip
        super(PrintManipulator, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("PrintManipulator")
        writer.WriteStartAttribute("type")
        writer.WriteString(self.manip)
        writer.WriteEndAttribute()
        writer.WriteEndElement()

class Rectangle(AstNode):
    def __init__(self, x1, y1, width, height, x2=None, y2=None, rectType=None, *args, **kwargs):
        # if height is NONE then it is a square
        # unsure if need to check that SWAP has a TO
        self.x1 = x1
        self.y1 = y1
        self.width = width
        self.height = height
        self.x2 = x2
        self.y2 = y2
        self.rectType = rectType
        super(Rectangle, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Rectangle")
        writer.WriteStartAttribute("rectType")
        writer.WriteString(str(self.rectType))
        writer.WriteEndAttribute()
        writer.WriteStartElement("X1")
        self.x1.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("Y1")
        self.y1.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("Width")
        self.width.xml(writer)
        writer.WriteEndElement()
        if self.height:
            writer.WriteStartElement("Height")
            self.height.xml(writer)
            writer.WriteEndElement()
        if self.x2 and self.y2:
            writer.WriteStartElement("DestX")            #'DestX' will work but 'X2' wont.
            self.x2.xml(writer)                          # Unknown why this fails
            writer.WriteEndElement()
            writer.WriteStartElement("DestY")            #'DestY' will work but 'Y2' wont.
            self.y2.xml(writer)                          # Unknown Why this fails
            writer.WriteEndElement()
        writer.WriteEndElement()        

class Report(AstNode):
    def __init__(self, *args, **kwargs):
        super(Report, self).__init__(*args, **kwargs)

    def xml(self, writer):
        writer.WriteStartElement("Report")
        writer.WriteEndElement()

class Sound(AstNode):
    def __init__(self, channel = None, amplitude = None, pitch = None, duration = None, off=False, *args, **kwargs):
        self.channel = channel
        self.amplitude = amplitude
        self.pitch = pitch
        self.duration = duration
        self.off = off
        super(Sound, self).__init__(*args, **kwargs)
               
    def xml(self, writer):
        writer.WriteStartElement("Sound")
        if self.off:
            writer.WriteStartAttribute("OFF")
            writer.WriteString(str(self.off))
            writer.WriteEndAttribute()
        else:
            writer.WriteStartElement("Channel")
            self.channel.xml(writer)
            writer.WriteEndElement()
            writer.WriteStartElement("Amplitude")
            self.amplitude.xml(writer)
            writer.WriteEndElement()
            writer.WriteStartElement("Pitch")
            self.pitch.xml(writer)
            writer.WriteEndElement()
            writer.WriteStartElement("Duration")
            self.duration.xml(writer)
            writer.WriteEndElement()
        writer.WriteEndElement()

class Swap(AstNode):
    def __init__(self, var1, var2, *args, **kwargs): # may need to detect differance between array and vars
        self.var1 = var1
        self.var2 = var2
        super(Swap, self).__init__(*args, **kwargs)

    def xml(self, writer):
        writer.WriteStartElement("Swap")
        writer.WriteStartElement("var1")
        self.var1.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("var2")
        self.var2.xml(writer)
        writer.WriteEndElement()
        writer.WriteEndElement()


class TabH(AstNode):
    def __init__(self, h, *args, **kwargs):
        self.h_expr = h
        super(TabH, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("TabH")
        self.h_expr.xml(writer)
        writer.WriteEndElement()
        
class TabXY(AstNode):
    def __init__(self, x, y, *args, **kwargs):
        self.x_expr = x
        self.y_expr = y
        super(TabXY, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("TabXY")
        writer.WriteStartElement("X")
        self.x_expr.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("Y")
        self.y_expr.xml(writer)
        writer.WriteEndElement()
        writer.WriteEndElement()
        
class Tempo(AstNode):
    def __init__(self, expression, *args, **kwargs):
        self.expression = expression
        super(Tempo, self).__init__(*args, **kwargs)

    def xml(self, writer):
        writer.WriteStartElement("Tempo")
        writer.WriteStartElement("expression")
        self.expression.xml(writer)
        writer.WriteEndElement()
        writer.WriteEndElement()

        
class Spc(AstNode):
    def __init__(self, spaces, *args, **kwargs):
        self.expr = spaces
        super(Spc, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Spc")
        self.expr.xml(writer)
        writer.WriteEndElement()
        
class VariableList(AstNode):
    def __init__(self, first_variable=None, *args, **kwargs):
        self.variables = []
        if first_variable:
            self.variables.append(first_variable)
        super(VariableList, self).__init__(*args, **kwargs)
    
    def append(self, variable):
        self.variables.append(variable)
        
    def xml(self, writer):
        writer.WriteStartElement("VariableList")
        for variable in self.variables:
            variable.xml(writer)
        writer.WriteEndElement()

class Variable(AstNode):
    def __init__(self, name, *args, **kwargs):
        self.name = name
        super(Variable, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Variable")
        writer.WriteStartAttribute("name")
        writer.WriteString(self.name)
        writer.WriteEndAttribute()
        writer.WriteEndElement()

class Array(AstNode):
    def __init__(self, name, *args, **kwargs):
        self.name = name
        super(Array, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Array")
        writer.WriteStartAttribute("name")
        writer.WriteString(self.name)
        writer.WriteEndAttribute()
        writer.WriteEndElement()
        
class Indexer(AstNode):
    def __init__(self, name, indices, *args, **kwargs):
        self.name = name
        self.indices = indices
        super(Indexer, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Indexer")
        writer.WriteStartAttribute("name")
        writer.WriteString(self.name)
        writer.WriteEndAttribute()
        self.indices.xml(writer)
        writer.WriteEndElement()    

class Until(AstNode):
    def __init__(self, expression, *args, **kwargs):
        self.expression = expression
        super(Until, self).__init__(*args, **kwargs)

    def xml(self, writer):
        writer.WriteStartElement("Until")
        writer.WriteStartElement("expression")
        self.expression.xml(writer)
        writer.WriteEndElement()
        writer.WriteEndElement()

class Voices(AstNode):
    def __init__(self, expression, *args, **kwargs):
        self.expression = expression
        super(Voices, self).__init__(*args, **kwargs)

    def xml(self, writer):
        writer.WriteStartElement("Voices")
        writer.WriteStartElement("expression")
        self.expression.xml(writer)
        writer.WriteEndElement()
        writer.WriteEndElement()

class Vdu(AstNode):
    def __init__(self, list=None, *args, **kwargs):
        self.list = list
        super(Vdu, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Vdu")
        if self.list:
            self.list.xml(writer)
        writer.WriteEndElement()       

class VduList(AstNode):
    def __init__(self, first_item=None, *args, **kwargs):
        self.items = []
        if first_item:
            self.items.append(first_item)
        super(VduList, self).__init__(*args, **kwargs)
    
    def append(self, item):
        self.items.append(item)
        
    def xml(self, writer):
        writer.WriteStartElement("VduList")
        for item in self.items:
            item.xml(writer)
        writer.WriteEndElement()

class VduItem(AstNode):
    def __init__(self, expr, separator=',', *args, **kwargs):
        self.expr = expr
        self.separator = separator
        super(VduItem, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("VduItem")
        writer.WriteStartAttribute("separator")
        writer.WriteString(str(self.separator))
        writer.WriteEndAttribute()
        self.expr.xml(writer)
        writer.WriteEndElement()

class While(AstNode):
    def __init__(self, expression, *args, **kwargs):
        self.expression = expression
        super(While, self).__init__(*args, **kwargs)

    def xml(self, writer):
        writer.WriteStartElement("While")
        writer.WriteStartElement("expression")
        self.expression.xml(writer)
        writer.WriteEndElement()
        writer.WriteEndElement()

class Endwhile(AstNode):
    def __init__(self, *args, **kwargs):
        super(Endwhile, self).__init__(*args, **kwargs)

    def xml(self, writer):
        writer.WriteStartElement("Endwhile")
        writer.WriteEndElement()

class Width(AstNode):
    def __init__(self, expression, *args, **kwargs):
        self.expression = expression
        super(Width, self).__init__(*args, **kwargs)

    def xml(self, writer):
        writer.WriteStartElement("Width")
        writer.WriteStartElement("expression")
        self.expression.xml(writer)
        writer.WriteEndElement()
        writer.WriteEndElement()




class ExpressionList(AstNode):
    def __init__(self, first_expr=None, *args, **kwargs):
        self.expressions = []
        if first_expr:
            self.expressions.append(first_expr)
        super(ExpressionList, self).__init__(*args, **kwargs)
        
    def append(self, expr):
        self.expressions.append(expr) 
        
    def xml(self, writer):
        writer.WriteStartElement("ExpressionList")
        for expr in self.expressions:
            expr.xml(writer)
        writer.WriteEndElement()
        
class UnaryPlus(AstNode):
    def __init__(self, expr, *args, **kwargs):
        super(UnaryPlus, self).__init__(*args, **kwargs)
        self.expr = expr
        
    def xml(self, writer):
        writer.WriteStartElement("UnaryPlus")
        self.expr.xml(writer)
        writer.WriteEndElement()

class UnaryMinus(AstNode):
    def __init__(self, expr, *args, **kwargs):
        super(UnaryMinus, self).__init__(*args, **kwargs)
        self.expr = expr
        
    def xml(self, writer):
        writer.WriteStartElement("UnaryMinus")
        self.expr.xml(writer)
        writer.WriteEndElement()

class UnaryByteIndirection(AstNode):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr
        super(UnaryByteIndirection, self).__init__(*args, **kwargs)

    def xml(self, writer):
        writer.WriteStartElement("UnaryByteIndirection")
        self.expr.xml(writer)
        writer.WriteEndElement()

class UnaryIntegerIndirection(AstNode):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr
        super(UnaryIntegerIndirection, self).__init__(*args, **kwargs)

    def xml(self, writer):
        writer.WriteStartElement("UnaryIntegerIndirection")
        self.expr.xml(writer)
        writer.WriteEndElement()

class UnaryStringIndirection(AstNode):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr
        super(UnaryStringIndirection, self).__init__(*args, **kwargs)

    def xml(self, writer):
        writer.WriteStartElement("UnaryStringIndirection")
        self.expr.xml(writer)
        writer.WriteEndElement()    

class UnaryFloatIndirection(AstNode):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr
        super(UnaryFloatIndirection, self).__init__(*args, **kwargs)

    def xml(self, writer):
        writer.WriteStartElement("UnaryFloatIndirection")
        self.expr.xml(writer)
        writer.WriteEndElement()

class DyadicByteIndirection(AstNode):
    def __init__(self, lhs, rhs, *args, **kwargs):
        self.lhs = lhs
        self.rhs = rhs
        super(DyadicByteIndirection, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("DyadicByteIndirection")
        writer.WriteStartElement("Left")
        self.lhs.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("Right")
        self.rhs.xml(writer)
        writer.WriteEndElement()
        writer.WriteEndElement()

class DyadicIntegerIndirection(AstNode):
    def __init__(self, lhs, rhs, *args, **kwargs):
        self.lhs = lhs
        self.rhs = rhs
        super(DyadicIntegerIndirection, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("DyadicIntegerIndirection")
        writer.WriteStartElement("Left")
        self.lhs.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("Right")
        self.rhs.xml(writer)
        writer.WriteEndElement()
        writer.WriteEndElement()

class Not(AstNode):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr
        super(Not, self).__init__(*args, **kwargs)

    def xml(self, writer):
        writer.WriteStartElement("Not")
        self.expr.xml(writer)
        writer.WriteEndElement()

class BinaryOperator(AstNode):
    def __init__(self, operator, lhs, rhs, *args, **kwargs):
        self.op = operator
        self.lhs = lhs
        self.rhs = rhs
        super(BinaryOperator, self).__init__(*args, **kwargs)
    
    def xml(self, writer):
        writer.WriteStartElement("BinaryOperator")
        writer.WriteStartAttribute("operator")
        writer.WriteString(str(self.op))
        writer.WriteEndAttribute()
        writer.WriteStartElement("Left")
        self.lhs.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("Right")
        self.rhs.xml(writer)
        writer.WriteEndElement()
        writer.WriteEndElement()

class Plus(BinaryOperator):
    def __init__(self, lhs, rhs, *args, **kwargs):
        super(Plus, self).__init__('plus', lhs, rhs)

class Minus(BinaryOperator):
    def __init__(self, lhs, rhs, *args, **kwargs):
        super(Minus, self).__init__('minus', lhs, rhs)

class Multiply(BinaryOperator):
    def __init__(self, lhs, rhs, *args, **kwargs):
        super(Multiply, self).__init__('multiply', lhs, rhs)
        
class Divide(BinaryOperator):
    def __init__(self, lhs, rhs, *args, **kwargs):
        super(Divide, self).__init__('divide', lhs, rhs)

class MatrixMultiply(BinaryOperator):
    def __init__(self, lhs, rhs, *args, **kwargs):
        super(MatrixMultiply, self).__init__('matrix_multiply', lhs, rhs)

class IntegerDivide(BinaryOperator):
    def __init__(self, lhs, rhs, *args, **kwargs):
        super(IntegerDivide, self).__init__('div', lhs, rhs)
        
class IntegerModulus(BinaryOperator):
    def __init__(self, lhs, rhs, *args, **kwargs):
        super(IntegerModulus, self).__init__('mod', lhs, rhs)

class Power(BinaryOperator):
    def __init__(self, lhs, rhs, *args, **kwargs):
        super(Power, self).__init__('power', lhs, rhs)    

class RelationalOperator(BinaryOperator):
    def __init__(self, operator, lhs, rhs, *args, **kwargs):
        super(RelationalOperator, self).__init__(operator, lhs, rhs)
        
    def xml(self, writer):
        writer.WriteStartElement("RelationalOperator")
        writer.WriteStartAttribute("operator")
        writer.WriteString(str(self.op))
        writer.WriteEndAttribute()
        writer.WriteStartElement("Left")
        self.lhs.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("Right")
        self.rhs.xml(writer)
        writer.WriteEndElement()
        writer.WriteEndElement()

class Equal(RelationalOperator):
    def __init__(self, lhs, rhs, *args, **kwargs):
        super(RelationalOperator, self).__init__('eq', lhs, rhs)

class NotEqual(RelationalOperator):
    def __init__(self, lhs, rhs, *args, **kwargs):
        super(RelationalOperator, self).__init__('ne', lhs, rhs)

class LessThan(RelationalOperator):
    def __init__(self, lhs, rhs, *args, **kwargs):
        super(RelationalOperator, self).__init__('lt', lhs, rhs)

class LessThanEqual(RelationalOperator):
    def __init__(self, lhs, rhs, *args, **kwargs):
        super(RelationalOperator, self).__init__('lte', lhs, rhs)

class GreaterThan(RelationalOperator):
    def __init__(self, lhs, rhs, *args, **kwargs):
        super(RelationalOperator, self).__init__('gt', lhs, rhs)

class GreatThanEqual(RelationalOperator):
    def __init__(self, lhs, rhs, *args, **kwargs):
        super(RelationalOperator, self).__init__('gte', lhs, rhs)

class ShiftLeft(BinaryOperator):
    def __init__(self, lhs, rhs, *args, **kwargs):
        super(ShiftLeft, self).__init__('shift_left', lhs, rhs)

class ShiftRight(BinaryOperator):
    def __init__(self, lhs, rhs, *args, **kwargs):
        super(ShiftRight, self).__init__('shift_right', lhs, rhs)
        
class ShiftRightUnsigned(BinaryOperator):
    def __init__(self, lhs, rhs, *args, **kwargs):
        super(ShiftRightUnsigned, self).__init__('shift_right_unsigned', lhs, rhs)

class And(BinaryOperator):
    def __init__(self, lhs, rhs, *args, **kwargs):
        super(And, self).__init__('and', lhs, rhs)

class Or(BinaryOperator):
    def __init__(self, lhs, rhs, *args, **kwargs):
        super(Or, self).__init__('and', lhs, rhs)
        
class Eor(BinaryOperator):
    def __init__(self, lhs, rhs, *args, **kwargs):
        super(Eor, self).__init__('and', lhs, rhs)

class AbsFunc(AstNode):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr
        super(AbsFunc, self).__init__(*args, **kwargs)
    
    def xml(self, writer):
        writer.WriteStartElement("Abs")
        self.expr.xml(writer)
        writer.WriteEndElement()

class EndValue(AstNode):
    def __init__(self, *args, **kwargs):
        super(EndValue, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("EndValue")
        writer.WriteEndElement()
        
class ExtValue(AstNode):
    def __init__(self, channel, *args, **kwargs):
        self.channel = channel
        super(ExtValue, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("ExtValue")
        self.channel.xml(writer)
        writer.WriteEndElement()

class MidStringLValue(AstNode):
    def __init__(self, target, position, length=None, *args, **kwargs):
        self.target = target
        self.position = position
        self.length = length
        super(EndValue, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("MidStringLValue")
        writer.WriteStartElement("Target")
        self.target.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("Position")
        self.position.xml(writer)
        writer.WriteEndElement()
        if self.length:
            writer.WriteStartElement("Length")
            self.length.xml(writer)
            writer.WriteEndElement()
        writer.WriteEndElement()    
        
class AcsFunc(AstNode):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr
        super(AcsFunc, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Acs")
        self.expr.xml(writer)
        writer.WriteEndElement()

class AdvalFunc(AstNode):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr
        super(AdvalFunc, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Adval")
        self.expr.xml(writer)
        writer.WriteEndElement()

class AscFunc(AstNode):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr
        super(AscFunc, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Asc")
        self.expr.xml(writer)
        writer.WriteEndElement()

class AsnFunc(AstNode):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr
        super(AsnFunc, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Asn")
        self.expr.xml(writer)
        writer.WriteEndElement()

class BeatFunc(AstNode):
    def __init__(self, *args, **kwargs):
        super(BeatFunc, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Beat")
        writer.WriteEndElement()

class BgetFunc(AstNode):
    def __init__(self, channel, *args, **kwargs):
        self.channel = expr
        super(AscFunc, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Bget")
        self.channel.xml(writer)
        writer.WriteEndElement()  

class ChrStrFunc(AstNode):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr
        super(AscFunc, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("ChrStr")
        self.expr.xml(writer)
        writer.WriteEndElement()

class CosFunc(AstNode):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr
        super(CosFunc, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Cos")
        self.expr.xml(writer)
        writer.WriteEndElement()

class CountFunc(AstNode):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr
        super(CountFunc, self).__init__(*args, **kwargs)

    def xml(self, writer):
        writer.WriteStartElement("Count")
        self.expr.xml(writer)
        writer.WriteEndElement()  

class DegFunc(AstNode):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr
        super(DegFunc, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Deg")
        self.expr.xml(writer)
        writer.WriteEndElement()

class DimensionsFunc(AstNode):
    def __init__(self, array, *args, **kwargs):
        self.array = array
        super(DimensionsFunc, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("DimensionsFunc")
        self.array.xml(writer)
        writer.WriteEndElement()
        
class DimensionSizeFunc(AstNode):
    def __init__(self, array, expr, *args, **kwargs):
        self.array = array
        self.expr = expr
        super(DimensionSizeFunc, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("DimensionSizeFunc")
        self.array.xml(writer)
        writer.WriteStartElement("Dimension")
        self.expr.xml(writer)
        writer.WriteEndElement()
        writer.WriteEndElement()

class MidStringFunc(AstNode):
    def __init__(self, source, position, length=None, *args, **kwargs):
        self.source = source
        self.position = position
        self.length = length
        super(MidStringFunc, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("MidStringFunc")
        writer.WriteStartElement("Source")
        self.source.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("Position")
        self.position.xml(writer)
        writer.WriteEndElement()
        if self.length:
            writer.WriteStartElement("Length")
            self.length.xml(writer)
            writer.WriteEndElement()
        writer.WriteEndElement()    

class RadFunc(AstNode):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr
        super(RadFunc, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Rad")
        self.expr.xml(writer)
        writer.WriteEndElement()

class SinFunc(AstNode):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr
        super(SinFunc, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Sin")
        self.expr.xml(writer)
        writer.WriteEndElement()
        
class StrStringFunc(AstNode):
    def __init__(self, expr, base=10, *args, **kwargs):
        self.expr = expr
        self.base = base
        super(StrStringFunc, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("StrString")
        writer.WriteStartAttribute("base")
        writer.WriteString(self.base)
        writer.WriteEndElement()
        self.expr.xml(writer)
        writer.WriteEndElement()

class LiteralString(AstNode):
    def __init__(self, value, *args, **kwargs):
        self.value = value
        super(LiteralString, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("String")
        writer.WriteStartAttribute("value")
        writer.WriteString(self.value)
        writer.WriteEndAttribute()
        writer.WriteEndElement()

class LiteralInteger(AstNode):
    def __init__(self, value, *args, **kwargs):
        self.value = value
        super(LiteralInteger, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Integer")
        writer.WriteStartAttribute("value")
        writer.WriteString(str(self.value))
        writer.WriteEndAttribute()
        writer.WriteEndElement()
    
class LiteralFloat(AstNode):
    def __init__(self, value, *args, **kwargs):
        self.value = value
        super(LiteralFloat, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Float")
        writer.WriteStartAttribute("value")
        writer.WriteString(str(self.value))
        writer.WriteEndAttribute()
        writer.WriteEndElement()        
        
 