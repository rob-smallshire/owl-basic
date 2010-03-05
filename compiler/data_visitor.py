import logging
import re
from visitor import Visitor

class DataVisitor(Visitor):
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
       