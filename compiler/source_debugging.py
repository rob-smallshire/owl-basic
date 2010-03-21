import logging
import re
from bisect import bisect_right

from visitor import Visitor

class SourceDebuggingVisitor(Visitor):
    '''
    A visitor for computing start and end character columns based upon
    file offsets attached to each AstStatement node and offsets to the beginning
    of each line. The operation of this visitor assumes that a depth-first traversal
    of the AST will visit all statements in source program order.
    '''
    def __init__(self, data, line_offsets, line_number_prefixes):
        '''
        :param data: The source file as a string
        :param line_offsets: an array of line offsets
        :param line_number_prexies: an array of the lengths of the line-number and
                                    whitespace prefix to each source line
        '''
        self.__data = data
        self.__line_offsets = line_offsets
        self.__line_number_prefixes = line_number_prefixes
        self.__previous_statement = None
        self.__separator_regex = re.compile(r'[\n:]') 

    def visitAstNode(self, node):
        node.forEachChild(self.visit)
    
    def visitAstStatement(self, statement):
        '''
        Get the startPos of the visited statement. Use this value, together with the
        probably innaccurate endPos of the *previous* statement to locate the end of
        the previous statement, and update its endPos value.
        '''
        print statement
        self.setPreviousStatementColumns(statement)
        self.__previous_statement = statement
        # There is no need to visit the children of most statements
    
    def visitIf(self, statement):
        print statement
        self.setPreviousStatementColumns(statement)
        # If statements, don't need adjusting, so we unset self.__previous_statement
        self.__previous_statement = None
        # We must visit the children of IF statements
        print "visiting trueClause"
        self.visit(statement.trueClause)
        
        self.__previous_statement = None
        print "visiting falseClause"
        self.visit(statement.falseClause)
        
        # Set up the columns for this IF statement itself
        self.setStartAndEndColumns(statement)
    
    def setPreviousStatementColumns(self, statement):
        '''
        Update the endPos attribute on self.__previous_statement based upon the startPos attribute
        of the statement parameters.  A search between the two statements for a statement separator
        is performed, and computations of the start and end character columns for __previous_statement
        are performed and these attributes set.
        Note: Assumes that self.__previous statement is the prior statement in the program
              order to statement
        :param statement: The statement being visited, the start of which marks the latest position
                          for the end of the previous statement.
        '''
        if self.__previous_statement is not None:
            # TODO: This needs to be smarter for compound IF statements - we need to separately visit
            # IF statements to ensure the children are visited and in the grammar we should only include
            # upto and including the THEN token as the marked part of the source.
            # Define a half-open range [search_start_pos, search_end_pos) within which we expect
            # to locate a statement boundary.
            search_start_pos = self.__previous_statement.endPos
            search_end_pos = statement.startPos
            assert search_start_pos is not None
            assert search_end_pos is not None
            if search_start_pos < search_end_pos - 1:
                # TODO: Some possible issue here with line end markers (because of normalised line endings), ignoring the contents of REMs, DATA and LiteralStrings
                #       and line continuation
                # Search for new-lines or COLONs within the search string
                m = self.__separator_regex.search(self.__data, search_start_pos, search_end_pos)
                if m is not None:
                    self.__previous_statement.endPos = m.start()
                else:
                    print "Error: Could not locate statement separator in >>>%s<<<" % self.__data[search_start_pos:search_end_pos]
            print ">>>%s<<<" % self.__data[self.__previous_statement.startPos:self.__previous_statement.endPos]
            self.setStartAndEndColumns(self.__previous_statement)

    def setStartAndEndColumns(self, statement):
        '''
        Sets the start and end columns on statement from start and end lexing positions.
        :param statement: The statement node to be modified.
        '''
        statement.startColumn = self.columnFromPos(statement.startPos)
        statement.endColumn = self.columnFromPos(statement.endPos)
    
    def columnFromPos(self, pos):
        '''
        :param pos: An zero-based offset from the beginning of the source file
        :returns: A one-based character column from the beginning of the line
        '''
        # TODO: Could make this faster by passing in a range on lines to check
        print "pos =", pos
        index = bisect_right(self.__line_offsets, pos) - 1
        print "index =", index
        line_start_pos = self.__line_offsets[index]
        print "line_start_pos =", line_start_pos
        prefix_length = self.__line_number_prefixes[index]
        print "prefix_length =", prefix_length
        column = pos - line_start_pos + prefix_length + 1 # One based
        print "column =", column
        print
        return column
        
        