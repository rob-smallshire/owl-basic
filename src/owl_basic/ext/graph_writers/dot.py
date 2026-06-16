"""The ``dot`` graph writer: GraphViz DOT.

Renders the neutral graph as a ``digraph`` for GraphViz. Node ``kind`` maps to a
shape (entry -> hexagon, decision -> diamond, statement -> rounded box); groups
become ``cluster`` subgraphs; back-edges are drawn dashed and grey.

    owl-basic visualise cfg prog.bbc -f dot -o - | dot -Tsvg -o prog.svg
"""

from owl_basic.visualise.writer import GraphWriter

_NODE_SHAPE = {
    "entry": ("hexagon", None),
    "decision": ("diamond", None),
    "statement": ("box", "rounded"),
    # Call-graph node kinds.
    "main": ("hexagon", None),
    "proc": ("box", "rounded"),
    "sub": ("box", "rounded"),
    "fn": ("ellipse", None),
    "sink": ("note", "filled"),
}

# Per-edge-kind styling (GraphViz attributes). Absent kinds draw as a plain
# solid arrow.
_EDGE_STYLE = {
    "back": {"style": "dashed", "color": "grey"},
    "longjump": {"style": "dotted", "color": "red"},
    "computed": {"style": "dashed", "color": "orange"},
    "external": {"style": "dashed", "color": "grey"},
    "entangled": {"style": "dotted", "color": "red", "dir": "none", "constraint": "false"},
}


def _quote(text: str) -> str:
    """Quote a string as a DOT double-quoted ID."""
    escaped = str(text).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return '"%s"' % escaped


class DotWriter(GraphWriter):
    """GraphViz DOT output, for ``dot``/``neato`` and friends."""

    @classmethod
    def file_extension(cls) -> str:
        return ".dot"

    def write(self, graph, stream) -> None:
        keyword = "digraph" if graph.directed else "graph"
        self._connector = "->" if graph.directed else "--"
        stream.write("%s %s {\n" % (keyword, _quote(graph.name)))
        stream.write("  node [fontname=\"Helvetica\"];\n")

        for group in (node for node in graph.nodes if node.kind == "block"):
            stream.write("  subgraph %s {\n" % _quote("cluster_" + group.id))
            stream.write("    label=%s;\n" % _quote(group.label))
            for member in graph.children_of(group.id):
                stream.write("    " + self._node_line(member))
            stream.write("  }\n")

        for node in graph.children_of(None):
            if node.kind != "block":
                stream.write("  " + self._node_line(node))

        for edge in graph.edges:
            stream.write("  " + self._edge_line(edge))

        stream.write("}\n")

    def _node_line(self, node) -> str:
        shape, style = _NODE_SHAPE.get(node.kind, ("box", None))
        attrs = ["label=%s" % _quote(node.label), "shape=%s" % shape]
        if style:
            attrs.append("style=%s" % style)
        if node.kind == "sink":
            attrs.append("fillcolor=lightgrey")
        return "%s [%s];\n" % (_quote(node.id), ", ".join(attrs))

    def _edge_line(self, edge) -> str:
        attrs = []
        if edge.label:
            attrs.append("label=%s" % _quote(edge.label))
        for name, value in _EDGE_STYLE.get(edge.kind, {}).items():
            attrs.append("%s=%s" % (name, value))
        suffix = " [%s]" % ", ".join(attrs) if attrs else ""
        return "%s %s %s%s;\n" % (
            _quote(edge.source), self._connector, _quote(edge.target), suffix)
