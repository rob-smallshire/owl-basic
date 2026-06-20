from owl_basic.exceptions import CompileError


class LineMapper(object):
    def __init__(self, physical_to_logical_map, line_to_stmt_map):
        self.physical_to_logical_map = physical_to_logical_map
        self.line_to_stmt_map = line_to_stmt_map
        
    def physicalToLogical(self, physical_line_number):
        if self.physical_to_logical_map is not None and physical_line_number is not None:
            return self.physical_to_logical_map[physical_line_number]
        else:
            return physical_line_number
    
    def logicalToPhysical(self, logical_line_number):
        if self.physical_to_logical_map is not None:
            
            return self.physical_to_logical_map.index(logical_line_number)
        else:
            return logical_line_number
        
    def logicalStatement(self, logical_line_number):
        physical_line_number = self.logicalToPhysical(logical_line_number)
        #print "physical_line_number = %s" % physical_line_number
        if physical_line_number in self.line_to_stmt_map:
            return self.line_to_stmt_map[physical_line_number]
        return None
    
    def firstStatement(self):
        statement_lines = sorted([line for line in list(self.line_to_stmt_map.keys()) if line is not None])
        #for s in statement_lines:
        #    print "%s : %s" % (s, lnv.line_to_stmt[s])
        first_statement_line = statement_lines[0]
        #print "first_statement_line = %s" % first_statement_line
        first_statement = self.line_to_stmt_map[first_statement_line]
        return first_statement
    
    def statementOnLine(self, integer_node):
        '''
        :param integer_node: A LiteralInteger node containing a logical line number
        :returns: The first AstStatement node on that logical source code line
        '''
        # GOTO/GOSUB/ON GOTO accept a general expression in the grammar, but a
        # static compiler must know the target at compile time. A non-constant
        # target (GOTO X, GOSUB -X) cannot be resolved, so reject it gracefully
        # rather than crash dereferencing a .value the node does not have.
        if type(integer_node).__name__ != "LiteralInteger":
            raise CompileError(
                "the target of GOTO/GOSUB must be a constant line number; a "
                "computed target (%s) cannot be compiled"
                % type(integer_node).__name__
            )
        logical_line_number = integer_node.value
        statement = self.logicalStatement(logical_line_number)
        #print "logical_line_number = %d, statement = %s" % (logical_line_number, statement)
        return statement