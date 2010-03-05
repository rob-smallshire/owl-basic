'''
Grouping of statements into basic blocks - resulting in a coarser grained control flow graph
'''
import logging
logger = logging.getLogger('flow.basic_block_identifier')
logger.setLevel(logging.WARNING)

from connectors import connect
from traversal import depthFirstSearch
from basic_block import BasicBlock

def identifyBasicBlocks(entry_points, options):
    '''
    Trace the control flow graph from each entry point and collect consecutive statements
    into basic blocks, comprising a more coarse grained control flow graph. This function applies
    a transformation to the statement level basic block, coarsening it by grouping statements into
    a graph consisting only of BasicBlock instances.  Each BasicBlock instance contains a list of
    non-branching, or non-branch target statements.
    
    A basic block is code that has one entry point (i.e., no code within it is the destination
    of a jump instruction), one exit point and no jump instructions contained within it. The
    start of a basic block may be jumped to from more than one location. The end of a basic block
    may be a jump instruction or the statement before the destination of a jump instruction. Basic
    blocks are usually the basic unit to which compiler optimizations are applied. Basic blocks
    form the vertices or nodes in a control flow graph.
    
    :param entry_points: A sequence of program statements which are the entry point to the program
                         or procedures
    :param options:      Program options
    :returns:            A dictionary of entry blocks - BasicBlock instances through which control
                         flow enters the graph of each program, function or procedure. The keys are
                         the entry point names
    '''
    logger.info("Identifying basic blocks")
    print entry_points
    return dict((k, coarsenControlFlowGraph(v)) for k, v in entry_points.items())
        
def coarsenControlFlowGraph(entry_point):
    '''
    Coarsen the control flow graph starting at the entry_point to consist of BasicBlocks
    :param entry_point: A program statement which is the entry point to the program, procedure or function
                        for which the control flow graph is to be coarsened to basic blocks.
    :returns: The entry block BasicBlock instance corresponding to entry_point
    '''
    logger.debug("entry_point = %s", entry_point)
    block = assignBlockAndContinue(entry_point)
    return block

# TODO: Decorate as a tail-call    
def assignBlockAndContinue(vertex, block=None):
    '''
    Assign vertex to block and continue with successor vertices
    '''
    if not vertex.block:           
        block = ((vertex.inDegree == 1) and block) or BasicBlock()
        block.statements.append(vertex)
        vertex.block = block
        logger.debug("%s with in-degree %s and out-degree %s at %s in %s", vertex, str(vertex.inDegree), str(vertex.outDegree), str(vertex.lineNum), vertex.block)
        for target in vertex.outEdges:
            successor_block = assignBlockAndContinue(target, block if vertex.outDegree == 1 else None)
            if block is not successor_block:
                connect(block, successor_block)             
    return vertex.block
           
    
        