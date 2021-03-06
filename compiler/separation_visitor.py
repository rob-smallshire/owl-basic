# A visitor implementation that creates an XML representation of the abstract syntax tree

from visitor import Visitor
from syntax.ast import StatementList, ScalarAssignment, Next, VariableList, Read, ReadFunc, WritableList
from ast_utils import replaceStatement, insertStatementBefore, removeStatement
    
class SeparationVisitor(Visitor):
    """
    AST visitor for separating complex nodes into multiple simpler nodes
    """
    
    def visitAstNode(self, node):
        node.forEachChild(self.visit)
                                          
    def visitDim(self, dim):
        """
        Split DIM i%(1), j%(2), k% 3 statements into separate AllocateArray and AllocateBlock
        statement nodes.
        """
        #self.visit(next.identifiers)
        statement_list = StatementList()
        statement_list.parent = dim.parent
        statement_list.parent_property = dim.parent_property
        statement_list.parent_index = dim.parent_index
        statement_list.statements = []
        
        for allocator in dim.items.items:           
            allocator.parent = statement_list
            allocator.parent_property = 'statements'
            allocator.parent_index = len(statement_list.statements)
            allocator.lineNum = dim.lineNum
            statement_list.append(allocator)
            
        getattr(dim.parent, dim.parent_property)[dim.parent_index] = statement_list
    
    def visitNext(self, next):
        """
        Split NEXT i%, j%, k% statements into NEXT i% : NEXT j% : NEXT k%
        """
        self.visit(next.identifiers)
        statement_list = StatementList()
        statement_list.parent = next.parent
        statement_list.parent_property = next.parent_property
        statement_list.parent_index = next.parent_index
        statement_list.statements = []
        
        for identifier in next.identifiers.variables:           
            new_next = Next()
            new_next.parent = statement_list
            new_next.parent_property = 'statements'
            new_next.parent_index = len(statement_list.statements)
            new_next.lineNum = next.lineNum
            statement_list.append(new_next)
            
            variable_list = VariableList()
            variable_list.parent = new_next
            variable_list.parent_property = 'identifiers'
            new_next.identifiers = variable_list
            
            variable_list.variables = [identifier] if identifier is not None else []
            
        getattr(next.parent, next.parent_property)[next.parent_index] = statement_list
    
    # TODO: Much of this code can be factored out of this method and the above one    
    def visitRead(self, read):
        """
        Split READ A, B, C statements into assignments A = READ : B = READ : C = READ
        where READ becomes a function.
        """
        
        # TODO Split READ A, B, C statements into READ A : READ B : READ C
        self.visit(read.writables)
        statement_list = StatementList()
        statement_list.parent = read.parent
        statement_list.parent_property = read.parent_property
        statement_list.parent_index = read.parent_index
        statement_list.statements = []
        
        for writable in read.writables.writables:
            read_func = ReadFunc()
            new_assignment = ScalarAssignment(lValue=writable, rValue=read_func)
            
            writable.parent = new_assignment
            writable.parent_property = 'lValue'
            writable.lineNum = read.lineNum
            
            read_func.parent = new_assignment
            read_func.parent_property = 'rValue'
            read_func.lineNum = read.lineNum
            
            new_assignment.parent = statement_list
            new_assignment.parent_property = 'statements'
            new_assignment.parent_index = len(statement_list.statements)
            new_assignment.lineNum = read.lineNum
            
            statement_list.append(new_assignment)
         
        getattr(read.parent, read.parent_property)[read.parent_index] = statement_list