# A visitor for performing type-checking over the Abstract Syntax Tree

from visitor import Visitor
from errors import *
from bbc_types import *
from symbol_tables import *
from bbc_ast import FormalArgument, FormalReferenceArgument

class SymbolTableVisitor(Visitor):
    """
    CFG visitor for annotating statement nodes with
    references to a symbol table.
    """
    def __init__(self):
        self.__global_symbols = SymbolTable(protection=SymbolTable.writable, parent=SystemSymbolTable.getInstance())
    
    def _getGlobalSymbols(self):
        return self.__global_symbols
    
    globalSymbols = property(_getGlobalSymbols)
    
    def followSuccessors(self, statement):
        # Visit successors - depth first through CFG
        for out_edge in statement.outEdges:
            if out_edge.symbolTable is None:
                self.visit(out_edge)
        
    def visitAstStatement(self, statement):
        "Depth first search visit of successors statements"
        print "SymbolTableVisitor.visitAstStatement %s at %s" % (statement, statement.lineNum)
        # Check that all predecessors are refer to the same
        # symbol table - raise an error if not - and attach that
        # symbol table to this node too
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
            statement.symbolTable = symbol_table
        self.followSuccessors(statement)
        
    def visitDefinitionStatement(self, defproc):
        print "SymbolTableVisitor.visitDefinitionStatement"
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
        print "SymbolTableVisitor.visitLocal"
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
            symbol_table = LocalSymbolTable(symbol_infos, procedure, local.entryPoints)
            assert symbol_table is not None  
            local.symbolTable = symbol_table
        self.followSuccessors(local)
    
    def visitPrivate(self, private):
        print "SymbolTableVisitor.visitPrivate"
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
            symbol_table = PrivateSymbolTable(symbol_infos, procedure, private.entryPoints)
            assert symbol_table is not None  
            private.symbolTable = symbol_table
        self.followSuccessors(private)
    
    