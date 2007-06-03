# Abstract Syntax Tree for BBC# Basic

class AstNode(object):
    def __init__(self, *args, **kwargs):
        pass

class Channel(AstNode):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr

class Assignment(AstNode):
    def __init__(self, identifier, expression, *args, **kwargs):
        self.identifier = identifier
        self.expr = expression
        super(Assignment, self).__init__(*args, **kwargs)
    
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
        
class TabH(AstNode):
    def __init__(self, h):
        self.h_expr = expr
        super(TabH, self).__init__(*args, **kwargs)
        
class TabXY(AstNode):
    def __init__(self, x, y):
        self.x_expr = x
        self.y_expr = y
        super(TabXY, self).__init__(*args, **kwargs)
        
class Spc(AstNode):
    def __init__(self, spaces, *args, **kwargs):
        self.expr = spaces
        super(Spc, self).__init__(*args, **kwargs)
        
class UnaryOp(AstNode):
    def __init__(self, *args, **kwargs):
        super(UnaryOp, self).__init__(*args, **kwargs)
    
class BinaryOp(AstNode):
    def __init__(self, *args, **kwargs):
        super(BinaryOp, self).__init__(*args, **kwargs)
    
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
        
        
        