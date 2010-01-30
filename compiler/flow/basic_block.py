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
        self.statements = []

    ''' The first statement in the BasicBlock, or None'''
    entryPoint = property(lambda self: self.statements[0] if len(self.statements) > 0 else None)
    
    '''The last statement in the BasicBlock, or None'''
    exitPoint = property(lambda self: self.statements[-1] if len(self.statements) > 0 else None)
    
    def __len__(self):
        return len(self.statements)
    
        
        