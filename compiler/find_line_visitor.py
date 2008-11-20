# A visitor implementation that locates the first statement on a specified logical line number

from bisect import bisect_left

from visitor import Visitor

class FindLineVisitor(Visitor):
    """
    AST visitor for locating the first statement of the specified line.
    """
    def __init__(self, logicalLineNumber):
        """
        Initialize the visitor with the logical line number we are looking for
        """
        self.targetLineNumber = logicalLineNumber
        
        # TODO: Wrap result in a property
        self.result = None
        
    def visitAstNode(self, node):
        "Default action is to do nothing"
        return
    
    def visitProgram(self, program):
        "Search the list of statements"
        # Extract the line numbers into an array
        line_numbers = [statement.lineNum for statement in program.statements]
        above_index = bisect_left(line_numbers, self.targetLineNumber)
        above_line_number = program.statements[above_index].lineNum
        
        if above_line_number == self.targetLineNumber:
            self.visit(program.statements[above_index])
            return
        
        if above_index == 0:
            return
        
        below_index = above_index - 1

        below_line_number = program.statements[below_index].lineNum
        if below_line_number <= self.targetLineNumber:
            self.visit(program.statements[below_index])
        
    def visitAstStatement(self, statement):
        if statement.lineNum == self.targetLineNumber:
            self.result = statement
            
    # TODO: Needs much more work for multi-line-if, CASE, WHEN, etc.
    
    