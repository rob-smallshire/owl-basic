'''
Grouping of statements into basic blocks - resulting in a coarser grained control flow graph
'''
import logging
logger = logging.getLogger('flow.basic_block_identifier')
logger.setLevel(logging.WARNING)

from .connectors import connect
from .traversal import depthFirstSearch
from .basic_block import BasicBlock

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
    logging.debug("entry points: %s", entry_points)
    return dict((k, coarsenControlFlowGraph(v)) for k, v in list(entry_points.items()))
        
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

def assignBlockAndContinue(vertex, block=None):
    '''
    Assign vertex to a basic block and continue with successor vertices.

    Done iteratively (an explicit stack rather than recursion) so deep control
    flow graphs do not overflow the call stack: first assign every reachable
    vertex to a block, then wire up the block-level edges. ``connect`` is
    idempotent because the CFG edge collections are sets.
    '''
    entry_vertex = vertex
    stack = [(vertex, block)]
    reached = []
    while stack:
        current, candidate = stack.pop()
        if not current.block:
            current.block = ((current.inDegree == 1) and candidate) or BasicBlock()
            current.block.statements.append(current)
            reached.append(current)
            logger.debug("%s with in-degree %s and out-degree %s at %s in %s", current, str(current.inDegree), str(current.outDegree), str(current.lineNum), current.block)
            # A successor continues the current block only on a straight-line
            # chain. An IF is a conditional branch even when one side falls off
            # the end of the program (out-degree 1: its only edge is the taken
            # clause) -- so its successor must start a fresh block, or codegen
            # would branch into the IF's own block and loop.
            chains = current.outDegree == 1 and type(current).__name__ != "If"
            # outEdges is a set of vertices, whose iteration order varies run to
            # run; visit in stable id order so block membership -- and hence the
            # emitted block layout -- is reproducible.
            for target in sorted(current.outEdges, key=lambda vertex: vertex.id):
                stack.append((target, current.block if chains else None))
    for current in reached:
        for target in current.outEdges:
            if current.block is not target.block:
                connect(current.block, target.block)
    return entry_vertex.block
           
    
        