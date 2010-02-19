'''
Created on 9 Feb 2010

@author: rjs
'''
import logging
logger = logging.getLogger('flow.basic_block_orderer')

from traversal import approximateTopologicalOrder

def orderBasicBlocks(basic_blocks, options):
    '''
    :param basic_blocks: A dictionary of entry blocks - BasicBlock instances through which control
                         flow enters the graph of each program, function or procedure. The keys are
                         the entry point names.
    :param options: Command line options
    :returns: A dictionary of lists of basic blocks in approximate topological order. Keys are entry_point names
    '''
    ordered_blocks = {}
    for name, basic_block in basic_blocks.items():
        logger.debug(name)
        order = approximateTopologicalOrder(basic_block)
        print "order = ", order
        for i, block in enumerate(order):
            block.topological_order = i
        ordered_blocks[name] = order
    return ordered_blocks

        