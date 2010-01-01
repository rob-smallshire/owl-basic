# A visitor implementation that creates an XML representation of the abstract syntax tree

from visitor import Visitor
from bbc_ast import StatementList, Statement, Assignment, Next, VariableList, Read, ReadFunc, WritableList
from ast_utils import replaceStatement, insertStatementBefore, removeStatement
    
class SeparationVisitor(Visitor):
    """
    AST visitor for separating complex nodes into multiple simpler nodes
    """
    
    def visitAstNode(self, node):
        node.forEachChild(self.visit)
    
    # TODO: Put DIM Statements in here
        
    def visitNext(self, next):
        """
        Split NEXT i%, j%, k% statements into NEXT i% : NEXT j% : NEXT k%
        """
        #print next
        self.visit(next.identifiers)
        statement_list = StatementList()
        statement_list.parent = next.parent
        statement_list.parent_property = next.parent_property
        statement_list.parent_index = next.parent_index
        statement_list.statements = []
        
        for identifier in next.identifiers.variables:
            statement = Statement()
            statement.parent = statement_list
            statement.parent_property = 'statements'
            statement.parent_index = len(statement_list.statements)
            statement_list.append(statement)
            
            new_next = Next()
            new_next.parent = statement
            new_next.parent_property = 'body'
            new_next.lineNum = next.lineNum
            statement.body = new_next
            
            variable_list = VariableList()
            variable_list.parent = new_next
            variable_list.parent_property = 'identifiers'
            new_next.identifiers = variable_list
            
            variable_list.variables = [identifier]
            
        getattr(next.parent.parent, next.parent.parent_property)[next.parent.parent_index] = statement_list
    
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
            statement = Statement()
            statement.parent = statement_list
            statement.parent_property = 'statements'
            statement.parent_index = len(statement_list.statements)
            statement_list.append(statement)
            
            read_func = ReadFunc()
            new_assignment = Assignment(lValue=writable, rValue=read_func)
            
            writable.parent = new_assignment
            writable.parent_property = 'lValue'
            writable.lineNum = read.lineNum
            
            read_func.parent = new_assignment
            read_func.parent_property = 'rValue'
            read_func.lineNum = read.lineNum
            
            new_assignment.parent = statement
            new_assignment.parent_property = 'body'
            new_assignment.lineNum = read.lineNum
            
            statement.body = new_assignment
                         
        getattr(read.parent.parent, read.parent.parent_property)[read.parent.parent_index] = statement_list