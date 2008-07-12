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