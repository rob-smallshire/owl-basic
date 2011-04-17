'''
Convert assignment statements into more specific nodes
depending on the type of the left and side.
'''

from visitor import Visitor

class AssignmentVisitor(Visitor):
    '''
    Visitor for converting the different forms of assignment statements
    into different node types, for type checking.
    '''

    def __init__(self):
        pass
    
    def visitAssignment(self, assignment):
        cav = ConvertAssignmentVisitor(assignment)
        assignment.lValue.accept(cav)

class ConvertAssignmentVisitor(Visitor):
    
    def __init__(self, assignment):
        self.assignment = assignment

    def visitVariable(self, variable):
        pass
    
    def visitArray(self, array):
        'Convert to ArrayAssignment'
        array_assignment = ArrayAssignment(self.assignment.lValue)
        reparentNode(array.lValue, array_assignment)
        reparentNode(array.rValue, array_assignment)
        replaceStatement(self.assignment, array_assignment)
        # Replace the statement
    
#    TODO def visitIndexer
#        'Convert to SetElement'
    
    def visitEndLValue(self, end):
        'Convert to SetEnd'
        
    def visitExtLValue(self, ext):
        'Convert to SetExt'
        
    def visitHimemLValue(self, himem):
        'Convert to SetHimem'
        
    
    def visitMidStrLValue(self, dyadic):
        'Convert to SetMidStr'
    
    def visitRightStrLValue(self, dyadic):
        'Convert to SetRightStr'
    
    def visitLeftStrLValue(self, dyadic):
        'Convert to SetLeftStr'
    
    def visitUnaryByteIndirectionLValue(self, dyadic):
        'Convert to PokeByte'
        
    
    def visitDyadicByteIndirectionLValue(self, dyadic):
        'Convert to PokeByte'
        
        
    def visitDyadicIntegerIndirection(self, dyadic):
        'Convert to PokeIneger'
        
    
    
        