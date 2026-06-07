import logging
from owl_basic.visitor import Visitor

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
        """Split the text following a DATA statement into comma-separated items.

        Commas delimit items, so N commas yield N+1 items: empty items between
        adjacent commas (or a trailing comma) are significant -- READ returns
        ""/0 for them and they keep sequential READ and RESTORE offsets aligned
        with the real interpreter. A double-quoted item may contain commas; ""
        inside quotes is a literal quote, and any characters between the closing
        quote and the next comma are ignored. Leading whitespace is stripped
        from unquoted items; trailing whitespace is stripped only from the final
        item (which runs to the end of the line).
        """
        items = []
        last_was_quoted = False
        i, n = 0, len(data)
        while True:
            # Skip leading spaces to see whether this item is quoted.
            j = i
            while j < n and data[j] == ' ':
                j += 1
            if j < n and data[j] == '"':
                j += 1
                chars = []
                while j < n:
                    if data[j] == '"':
                        if j + 1 < n and data[j + 1] == '"':
                            chars.append('"')
                            j += 2
                            continue
                        j += 1
                        break
                    chars.append(data[j])
                    j += 1
                items.append(''.join(chars))
                last_was_quoted = True
                # Ignore anything between the closing quote and the next comma.
                while j < n and data[j] != ',':
                    j += 1
            else:
                k = data.find(',', i)
                if k == -1:
                    k = n
                items.append(data[i:k].lstrip())
                last_was_quoted = False
                j = k
            if j >= n:
                break
            i = j + 1  # consume the comma and continue with the next field
        if items and not last_was_quoted:
            items[-1] = items[-1].rstrip()
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
