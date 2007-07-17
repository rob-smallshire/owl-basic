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

class StatementList(AstNode):
    def __init__(self, list=None, statement=None, *args, **kwargs):
        self.prior_list      = list
        self.next_statement  = statement
        super(StatementList, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("StatementList")
        if self.prior_list:
            writer.WriteStartElement("PriorList")
            self.prior_list.xml(writer)
            writer.WriteEndElement()
        if self.next_statement:
            writer.WriteStartElement("NextStatement")      
            self.next_statement.xml(writer)
            writer.WriteEndElement()
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
        self.WriteStartElement("Assignment")
        self.WriteStartElement("LValue")
        self.lvalue.xml(writer)
        self.WriteEndElement()
        self.WriteStartElement("RValue")
        self.rvalue.xml(writer)
        self.WriteEndElement()
        self.WriteEndElement()

class Bput(AstNode):
    def __init__(self, channel, expr, *args, **kwargs):
        self.channel = channel
        self.expr = expr
        super(Bput, self).__init__(*args, **kwargs)

    def xml(self, writer):
        writer.WriteStartElement("Bput")
        self.channel.xml(writer)
        writer.WriteEndElement()  
        
class Case(AstNode):
    def __init__(self, expr, when_list, *args, **kwargs):
        self.expr = expr
        self.when_list = when_list
        
    def xml(self, writer):
        pass

class WhenClauseList(AstNode):
    def __init__(self, list, item, *args, **kwargs):
        self.list = list
        self.item = item
        super(WhenClauseList, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        pass

class WhenClause(AstNode):
    def __init__(self, expr_list, statement_list, *args, **kwargs):
        self.expr_list = expr_list
        self.statement_list = statement_list
        super(WhenClause, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        pass

class OtherwiseClause(AstNode):
    def __init__(self, statement_list, *args, **kwargs):
        self.statement_list = statement_list
        super(OtherwiseClause, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        pass

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
        print self.identifier
        self.identifier.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("First")
        self.start.xml(writer)
        writer.WriteEndElement()
        writer.WriteStartElement("Last")
        self.end.xml(writer)
        writer.WriteEndElement()
        if self.step:
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
    
class Print(AstNode):
    def __init__(self, print_list, *args, **kwargs):
        self.print_list = print_list
        super(Print, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Print")
        if self.print_list:
            self.print_list.xml(writer)
        writer.WriteEndElement()

class PrintList(AstNode):
    def __init__(self, list=None, item=None, *args, **kwargs):
        self.prior_list = list
        self.next_item  = item
        super(PrintList, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("PrintList")
        if self.prior_list:
            writer.WriteStartElement("PriorList")
            self.prior_list.xml(writer)
            writer.WriteEndElement()
        writer.WriteStartElement("NextItem")
        self.next_item.xml(writer)
        writer.WriteEndElement()
        writer.WriteEndElement()
        
class TabH(AstNode):
    def __init__(self, h):
        self.h_expr = expr
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
        
class Vdu(AstNode):
    def __init__(self, list, *args, **kwargs):
        self.list = list
        super(Vdu, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Vdu")
        self.list.xml(writer)
        writer.WriteEndElement()

class VariableList(AstNode):
    def __init__(self, list, item, *args, **kwargs):
        self.list = list
        self.item = item
        super(VariableList, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("VariableList")
        if self.list:
            writer.WriteStartElement("PriorList")
            self.list.xml(writer)
            writer.WriteEndElement()
        writer.WriteStartElement("NextItem")
        self.item.xml(writer)
        writer.WriteEndElement()
        writer.WriteEndElement()

class Variable(AstNode):
    def __init__(self, id, *args, **kwargs):
        self.id = id
        super(Variable, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("Variable")
        writer.WriteStartAttribute("id")
        writer.WriteString(self.id)
        writer.WriteEndAttribute()
        writer.WriteEndElement()
        

class VduList(AstNode):
    def __init__(self, item, tail, *args, **kwargs):
        self.item = item
        self.tail = tail
        super(VduList, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("VduList")
        writer.WriteStartElement("Item")
        self.item.xml(writer)
        writer.WriteEndElement()
        if self.tail:
            writer.WriteStartElement("Tail")
            self.tail.xml(writer)
            writer.WriteEndElement()
        writer.WriteEndElement()

class VduItem(AstNode):
    def __init__(self, expr, separator, *args, **kwargs):
        self.expr = expr
        self.separator = separator
        super(VduItem, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("VduItem")
        writer.WriteStartAttribute("separator")
        writer.WriteString(self.separator)
        writer.WriteEndAttribute()
        writer.expr.xml(writer)
        writer.WriteEndElement()
        return "VduItem { %s, '%s' }" % (self.expr, self.separator)

class ExpressionList(AstNode):
    def __init__(self, list, item, *args, **kwargs):
        self.list = list
        self.item = item
        super(ExpressionList, self).__init__(*args, **kwargs)
        
    def xml(self, writer):
        writer.WriteStartElement("ExpressionList")
        if self.list:
            writer.WriteStartElement("PriorList")
            self.list.xml(writer)
            writer.WriteEndElement()
        writer.WriteStartElement("NextItem")
        self.item.xml(writer)
        writer.WriteEndElement()
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
        
 