class Node(object):
    def __init__(self, formalType=None, description="A parameter"):
        self._formal_type = formalType
        self._description = description
        
    def _getFormalType(self):
        return self._formal_type
    
    formalType = property(_getFormalType)
    
    def _getDescription(self):
        return self._description
    
    description = property(_getDescription)
  