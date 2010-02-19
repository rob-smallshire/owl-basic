'''
Created on 30 Jan 2010

@author: rjs
'''

from cfg_vertex import CfgVertex

class BasicBlock(CfgVertex):
    '''
    A sequence of statements with a single entry and exit point
    '''

    def __init__(self, statements=[], *args, **kwargs):
        '''
        :param statements: A list of statements comprising the basic block
        '''
        super(BasicBlock, self).__init__(*args, **kwargs)
        self.statements = [] # The list of statements comprising the basic block
        self.topological_order = None # Integer giving ordinal position in method
        self.label = None # A label into which can be branched to, to enter this basic block
        self.is_label_marked = False # A flag for whether the label has been marked
        
    ''' The first statement in the BasicBlock, or None'''
    entryPoint = property(lambda self: self.statements[0] if len(self.statements) > 0 else None)
    
    '''The last statement in the BasicBlock, or None'''
    exitPoint = property(lambda self: self.statements[-1] if len(self.statements) > 0 else None)
    
    def __len__(self):
        return len(self.statements)
    
        
        