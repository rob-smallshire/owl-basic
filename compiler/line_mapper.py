class LineMapper(object):
    def __init__(self, physical_to_logical_map, line_to_stmt_map):
        self.physical_to_logical_map = physical_to_logical_map
        self.line_to_stmt_map = line_to_stmt_map
        
    def physicalToLogical(self, physical_line_number):
        if self.physical_to_logical_map is not None:
            return self.physical_to_logical_map(physical_line_number)
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
        if self.line_to_stmt_map.has_key(physical_line_number):
            return self.line_to_stmt_map[physical_line_number]
        return None
    
    def firstStatement(self):
        statement_lines = sorted([line for line in self.line_to_stmt_map.keys() if line is not None])
        #for s in statement_lines:
        #    print "%s : %s" % (s, lnv.line_to_stmt[s])
        first_statement_line = statement_lines[0]
        #print "first_statement_line = %s" % first_statement_line
        first_statement = self.line_to_stmt_map[first_statement_line]
        return first_statement