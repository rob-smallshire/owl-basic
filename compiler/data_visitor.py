import logging
import re
from visitor import Visitor

class DataVisitor(Visitor):
    '''
    Extra DATA from DATA statements and hidden DATA within REM statements.
    BBC BASIC allows any line to be RESTOREd to and will attempt to READ data
    from either the first DATA statement or the first COMMA.  This means it
    is possible to do
    10 REM,"HELLO", "WORLD"
    20 RESTORE 10
    30 READ A$
    40 PRINT A$
    > RUN
    HELLO
    
    For this reason, we need to store anything following a COMMA in a REM
    statement.  Any DATA keyword following a REM is irrelevant since it will
    not be tokenized, reading will start from the first COMMA.
    
    It is NOT possible to READ into a REMed data block from a previous DATA
    statement; the REMed line must be RESTOREd to directly
    '''
    def __init__(self):
        self.data = []
        self.index = {} # physical 0-based line number -> data[index]

    def parse(self, data):
        "Parse the text following a DATA statement into items"
        # Break the data into fields
        raw_items = re.findall(r'(?:\s*"((?:[^"]+|"")*)"(?!")\s*)|([^,]+)', data)
        items = []
        for i, (quoted, unquoted) in enumerate(raw_items):
            if quoted:
                item = quoted.replace('""', '"')
            else:
                item = unquoted.lstrip()
                # If its the last item on the line, strip trailing space
                if i == len(raw_items) - 1:
                    item = item.rstrip()
            items.append(item)
        return items
    
    def visitAstNode(self, node):
        node.forEachChild(self.visit)
    
    def visitData(self, statement):
       logging.debug("DATA statement : %s" % statement.data)
       self.index[statement.lineNum] = len(self.data)
       items = self.parse(statement.data)
       self.data.extend(items)
       
    def visitRem(self, statement):
        logging.debug("REM statement : %s" % statement.data)
        # Find the index of the first comma
        comma_index = statement.data.find(',')
        if comma_index != -1:
            # A comma was found, so it is possible to RESTORE to this line
            self.index[statement.lineNum] = len(self.data)
            items = self.parse(statement.data[comma_index+1:])
            self.data.extend(items)
