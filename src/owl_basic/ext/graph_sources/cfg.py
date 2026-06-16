"""The ``cfg`` graph source: the statement-level control-flow graph.

Every program statement is a vertex; edges are control flow between statements,
including loop back-edges. Statements are collected from two complementary
sources, then unioned, so the view is complete:

* a walk of the AST -- which is a single connected component -- catches every
  *written* statement, including any not reachable through control flow;
* a closure over the control-flow edges from those seeds catches the *synthetic*
  vertices that later flow passes (subroutine-to-procedure conversion, longjump
  -to-exception conversion) wire in by edge only, without an AST parent.
"""

from owl_basic.ext.graph_sources import _routines
from owl_basic.ext.graph_sources._statements import (
    StatementLabeller, statement_edges, statement_id, statement_node,
)
from owl_basic.syntax.ast import AstStatement
from owl_basic.visualise.model import Graph
from owl_basic.visualise.source import GraphSource


def _walk(root):
    """Iteratively yield every node in the AST rooted at *root*.

    Iterative (explicit stack) rather than recursive so deep programs do not
    overflow the call stack, matching the rest of the flow tooling.
    """
    stack = [root]
    while stack:
        node = stack.pop()
        if node is None:
            continue
        yield node
        for child in node.children.values():
            if isinstance(child, list):
                stack.extend(child)
            else:
                stack.append(child)


def _all_statements(program):
    """Every statement vertex of the CFG: AST statements and synthetic nodes.

    Seeds are the AST statements and the entry points; the set is then closed
    over outgoing and loop back-edges to reach vertices that exist only in the
    control-flow graph.
    """
    seen = set()
    stack = [n for n in _walk(program.parse_tree) if isinstance(n, AstStatement)]
    stack.extend(program.entry_points.values())
    statements = []
    while stack:
        statement = stack.pop()
        if statement is None or id(statement) in seen:
            continue
        seen.add(id(statement))
        statements.append(statement)
        stack.extend(statement.outEdges)
        stack.extend(statement.loopBackEdges)
    return statements


class CfgSource(GraphSource):
    """The statement-level control-flow graph of the program."""

    def build(self, program, options=None) -> Graph:
        graph = Graph(name="CFG")
        statements = _all_statements(program)

        scope = _routines.resolve_routine(program, _routines.routine_option(options))
        if scope is not None:
            mapping = _routines.tag_to_name(program)
            statements = [s for s in statements
                          if scope in _routines.routines_of(s, mapping)]

        labeller = StatementLabeller(program)
        for statement in statements:
            graph.add_node(statement_node(statement, labeller))
        # Keep only edges between surviving statements, so a scoped view does
        # not dangle into routines that were filtered out.
        kept = {statement_id(s) for s in statements}
        for statement in statements:
            for edge in statement_edges(statement):
                if edge.target in kept:
                    graph.add_edge(edge)
        return graph
