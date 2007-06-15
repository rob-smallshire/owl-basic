# Abstract Syntax Tree for BBC# Basic

class AstNode(object):
    def __init__(self, *args, **kwargs):
        pass
    
class Program(AstNode):
    def __init__(self, statement_list, *args, **kwargs):
        self.statement_list = statement_list
        super(Program, self).__init__(*args, **kwargs)
        
    def __str__(self):
        return "Program { %s }" % self.statement_list

class StatementList(AstNode):
    def __init__(self, list=None, statement=None, *args, **kwargs):
        self.prior_list      = list
        self.next_statement  = statement
        super(StatementList, self).__init__(*args, **kwargs)
        
    def __str__(self):
        return "StatementList { %s, %s }" % (self.prior_list, self.next_statement)

class Channel(AstNode):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr

class Assignment(AstNode):
    def __init__(self, identifier, expression, *args, **kwargs):
        self.lvalue = identifier
        self.rvalue = expression
        super(Assignment, self).__init__(*args, **kwargs)
        
    def __str__(self):
        return "Assignment { %s, %s }" % (self.lvalue, self.rvalue)

class Case(AstNode):
    def __init__(self, expr, when_list, *args, **kwargs):
        self.expr = expr
        self.when_list = when_list
        
    def __str__(self):
        return "Case { %s %s }" % (self.expr, self.when_list)

class WhenClauseList(AstNode):
    def __init__(self, list, item, *args, **kwargs):
        self.list = list
        self.item = item
        super(WhenClauseList, self).__init__(*args, **kwargs)
        
    def __str__(self):
        return "WhenClauseList { %s %s }" % (self.list, self.item)

class WhenClause(AstNode):
    def __init__(self, expr_list, statement_list, *args, **kwargs):
        self.expr_list = expr_list
        self.statement_list = statement_list
        super(WhenClause, self).__init__(*args, **kwargs)
        
    def __str__(self):
        return "WhenClause { %s %s }" % (self.expr_list, self.statement_list) 

class OtherwiseClause(AstNode):
    def __init__(self, statement_list, *args, **kwargs):
        self.statement_list = statement_list
        super(OtherwiseClause, self).__init__(*args, **kwargs)
        
    def __str__(self):
        return "OtherwiseClause { %s }" % self.statement_list

class ForToStep(AstNode):
    def __init__(self, identifier, start, end, step, *args, **kwargs):
        self.identifier = identifier
        self.start = start
        self.end = end
        self.step = step
        super(ForToStep, self).__init__(*args, **kwargs)
        
    def __str__(self):
        return "ForToStep { %s %s %s %s }" % (self.identifier, self.start, self.end, self.step)
    
class Next(AstNode):
    def __init__(self, var_list, *args, **kwargs):
        self.var_list = var_list
        super(Next, self).__init__(*args, **kwargs)
        
    def __str__(self):
        return "Next { %s }" % self.var_list
        
class If(AstNode):
    def __init__(self, condition, true_clause, false_clause, *args, **kwargs):
        self.condition = expression
        self.true_clause = true_clause
        self.false_clause = false_clause
        super(If, self).__init__(*args, **kwargs)
    
class Print(AstNode):
    def __init__(self, print_list, *args, **kwargs):
        self.print_list = print_list
        super(Print, self).__init__(*args, **kwargs)
        
    def __str__(self):
        return "Print { %s }" % self.print_list

class PrintList(AstNode):
    def __init__(self, list=None, item=None, *args, **kwargs):
        self.prior_list = list
        self.next_item  = item
        super(PrintList, self).__init__(*args, **kwargs)
        
    def __str__(self):
        return "PrintList { %s, %s }" % (self.prior_list, self.next_item)
        
class TabH(AstNode):
    def __init__(self, h):
        self.h_expr = expr
        super(TabH, self).__init__(*args, **kwargs)
        
    def __str__(self):
        return "TabH { %s }" % self.h_expr
        
