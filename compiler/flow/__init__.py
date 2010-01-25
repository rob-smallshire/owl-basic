'''
Package for analysing and manipulating control flow.
'''

from entry_point_locator import locateEntryPoints
from flow_graph_creator import createForwardControlFlowGraph

__all__ = ["locateEntryPoints",
           "createForwardControlFlowGraph"]
