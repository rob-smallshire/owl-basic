# A visitor for performing type-checking over the Abstract Syntax Tree

import logging
from functools import partial

from owl_basic.visitor import Visitor
from owl_basic.symbol_tables import (SymbolInfo, SymbolTable, SystemSymbolTable,
    FormalParameterSymbolTable, LocalSymbolTable, PrivateSymbolTable)
from owl_basic.syntax.ast import FormalArgument, FormalReferenceArgument, Variable, Array, AstStatement


def _names_a_variable(node):
    """Does this formal parameter or LOCAL/PRIVATE item introduce a named symbol?

    A scalar (``Variable``) or whole array (``Array``) is a named, dynamically
    scoped location, so it gets a symbol-table entry. An array element or a
    ``?``/``!``/``$`` indirection is an l-value onto *existing* storage -- it has
    no name to localise, and codegen saves/restores the cell directly -- so it
    contributes no symbol.
    """
    return isinstance(node, (Variable, Array))
from owl_basic.ast_utils import findNode
from owl_basic import sigil

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
    
    def start(self, entry_point):
        """Drive CFG traversal from an entry point with an explicit worklist.

        Recursing through ``followSuccessors`` once per node overflows the call
        stack on large programs, so successors are queued here and processed in
        a loop instead.
        """
        self._worklist = []
        entry_point.accept(self)
        while self._worklist:
            node = self._worklist.pop()
            if node.symbolTable is None:
                node.accept(self)

    def followSuccessors(self, statement):
        # Queue successors for the worklist in start() (iterative depth-first).
        for out_edge in statement.outEdges:
            if out_edge.symbolTable is None:
                self._worklist.append(out_edge)
                
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
                    elif in_edge.symbolTable is not symbol_table:
                        # The statement is reached with different scopes on
                        # different paths (e.g. shared by MAIN and a PROC via an
                        # unstructured GOTO). Every BBC variable is a global that
                        # a LOCAL merely save/restores within a frame, so where
                        # the frame is path-dependent the safe, consistent scope
                        # is the global one -- the no-op (see docs/local-
                        # semantics.md). The per-routine save/restore is driven
                        # by block membership, not this chain, so resolving the
                        # name here to the global table does not lose a local.
                        return self.globalSymbols
            # No predecessor carries a scope yet (an unstructured entry, or the
            # routine's first statement): fall back to the global scope.
            return symbol_table if symbol_table is not None else self.globalSymbols
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
                    if not _names_a_variable(formal_argument.argument):
                        continue  # l-value formal: no named symbol (see helper)
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
        # A LOCAL save/restores its variables within each PROC/FN frame that owns
        # it (the frame whose ENDPROC/= restores them). The main program has no
        # such frame, so a LOCAL reached only from MAIN -- or, via unstructured
        # flow, *also* from MAIN -- is simply a no-op there: the variable stays
        # global. We therefore never reject on attribution; we name the scope
        # after a PROC/FN owner when there is one. See docs/local-semantics.md.
        if local.symbolTable is None:
            symbol_infos = self._local_symbol_infos(
                local.variables, SymbolInfo.modifier_local)
            local.symbolTable = LocalSymbolTable(
                symbol_infos, self._owning_routine(local),
                self.checkPredecessorsAndRefer(local))
        self.followSuccessors(local)
    
    def visitPrivate(self, private):
        #logger.debug("SymbolTableVisitor.visitPrivate")
        # TODO: We should have a warning if LOCAL and PRIVATE are not the first
        #       statements in a definition
        # PRIVATE shares LOCAL's scoping rule (see visitLocal): owned by each
        # PROC/FN frame that reaches it, a no-op where there is none.
        if private.symbolTable is None:
            symbol_infos = self._local_symbol_infos(
                private.variables, SymbolInfo.modifier_private)
            private.symbolTable = PrivateSymbolTable(
                symbol_infos, self._owning_routine(private),
                self.checkPredecessorsAndRefer(private))
        self.followSuccessors(private)

    def _local_symbol_infos(self, variables, modifier):
        """Symbol infos for the named items of a LOCAL/PRIVATE statement.

        l-value items (array elements, ?/!/$ indirection) name no symbol -- they
        save/restore an existing cell directly -- so they are skipped here.
        """
        infos = []
        for variable in variables:
            if _names_a_variable(variable):
                infos.append(SymbolInfo(variable.identifier,
                                        variable.actualType, modifier))
        return infos

    def _owning_routine(self, statement):
        """A PROC/FN that owns *statement*'s LOCAL/PRIVATE frame, for the scope
        table's name. The main program owns no LOCAL frame, so it is only the
        owner when nothing else reaches the statement (a no-op LOCAL)."""
        owners = sorted(statement.entryPoints - {'MAIN'})
        return owners[0] if owners else 'MAIN'
    
    def visitAssignment(self, statement):
        logger.debug("SymbolTableVisitor.visitAssignment")
        logging.debug("symbol-table statement: %s", statement)
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
        # DIM b n reserves a byte block and stores its base address in b, which
        # is therefore an ordinary (integer) variable holding a pointer.
        statement.symbolTable = self.checkPredecessorsAndRefer(statement)
        assert statement.symbolTable is not None
        self.tryAddVariable(statement.symbolTable, statement.identifier)
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
        
    def visitInputFile(self, statement):
        #logger.debug("SymbolTableVisitor.visitInputFile")
        statement.symbolTable = self.checkPredecessorsAndRefer(statement)
        assert statement.symbolTable is not None
        # INPUT#channel, var, var, ... -- items is the variable list read into
        # (flattened to a plain list by this stage, as visitInput's is).
        variables = (item for item in statement.items if isinstance(item, Variable))
        for variable in variables:
            self.tryAddVariable(statement.symbolTable, variable)
        self.followSuccessors(statement)
        
    def visitMouse(self, mouse):
        # MOUSE x,y,b[,t] reads the pointer position, button state and (optional)
        # time into its target variables -- so each is declared, like INPUT's.
        mouse.symbolTable = self.checkPredecessorsAndRefer(mouse)
        assert mouse.symbolTable is not None
        for target in (mouse.xCoord, mouse.yCoord, mouse.buttons, mouse.time):
            if isinstance(target, Variable):
                self.tryAddVariable(mouse.symbolTable, target)
        self.followSuccessors(mouse)
        
    def visitRead(self, statement):
        #logger.debug("SymbolTableVisitior.visitRead")
        statement.symbolTable = self.checkPredecessorsAndRefer(statement)
        assert statement.symbolTable is not None
        for writable in statement.writables.writables:
            self.tryAddVariable(statement.symbolTable, writable)
        
     