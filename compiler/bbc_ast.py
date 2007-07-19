# Abstract Syntax Tree for BBC# Basic

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

class Channel(AstNode):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr
        
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

class Bput(AstNode):
    def __init__(self, channel, expression, *args, **kwargs):
        self.channel = channel
        self.expr = expression
        super(Bput, self).__init__(*args, **kwargs)

    def xml(self, writer):
        writer.WriteStartElement("Bput")
        self.channel.xml(writer)
        writer.WriteStartElement("Byte")
        self.expr.xml(writer)
        writer.WriteEndElement()
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
    def __init__(self, x, y, hrad, vrad, fill=False, *args, **kwargs):
        self.x = x
        self.y = y
        self.hrad = hrad
        self.vrad = vrad
        self.fill = fill
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
        
class UnaryOp(AstNode):
    def __init__(self, *args, **kwargs):
        super(UnaryOp, self).__init__(*args, **kwargs)

    
class BinaryMathOp(AstNode):
    def __init__(self, operator, lhs, rhs, *args, **kwargs):
        self.op = operator
        self.lhs = lhs
        self.rhs = rhs
        super(BinaryMathOp, self).__init__(*args, **kwargs)
    
    def xml(self, writer):
        writer.WriteStartElement("BinaryOperator")
        writer.WriteStartAttribute("operator")
        writer.WriteString(self.op)
        writer.WriteEndAttribute()
        writer.WriteStartAttribute("Left")
        self.lhs.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartAttribute("Right")
        self.rhs.xml(writer)
        writer.WriteEndElement()
        writer.WriteEndElement()
    
class AbsFunc(AstNode):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr
        super(AbsFunc, self).__init__(*args, **kwargs)
    
    def xml(self, writer):
        writer.WriteStartElement("Abs")
        self.expr.xml(writer)
        writer.WriteEndElement()
        
class AcsFunc(AstNode):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr
        super(AcsFunc, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Acs")
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
        
 