class Node(object):
    def __init__(self, nodeType=None, formalType=None, description="A parameter"):
        self._node_type = nodeType
        self._formal_type = formalType
        self._description = description
    
    def _getNodeType(self):
        return self._node_type
    
    nodeType = property(_getNodeType)
        
    def _getFormalType(self):
        return self._formal_type
    
    formalType = property(_getFormalType)
    
    def _getDescription(self):
        return self._description
    
    description = property(_getDescription)
  