class TabXY(AstNode):
    def __init__(self, x, y, *args, **kwargs):
        self.x_expr = x
        self.y_expr = y
        super(TabXY, self).__init__(*args, **kwargs)
        
    def __str__(self):
        return "TabXY { %s, %s }" % (self.x_expr, self.y_expr)
        
class Spc(AstNode):
    def __init__(self, spaces, *args, **kwargs):
        self.expr = spaces
        super(Spc, self).__init__(*args, **kwargs)
        
    def __str__(self):
        return "Spc { %s }" % self.expr
        
class Vdu(AstNode):
    def __init__(self, list, *args, **kwargs):
        self.list = list
        super(Vdu, self).__init__(*args, **kwargs)
        
    def __str__(self):
        return "Vdu { %s }" % self.list

class VariableList(AstNode):
    def __init__(self, list, item, *args, **kwargs):
        self.list = list
        self.item = item
        super(VariableList, self).__init__(*args, **kwargs)
        
    def __str__(self):
        return "VariableList { %s %s }" % (self.list, self.item)
    
class VduList(AstNode):
    def __init__(self, item, tail, *args, **kwargs):
        self.item = item
        self.tail = tail
        super(VduList, self).__init__(*args, **kwargs)
        
    def __str__(self):
        return "VduList { %s, %s }" % (self.item, self.tail)

class VduItem(AstNode):
    def __init__(self, expr, separator, *args, **kwargs):
        self.expr = expr
        self.separator = separator
        super(VduItem, self).__init__(*args, **kwargs)
        
    def __str__(self):
        return "VduItem { %s, '%s' }" % (self.expr, self.separator)

class ExpressionList(AstNode):
    def __init__(self, list, item, *args, **kwargs):
        self.list = list
        self.item = item
        super(ExpressionList, self).__init__(*args, **kwargs)
        
    def __str__(self):
        return "ExpressionList { %s %s }" % (self.list, self.item)
        
class UnaryOp(AstNode):
    def __init__(self, *args, **kwargs):
        super(UnaryOp, self).__init__(*args, **kwargs)

    
class BinaryMathOp(AstNode):
    def __init__(self, operator, lhs, rhs, *args, **kwargs):
        self.op = operator
        self.lhs = lhs
        self.rhs = rhs
        print "Blah!"
        super(BinaryMathOp, self).__init__(*args, **kwargs)
    
    def __str__(self):
        return "BinaryOperator { %s, %s %s }" % (self.op, self.lhs, self.rhs) 
    
class AbsFunc(AstNode):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr
        super(AbsFunc, self).__init__(*args, **kwargs)
        
class AcsFunc(AstNode):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr
        super(AcsFunc, self).__init__(*args, **kwargs)

class AscFunc(AstNode):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr
        super(AscFunc, self).__init__(*args, **kwargs)
        
class BgetFunc(AstNode):
    def __init__(self, channel, *args, **kwargs):
        self.channel = expr
        super(AscFunc, self).__init__(*args, **kwargs)        

class ChrStrFunc(AstNode):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr
        super(AscFunc, self).__init__(*args, **kwargs)

class CosFunc(AstNode):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr
        super(CosFunc, self).__init__(*args, **kwargs)

class CountFunc(AstNode):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr
        super(CountFunc, self).__init__(*args, **kwargs)    
        
class StrStringFunc(AstNode):
    def __init__(self, expr, base=10, *args, **kwargs):
        self.expr = expr
        self.base = base
        super(StrStringFunc, self).__init__(*args, **kwargs)
        
class LiteralString(AstNode):
    def __init__(self, value, *args, **kwargs):
        self.value = value
        super(LiteralString, self).__init__(*args, **kwargs)
        
    def __str__(self):
        return '"%s"' % self.value

class LiteralInteger(AstNode):
    def __init__(self, value, *args, **kwargs):
        self.value = value
        super(LiteralInteger, self).__init__(*args, **kwargs)
        
    def __str__(self):
        return '%d' % self.value
    
class LiteralFloat(AstNode):
    def __init__(self, value, *args, **kwargs):
        self.value = value
        super(LiteralFloat, self).__init__(*args, **kwargs)
        
    def __str__(self):
        return '%f' % self.value        