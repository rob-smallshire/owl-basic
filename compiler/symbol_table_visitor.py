# A visitor for performing type-checking over the Abstract Syntax Tree

import logging
from functools import partial

from visitor import Visitor
from errors import *
from symbol_tables import *
from syntax.ast import FormalArgument, FormalReferenceArgument, Variable, AstStatement
from ast_utils import findNode
import sigil

logger = logging.getLogger('symbol_table_visitor')

class SymbolTableVisitor(Visitor):
    """
    CFG visitor for annotating statement nodes with
    references to a symbol table.
    """
    def __init__(self):
        self.__global_symbols = SymbolTable("global symbol table",
                                            protection=SymbolTable.writable,
                                            parent=SystemSymbolTable.getInstance())
    
    def _getGlobalSymbols(self):
        return self.__global_symbols
    
    globalSymbols = property(_getGlobalSymbols)
    
    def followSuccessors(self, statement):
        # Visit successors - depth first through CFG
        for out_edge in statement.outEdges:
            if out_edge.symbolTable is None:
                self.visit(out_edge)
                
    def checkPredecessorsAndRefer(self, statement):
        """
        Given a statement, return the symbol table of the
        preceding statement. If a statement has multiple predecessors,
        check that all predecessors refer to the same
        symbol table - raise an error if not.
        """
        if statement.symbolTable is None:
            symbol_table = None
            for in_edge in statement.inEdges:
                if in_edge.symbolTable is not None:
                    if symbol_table is None:
                        symbol_table = in_edge.symbolTable
                    else:
                        if in_edge.symbolTable is not symbol_table:
                            errors.fatalError("Inconsistent variable scopes for %s at line %s" % statement, statement.lineNum)
            assert symbol_table is not None                
            return symbol_table
        return statement.symbolTable
    
    def tryAddVariable(self, symbol_table, variable):
        if (isinstance(variable, Variable)):
            symbol_info = SymbolInfo(variable.identifier, variable.actualType)
            symbol_table.tryAdd(symbol_info)
        else:
            assert 0, "%s is not a variable" % variable
            # TODO: What?
            pass
    
    def visitAstStatement(self, statement):
        """
        Attaches the same symbol table as the predecessor statement to this
        statement Depth first search visit of successors statements
        """
        #logger.debug("SymbolTableVisitor.visitAstStatement %s at %s", statement, statement.lineNum)
        statement.symbolTable = self.checkPredecessorsAndRefer(statement)
        assert statement.symbolTable is not None
        # TODO: Check that all other variable references within this statement can
        #       be successfully looked up.
        self.followSuccessors(statement)
        
    def visitDefinitionStatement(self, defproc):
        """
        Visit DEFPROC DEFFN. Create a new symbol table containing the formal
        parameters of the procedure or function, which also refers to the global symbol
        table.
        """
        #logger.debug("SymbolTableVisitor.visitDefinitionStatement")
        if defproc.symbolTable is None:
            symbol_table = None
            if defproc.formalParameters is None or len(defproc.formalParameters.arguments) == 0:
                # If there are no parameters, we just use the
                # global symbol table
                symbol_table = self.__global_symbols
            else:
                symbol_infos = []
                
                for formal_argument in defproc.formalParameters.arguments:
                    name = formal_argument.argument.identifier
                    type = formal_argument.argument.actualType
                    if isinstance(formal_argument.argument, FormalArgument):
                        modifier = SymbolInfo.modifier_arg    
                    elif isinstance(formal_argument.argument, FormalReferenceArgument):
                        modifier = SymbolInfo.modifier_ref_arg
                    symbol_info = SymbolInfo(name, type, SymbolInfo.modifier_arg)
                    symbol_infos.append(symbol_info)
                symbol_table = FormalParameterSymbolTable(symbol_infos, defproc.name, self.__global_symbols)
            assert symbol_table is not None  
            defproc.symbolTable = symbol_table
        self.followSuccessors(defproc)
                    
    def visitLocal(self, local):
        #logger.debug("SymbolTableVisitor.visitLocal")
        # TODO: We should have a warning if LOCAL and PRIVATE are not the first
        #       statements in a definition
        # TODO: REFACTOR This is almost identical to visitPrivate
        if 'MAIN' in local.entryPoints:
            errors.fatalError("Items can only be made local in a function or procedure at line %s" % local.lineNum)
        if local.symbolTable is None:
            symbol_infos = []
            for variable in local.variables:
                name = variable.identifier
                type = variable.actualType
                symbol_info = SymbolInfo(name, type, SymbolInfo.modifier_local)
                symbol_infos.append(symbol_info)
            assert len(local.entryPoints) == 1
            procedure = iter(local.entryPoints).next()
            symbol_table = LocalSymbolTable(symbol_infos, procedure, self.checkPredecessorsAndRefer(local))
            assert symbol_table is not None  
            local.symbolTable = symbol_table
        self.followSuccessors(local)
    
    def visitPrivate(self, private):
        #logger.debug("SymbolTableVisitor.visitPrivate")
        # TODO: We should have a warning if LOCAL and PRIVATE are not the first
        #       statements in a definition
        # TODO: REFACTOR This is almost identical to visitLocal
        if 'MAIN' in private.entryPoints:
            errors.fatalError("Items can only be made local in a function or procedure at line %s" % local.lineNum)
        if private.symbolTable is None:
            symbol_infos = []
            for variable in private.variables:
                name = variable.identifier
                type = variable.actualType
                symbol_info = SymbolInfo(name, type, SymbolInfo.modifier_private)
                symbol_infos.append(symbol_info)
            assert len(private.entryPoints) == 1
            procedure = iter(private.entryPoints).next()
            symbol_table = PrivateSymbolTable(symbol_infos, procedure, self.checkPredecessorsAndRefer(private))
            assert symbol_table is not None  
            private.symbolTable = symbol_table
        self.followSuccessors(private)
    
    def visitAssignment(self, statement):
        logger.debug("SymbolTableVisitor.visitAssignment")
        print statement
        #assert statement.symbolTable is not None
        statement.symbolTable = self.checkPredecessorsAndRefer(statement)
        #self.tryAddVariable(statement.symbolTable, statement.lValue)
        statement.lValue.accept(self)
        self.followSuccessors(statement)
    
    def visitVariable(self, variable):
        logger.debug("SymbolTableVisitor.visitVariable")
        statement_node = findNode(variable, lambda node: isinstance(node, AstStatement))
        symbol_table = statement_node.symbolTable
        self.tryAddVariable(symbol_table, variable)
        
    def visitAllocateArray(self, statement):
        logger.debug("SymbolTableVisitor.allocateArray")
        statement.symbolTable = self.checkPredecessorsAndRefer(statement)    
        symbol_info = SymbolInfo(statement.identifier, sigil.identifierToType(statement.identifier),
                                 rank=len(statement.dimensions))
        statement.symbolTable.tryAdd(symbol_info)
        self.followSuccessors(statement)
        
    def visitAllocateBlock(self, statement):
        #logger.debug("SymbolTableVisitor.allocateBlock")
        statement.symbolTable = self.checkPredecessorsAndRefer(statement)    
        assert statement.symbolTable is not None
        symbol_info = SymbolInfo(statement.identifier, PtrType)
        self.followSuccessors(statement)
    
    def visitForToStep(self, statement):
        #logger.debug("SymbolTableVisitor.visitForToStep")
        statement.symbolTable = self.checkPredecessorsAndRefer(statement)    
        assert statement.symbolTable is not None
        self.tryAddVariable(statement.symbolTable, statement.identifier)
        self.followSuccessors(statement)
        
    def visitInput(self, statement):
        #logger.debug("SymbolTableVisitor.visitInput")
        statement.symbolTable = self.checkPredecessorsAndRefer(statement)       
        assert statement.symbolTable is not None
        variables = (item for item in statement.inputList if isinstance(item, Variable))
        for variable in variables:
            self.tryAddVariable(statement.symbolTable, variable)
        self.followSuccessors(statement)
        
    def visitInputFile(self, input):
        #logger.debug("SymbolTableVisitor.visitInputFile")
        statement.symbolTable = self.checkPredecessorsAndRefer(statement)       
        assert statement.symbolTable is not None
        for item in statement.inputList:
            self.tryAddVariable(statement.symbolTable, item)
        self.followSuccessors(input)
        
    def visitMouse(self, mouse):
        #logger.debug("SymbolTableVisitor.visitInput")
        statement.symbolTable = self.checkPredecessorsAndRefer(statement)
        assert statement.symbolTable is not None
        self.tryAddVariable(statement.symbolTable, statement.xCoord)
        self.tryAddVariable(statement.symbolTable, statement.yCoord)
        self.tryAddVariable(statement.symbolTable, statement.buttons)
        self.tryAddVariable(statement.symbolTable, statement.time)
        self.followSuccessors(statement)
        
    def visitRead(self, statement):
        #logger.debug("SymbolTableVisitior.visitRead")
        statement.symbolTable = self.checkPredecessorsAndRefer(statement)
        assert statement.symbolTable is not None
        for writable in statement.writables.writables:
            self.tryAddVariable(statement.symbolTable, writable)
        
     