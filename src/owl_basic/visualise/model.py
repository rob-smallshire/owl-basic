"""A neutral, format-agnostic graph model.

Graph *sources* build one of these from an analysed program; graph *writers*
render it. The model deliberately knows nothing about either side: nodes and
edges carry a *kind* -- a short semantic tag such as ``"entry"``, ``"decision"``
or ``"back"`` -- and writers decide how each kind looks (a hexagon, a dashed
arrow, and so on). Optional grouping lets a source nest nodes (statements within
a basic block); writers render groups as yEd group nodes or DOT clusters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Node:
    """A vertex in a neutral graph.

    Args:
        id: A graph-unique identifier (used as the node's key in the output).
        label: Human-readable text drawn in the node.
        kind: A short semantic tag a writer maps to a shape/style
            (e.g. ``"entry"``, ``"decision"``, ``"statement"``, ``"block"``).
        group: The id of an enclosing group node, or ``None`` for a top-level
            node. The enclosing node should itself be a :class:`Node` in the
            graph (typically of kind ``"block"``).
        attrs: Arbitrary extra attributes, surfaced by writers that can carry
            them (e.g. GraphML data keys).
    """

    id: str
    label: str
    kind: str = "node"
    group: str | None = None
    attrs: dict[str, Any] = field(default_factory=dict)


@dataclass
class Edge:
    """A directed edge from ``source`` to ``target``.

    ``kind`` tags the edge for the writer (e.g. ``"flow"`` for ordinary control
    flow, ``"back"`` for a loop back-edge); ``label`` is optional edge text.
    """

    source: str
    target: str
    kind: str = "flow"
    label: str | None = None


@dataclass
class Graph:
    """A neutral directed (by default) graph of :class:`Node`/:class:`Edge`.

    Nodes are kept in insertion order and indexed by id, so a source can add a
    group node and then its members, and a writer can recover the nesting.
    """

    name: str = "G"
    directed: bool = True
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)

    def __post_init__(self):
        self._by_id: dict[str, Node] = {}
        for node in self.nodes:
            self._by_id[node.id] = node

    def add_node(self, node: Node) -> Node:
        """Add *node*, replacing any existing node with the same id."""
        if node.id in self._by_id:
            existing = self._by_id[node.id]
            self.nodes[self.nodes.index(existing)] = node
        else:
            self.nodes.append(node)
        self._by_id[node.id] = node
        return node

    def add_edge(self, edge: Edge) -> Edge:
        self.edges.append(edge)
        return edge

    def node(self, node_id: str) -> Node | None:
        """The node with *node_id*, or ``None``."""
        return self._by_id.get(node_id)

    def children_of(self, group_id: str | None) -> list[Node]:
        """The nodes whose ``group`` is *group_id* (top-level when ``None``)."""
        return [node for node in self.nodes if node.group == group_id]
