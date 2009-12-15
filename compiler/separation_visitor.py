# A visitor implementation that creates an XML representation of the abstract syntax tree

from visitor import Visitor
from bbc_ast import StatementList, Statement, Next, VariableList, Read, WritableList
    
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
        Split READ A, B, C statements into READ A : READ B : READ C
        """
        # TODO Split READ A, B, C statements into READ A : READ B : READ C
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
            
            new_read = Read()
            new_read.parent = statement
            new_read.parent_property = 'body'
            new_read.lineNum = read.lineNum
            statement.body = new_read
            
            writable_list = WritableList()
            writable_list.parent = new_read
            writable_list.parent_property = 'writables'
            new_read.writables = writable_list
            
            writable_list.writables = [writable]
            
        getattr(read.parent.parent, read.parent.parent_property)[read.parent.parent_index] = statement_list
            
            
             