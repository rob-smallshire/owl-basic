from visitor import Visitor

class BasicVisitor(Visitor):
    """
    AST visitor for converting the AST into back into OWL BASIC.
    """
    def __init__(self):
        pass
        
    def visitLiteralInteger(self, integer):
        sys.stdout.write(str(integer.value))
        
    def visitCircle(self, circle):
        sys.stdout.write("CIRCLE ")
        if circle.fill:
            sys.stdout.write("FILL ")
        self.visit(circle.xCoord)
        sys.stdout.write(", ")
        self.visit(circle.yCoord)
        sys.stdout.write(", ")
        self.visit(circle.radius)
        sys.stdout.write('\n')
        
    def visitMidStrFunc(self, mid_str_func):
        sys.stdout.write("MID$(")
        self.visit(mid_str_func.source)
        sys.stdout.write(", ")
        self.visit(mid_str_func.position)
        if mid_str_func.length is not None:
            sys.stdout.write(", ")
            self.visit(mid_str_func.length)
        sys.stdout.write(")")
        
    def visitTrueFunc(self, true_func):
        sys.stdout.write("TRUE ")

    def visitAcsFunc(self, acs_func):
        sys.stdout.write("ACS ")
        
    def visitAdvalFunc(self, adval_func):
        sys.stdout.write("ADVAL ")
        sys.stdout.write(adval_func.factor)
        
    def visitAsnFunc(self, Asn_func):
        sys.stdout.write("ASN ")

    def visitAtnFunc(self, atn_func):
        sys.stdout.write("ATN ")

    def visitStrStringFunc(self, str_string_func):
        sys.stdout.write("STR$")
        if str_string_func.base == 16:
            sys.stdout.write("~")
        self.visit(str_string_func.factor)
        