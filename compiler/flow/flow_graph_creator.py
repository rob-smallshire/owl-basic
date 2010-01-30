'''
Creation of the forward control flow graph
'''

import logging

from flowgraph_visitor import FlowgraphForwardVisitor

logger = logging.getLogger('flow.flow_graph_creator')

def createForwardControlFlowGraph(parse_tree, line_mapper, options):
    logger.debug("flowgraph")
    logger.info("Creating Control Flow Graph...")
    parse_tree.accept(FlowgraphForwardVisitor(line_mapper))
