"""The ``ast`` graph source: the abstract syntax tree.

Every AST node is a vertex; edges run from a node to each of its children,
labelled with the child slot (and index, for list slots). Unlike the cfg/blocks
views -- which draw only statements and control flow -- this shows the full
parse-tree structure, expressions included.

With ``-r`` the tree is rooted at one routine's definition (the whole program
for MAIN), which is the only way the AST of a large program stays legible.
"""

from owl_basic.ext.graph_sources import _routines
from owl_basic.ext.graph_sources._statements import _ordered_statements, statement_kind
from owl_basic.syntax.ast import AstStatement
from owl_basic.utility import underscoresToCamelCase
from owl_basic.visualise.model import Edge, Graph, Node
from owl_basic.visualise.source import GraphSource

# Options carried on every node but not worth drawing.
_HIDDEN_OPTIONS = frozenset(("formal_type", "actual_type", "line_num"))


def _ast_kind(node) -> str:
    """Shape class for an AST node: statements reuse the cfg classification."""
    if isinstance(node, AstStatement):
        return statement_kind(node)
    return "node"


def _ast_label(node) -> str:
    """The node's class name plus its salient scalar options (value, name, ...)."""
    label = type(node).__name__
    parts = []
    for name, value in node.options.items():
        if name in _HIDDEN_OPTIONS:
            continue
        if isinstance(value, (str, int, float, bool)) and value != "":
            parts.append("%s=%r" % (underscoresToCamelCase(name), value))
    if parts:
        label += " " + " ".join(parts)
    return label


class AstSource(GraphSource):
    """The abstract syntax tree, optionally rooted at one routine."""

    def build(self, program, options=None) -> Graph:
        graph = Graph(name="AST")
        roots, boundary = self._roots(program, options)

        ids = {}

        def node_id(node) -> str:
            key = id(node)
            if key not in ids:
                ids[key] = "n%d" % len(ids)
            return ids[key]

        # Pre-order DFS that emits nodes and edges left-to-right in source order:
        # roots and each node's children are pushed reversed so they pop (and so
        # are declared to GraphViz) in their natural order.
        seen = set()
        stack = list(reversed(roots))
        while stack:
            node = stack.pop()
            if node is None or id(node) in seen:
                continue
            # When scoped, don't wander out of the routine: a statement is only
            # followed if it is one of the routine's own (expressions, which are
            # not statements, are always followed).
            if boundary is not None and isinstance(node, AstStatement) \
                    and id(node) not in boundary:
                continue
            seen.add(id(node))
            graph.add_node(Node(
                id=node_id(node), label=_ast_label(node), kind=_ast_kind(node),
            ))
            children = []
            for slot, child in node.children.items():
                name = underscoresToCamelCase(slot)
                if isinstance(child, list):
                    for index, item in enumerate(child):
                        self._link(graph, node_id, node, item, "%s[%d]" % (name, index))
                        children.append(item)
                else:
                    self._link(graph, node_id, node, child, name)
                    children.append(child)
            stack.extend(reversed(children))
        return graph

    def _link(self, graph, node_id, parent, child, label) -> None:
        if child is not None:
            graph.add_edge(Edge(node_id(parent), node_id(child), kind="child", label=label))

    def _roots(self, program, options):
        """The traversal roots and an optional statement boundary.

        Whole program: the single Program root, no boundary. Scoped to a
        routine: a forest of that routine's statements (BBC BASIC routines are
        sibling statements joined by control flow, not an AST subtree), with a
        boundary so traversal stays within them.
        """
        scope = _routines.resolve_routine(program, _routines.routine_option(options))
        if scope is None:
            return [program.parse_tree], None
        mapping = _routines.tag_to_name(program)
        members = [s for s in _ordered_statements(program.parse_tree)
                   if scope in _routines.routines_of(s, mapping)]
        return members, {id(s) for s in members}
