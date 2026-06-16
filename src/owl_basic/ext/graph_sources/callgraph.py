"""The ``callgraph`` graph source: the inter-routine call graph.

Nodes are the program's routines -- the entry points the flow analysis found:
the main program, each ``PROC`` and ``FN``, and each ``GOSUB`` target promoted
to a procedure. Edges are the relationships between routines, classified so the
diagram tells the truth about *unstructured* code rather than pretending it is a
tree:

* ``call``      -- a ``PROC`` / ``FN`` / (converted) ``GOSUB`` call. The real,
                   well-defined call graph; drawn solid.
* ``longjump``  -- a ``GOTO`` that leaves its routine. The flow analysis already
                   identifies these (a control edge whose endpoints carry
                   different entry-point tags) and reifies them as ``LongJump``
                   nodes; drawn red and dotted.
* ``computed``  -- an ``ON ... GOTO`` whose target lies in another routine; a
                   multi-target jump out of the routine. Drawn orange, dashed.
* ``external``  -- a ``CALL <address>`` into machine code, an opaque target.
* ``entangled`` -- two routines that physically *share* statements (a statement
                   the analysis tagged with both routines). The deepest form of
                   unstructuredness; drawn red and dotted between the routines.

Unresolved jump/call targets go to a single ``?`` sink; machine-code targets to
an ``external`` sink, so "we don't know where this goes" is explicit.

A cleanly structured program is a tidy solid graph; spaghetti lights up red.
"""

from itertools import combinations

from owl_basic.ext.graph_sources import _routines
from owl_basic.ext.graph_sources.cfg import _all_statements, _walk
from owl_basic.syntax.ast import (
    Call, CallProcedure, Goto, LongJump, LiteralInteger, OnGoto, UserFunc,
)
from owl_basic.visualise.model import Edge, Graph, Node
from owl_basic.visualise.source import GraphSource

_UNKNOWN = "__unknown__"
_EXTERNAL = "__external__"


def _ego(graph: Graph, centre: str) -> Graph:
    """The neighbourhood of *centre*: it, its callers and callees, their edges.

    Scopes a whole-program call graph to one routine -- every edge incident to
    *centre*, and the routines (and sinks) at the other end.
    """
    kept_nodes = {centre}
    kept_edges = []
    for edge in graph.edges:
        if edge.source == centre or edge.target == centre:
            kept_edges.append(edge)
            kept_nodes.add(edge.source)
            kept_nodes.add(edge.target)
    scoped = Graph(name=graph.name, directed=graph.directed)
    for node in graph.nodes:
        if node.id in kept_nodes:
            scoped.add_node(node)
    for edge in kept_edges:
        scoped.add_edge(edge)
    return scoped


class CallGraphSource(GraphSource):
    """The inter-routine call graph, with unstructured transfers flagged."""

    def build(self, program, options=None) -> Graph:
        self._graph = Graph(name="CallGraph", directed=True)
        self._line_mapper = program.line_mapper
        self._entry_points = program.entry_points
        self._edges = {}        # (source, target, kind) -> count, for dedup
        self._entangled = set()  # frozenset({a, b}) pairs already linked
        self._sinks = set()      # which sink nodes have been created

        # A routine node per entry point, and a tag -> routine-name index so a
        # statement's owning routine(s) can be recovered from its entry-point
        # tags (the analysis records membership there).
        self._tag_to_name = _routines.tag_to_name(program)
        for name in self._entry_points:
            self._graph.add_node(Node(
                id=name, label=_routines.display_name(name),
                kind=_routines.routine_kind(name),
            ))

        for statement in _all_statements(program):
            self._visit(statement)

        for (source, target, kind), count in self._edges.items():
            label = "x%d" % count if kind == "call" and count > 1 else None
            self._graph.add_edge(Edge(source, target, kind=kind, label=label))

        scope = _routines.resolve_routine(program, _routines.routine_option(options))
        return self._graph if scope is None else _ego(self._graph, scope)

    # -- per-statement classification --------------------------------------

    def _visit(self, statement) -> None:
        callers = self._routines_of(statement)
        self._flag_entanglement(callers)

        if isinstance(statement, CallProcedure):
            self._call(callers, statement.name)
        if isinstance(statement, LongJump):
            self._jump(callers, statement.targetLogicalLine, kind="longjump")
        elif isinstance(statement, OnGoto):
            for target_line in self._integer_nodes(statement.targetLogicalLines):
                self._jump(callers, target_line, kind="computed")
        elif isinstance(statement, Goto):
            # A plain Goto that survived longjump conversion is intra-routine
            # (internal flow), so it is not a call-graph edge.
            pass
        if isinstance(statement, Call):
            for caller in callers:
                self._add(caller, self._sink(_EXTERNAL), "external")

        for func in self._user_funcs(statement):
            self._call(callers, func.name)

    def _call(self, callers, callee_name: str) -> None:
        target = callee_name if callee_name in self._entry_points \
            else self._sink(_UNKNOWN)
        for caller in callers:
            self._add(caller, target, "call")

    def _jump(self, callers, target_line, kind: str) -> None:
        target_statement = self._line_mapper.statementOnLine(target_line) \
            if target_line is not None else None
        if target_statement is None:
            for caller in callers:
                self._add(caller, self._sink(_UNKNOWN), kind)
            return
        targets = self._routines_of(target_statement)
        for caller in callers:
            # Only transfers that leave the routine are call-graph edges.
            for target in targets:
                if target != caller:
                    self._add(caller, target, kind)

    # -- helpers -----------------------------------------------------------

    def _routines_of(self, statement) -> list[str]:
        """The routine node ids a statement belongs to (>1 means shared code)."""
        return sorted(_routines.routines_of(statement, self._tag_to_name))

    def _flag_entanglement(self, callers) -> None:
        for a, b in combinations(callers, 2):
            pair = frozenset((a, b))
            if pair not in self._entangled:
                self._entangled.add(pair)
                self._add(a, b, "entangled")

    def _user_funcs(self, statement):
        """The FN-call expression nodes within *statement*'s own subtree."""
        return [node for node in _walk(statement) if isinstance(node, UserFunc)]

    def _integer_nodes(self, node):
        """The LiteralInteger nodes (line numbers) beneath *node*.

        *node* may be a single AST node or a list of them (an ``ON ... GOTO``
        carries its targets as a list child).
        """
        items = node if isinstance(node, list) else [node]
        result = []
        for item in items:
            if item is not None:
                result.extend(n for n in _walk(item) if isinstance(n, LiteralInteger))
        return result

    def _sink(self, sink_id: str) -> str:
        if sink_id not in self._sinks:
            self._sinks.add(sink_id)
            label = "?" if sink_id == _UNKNOWN else "CALL (machine code)"
            self._graph.add_node(Node(id=sink_id, label=label, kind="sink"))
        return sink_id

    def _add(self, source: str, target: str, kind: str) -> None:
        key = (source, target, kind)
        self._edges[key] = self._edges.get(key, 0) + 1
