"""The ``blocks`` graph source: the basic-block graph.

The same statements and control-flow edges as the ``cfg`` view, but with the
statements grouped into the basic blocks identified by flow analysis. Each
basic block is a group node (labelled with its topological order) enclosing its
statements; writers render groups as yEd group nodes or DOT clusters.
"""

from owl_basic.ext.graph_sources import _routines
from owl_basic.ext.graph_sources._statements import (
    StatementLabeller, statement_edges, statement_id, statement_node,
)
from owl_basic.visualise.model import Graph, Node
from owl_basic.visualise.source import GraphSource


def _block_id(block) -> str:
    return "b%d" % block.id


class BlocksSource(GraphSource):
    """The basic-block graph: statements grouped into basic blocks."""

    def build(self, program, options=None) -> Graph:
        graph = Graph(name="BasicBlocks")
        # ordered_basic_blocks maps each entry-point name to its blocks in
        # approximate topological order. Scope to one routine by taking just its
        # entry; otherwise take every routine's blocks.
        scope = _routines.resolve_routine(program, _routines.routine_option(options))
        if scope is not None:
            entries = [program.ordered_basic_blocks.get(scope, [])]
        else:
            entries = program.ordered_basic_blocks.values()

        # A block belongs to one entry point's graph, but dedupe by id defensively.
        seen = set()
        blocks = []
        for entry_blocks in entries:
            for block in entry_blocks:
                if block.id not in seen:
                    seen.add(block.id)
                    blocks.append(block)

        labeller = StatementLabeller(program)
        for block in blocks:
            graph.add_node(Node(
                id=_block_id(block),
                label=str(block.topological_order),
                kind="block",
            ))
            for statement in block.statements:
                graph.add_node(
                    statement_node(statement, labeller, group=_block_id(block)))

        # Keep only edges between surviving statements, so a scoped view does
        # not dangle into blocks that were filtered out.
        kept = {statement_id(s) for block in blocks for s in block.statements}
        for block in blocks:
            for statement in block.statements:
                for edge in statement_edges(statement):
                    if edge.target in kept:
                        graph.add_edge(edge)
        return graph
