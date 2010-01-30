'''
Package for analysing and manipulating control flow.
'''

from entry_point_locator import locateEntryPoints
from flow_graph_creator import createForwardControlFlowGraph
from longjump_converter import convertLongjumpsToExceptions
from subroutine_converter import convertSubroutinesToProcedures
from basic_block_identifier import identifyBasicBlocks

__all__ = ["locateEntryPoints",
           "createForwardControlFlowGraph",
           "convertLongjumpsToExceptions",
           "convertSubroutinesToProcedures",
           "identifyBasicBlocks"]

