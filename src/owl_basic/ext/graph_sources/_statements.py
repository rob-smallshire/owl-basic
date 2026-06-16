"""Shared helpers for sources that render program *statements*.

Both the control-flow and basic-block views draw the same statement vertices
and the same control-flow edges between them; they differ only in whether the
statements are grouped into basic blocks. These helpers keep that shared
classification in one place.
"""

from owl_basic.syntax.ast import AstStatement, If, OnGoto
from owl_basic.visualise.model import Edge, Node


def statement_id(statement) -> str:
    """A graph-unique node id for a statement vertex."""
    return "s%d" % statement.id


def _logical_line(line_mapper, statement):
    """The BBC (logical) line number for a statement, or its physical line.

    ``statement.lineNum`` is a *physical* line index into the detokenised
    listing; the logical line is the number as listed and as GOTO/GOSUB target.
    Bounds are checked explicitly so a synthetic statement with an out-of-range
    or absent line falls back to its physical line rather than raising.
    """
    physical = statement.lineNum
    table = line_mapper.physical_to_logical_map
    if physical is not None and table is not None and 0 <= physical < len(table):
        return table[physical]
    return physical


def _ordered_statements(root):
    """Yield every AST statement under *root* in source (document) order.

    Iterative pre-order (children pushed reversed so they pop in order) to avoid
    overflowing the stack on deep programs, matching the rest of the flow tooling.
    """
    stack = [root]
    while stack:
        node = stack.pop()
        if node is None:
            continue
        if isinstance(node, AstStatement):
            yield node
        children = []
        for child in node.children.values():
            if isinstance(child, list):
                children.extend(child)
            else:
                children.append(child)
        stack.extend(reversed(children))


class StatementLabeller:
    """Labels statements ``<logical line>.<ordinal>`` (e.g. ``438.3``).

    BBC BASIC packs several statements onto one numbered line, so the logical
    line alone is ambiguous; the ordinal numbers the statements sharing a line
    in source order. Built once per graph from the program's AST and line map.
    """

    def __init__(self, program):
        self._line_mapper = program.line_mapper
        self._line_of = {}
        self._ordinal = {}
        counts = {}
        for statement in _ordered_statements(program.parse_tree):
            logical = _logical_line(self._line_mapper, statement)
            counts[logical] = counts.get(logical, 0) + 1
            self._line_of[id(statement)] = logical
            self._ordinal[id(statement)] = counts[logical]

    def line_label(self, statement) -> str:
        key = id(statement)
        if key in self._ordinal:
            return "%s.%d" % (self._line_of[key], self._ordinal[key])
        # A synthetic statement not present in the AST: best-effort logical line.
        return str(_logical_line(self._line_mapper, statement))


def statement_kind(statement) -> str:
    """Classify a statement for shape selection.

    ``"entry"`` for a procedure/program entry point, ``"decision"`` for a
    branch (``IF`` / ``ON ... GOTO``), otherwise ``"statement"`` -- mirroring
    the hexagon/diamond/round-rectangle distinction of the legacy emitters.
    """
    if hasattr(statement, "entryPoint"):
        return "entry"
    if isinstance(statement, (If, OnGoto)):
        return "decision"
    return "statement"


def statement_node(statement, labeller: "StatementLabeller",
                   group: str | None = None) -> Node:
    """A neutral graph :class:`Node` for *statement*."""
    attrs = {"description": statement.description}
    if statement.entryPoints:
        attrs["entryPoints"] = ";".join(statement.entryPoints)
    return Node(
        id=statement_id(statement),
        label="%s: %s" % (labeller.line_label(statement), statement.description),
        kind=statement_kind(statement),
        group=group,
        attrs=attrs,
    )


def statement_edges(statement):
    """Yield the outgoing control-flow and loop back-edges of *statement*."""
    for target in statement.outEdges:
        yield Edge(statement_id(statement), statement_id(target), kind="flow")
    for target in statement.loopBackEdges:
        yield Edge(statement_id(statement), statement_id(target), kind="back")
