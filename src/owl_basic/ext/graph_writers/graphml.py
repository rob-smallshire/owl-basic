"""The ``graphml`` graph writer: yEd / yFiles GraphML.

Produces GraphML carrying yWorks node/edge graphics, so the output opens in yEd
with shapes already applied: entry points are hexagons, branches diamonds, plain
statements round rectangles, and basic blocks become yEd group nodes enclosing
their statements. Back-edges are drawn dashed.

This reimplements the legacy ``.NET`` ``System.Xml`` emitters on the standard
library's :mod:`xml.etree.ElementTree`, so it needs no IronPython/CLR.
"""

import xml.etree.ElementTree as ET

from owl_basic.visualise.writer import GraphWriter

_GRAPHML_NS = "http://graphml.graphdrawing.org/xmlns"
_Y_NS = "http://www.yworks.com/xml/graphml"
_XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
_SCHEMA_LOCATION = (
    "http://graphml.graphdrawing.org/xmlns "
    "http://www.yworks.com/xml/schema/graphml/1.0/ygraphml.xsd"
)

_NODE_SHAPE = {
    "entry": "hexagon",
    "decision": "diamond",
    "statement": "roundrectangle",
    # Call-graph node kinds.
    "main": "hexagon",
    "proc": "roundrectangle",
    "sub": "roundrectangle",
    "fn": "ellipse",
    "sink": "roundrectangle",
}

# Per-edge-kind yFiles line style: (LineStyle type, colour). Absent kinds draw
# as a plain solid black arrow.
_EDGE_LINE = {
    "back": ("dashed", None),
    "longjump": ("dotted", "#FF0000"),
    "computed": ("dashed", "#FF8C00"),
    "external": ("dashed", "#808080"),
    "entangled": ("dotted", "#FF0000"),
}

ET.register_namespace("", _GRAPHML_NS)
ET.register_namespace("y", _Y_NS)
ET.register_namespace("xsi", _XSI_NS)


def _g(tag: str) -> str:
    return "{%s}%s" % (_GRAPHML_NS, tag)


def _y(tag: str) -> str:
    return "{%s}%s" % (_Y_NS, tag)


class GraphMLWriter(GraphWriter):
    """yEd-compatible GraphML output (yFiles node and edge graphics)."""

    @classmethod
    def file_extension(cls) -> str:
        return ".graphml"

    def write(self, graph, stream) -> None:
        root = ET.Element(_g("graphml"))
        root.set("{%s}schemaLocation" % _XSI_NS, _SCHEMA_LOCATION)
        self._write_keys(root)

        graph_el = ET.SubElement(root, _g("graph"))
        graph_el.set("id", graph.name)
        graph_el.set("edgedefault", "directed" if graph.directed else "undirected")

        for node in graph.children_of(None):
            if node.kind == "block":
                self._write_group(graph_el, graph, node)
            else:
                self._write_node(graph_el, node)

        # Edges live at the top level; GraphML permits them to reference nodes
        # nested inside group subgraphs.
        for edge in graph.edges:
            self._write_edge(graph_el, edge)

        tree = ET.ElementTree(root)
        ET.indent(tree)
        tree.write(stream, encoding="unicode", xml_declaration=True)
        stream.write("\n")

    def _write_keys(self, root) -> None:
        for key_id, for_, attrs in (
            ("d0", "node", {"yfiles.type": "nodegraphics"}),
            ("d1", "node", {"attr.name": "description", "attr.type": "string"}),
            ("d3", "edge", {"yfiles.type": "edgegraphics"}),
            ("d4", "graphml", {"yfiles.type": "resources"}),
        ):
            key = ET.SubElement(root, _g("key"))
            key.set("id", key_id)
            key.set("for", for_)
            for name, value in attrs.items():
                key.set(name, value)

    def _write_node(self, parent, node) -> None:
        node_el = ET.SubElement(parent, _g("node"))
        node_el.set("id", node.id)

        data = ET.SubElement(node_el, _g("data"))
        data.set("key", "d0")
        shape_node = ET.SubElement(data, _y("ShapeNode"))
        if node.kind == "sink":
            ET.SubElement(shape_node, _y("Fill")).set("color", "#D3D3D3")
        ET.SubElement(shape_node, _y("NodeLabel")).text = node.label
        shape = ET.SubElement(shape_node, _y("Shape"))
        shape.set("type", _NODE_SHAPE.get(node.kind, "roundrectangle"))

        description = node.attrs.get("description")
        if description is not None:
            desc = ET.SubElement(node_el, _g("data"))
            desc.set("key", "d1")
            desc.text = description

    def _write_group(self, parent, graph, group) -> None:
        node_el = ET.SubElement(parent, _g("node"))
        node_el.set("id", group.id)
        node_el.set("yfiles.foldertype", "group")

        data = ET.SubElement(node_el, _g("data"))
        data.set("key", "d0")
        proxy = ET.SubElement(data, _y("ProxyAutoBoundsNode"))
        realizers = ET.SubElement(proxy, _y("Realizers"))
        realizers.set("active", "0")
        group_node = ET.SubElement(realizers, _y("GroupNode"))
        ET.SubElement(group_node, _y("NodeLabel")).text = group.label
        ET.SubElement(group_node, _y("Shape")).set("type", "roundrectangle")

        subgraph = ET.SubElement(node_el, _g("graph"))
        subgraph.set("id", group.id + ":")
        subgraph.set("edgedefault", "directed")
        for member in graph.children_of(group.id):
            self._write_node(subgraph, member)

    def _write_edge(self, parent, edge) -> None:
        edge_el = ET.SubElement(parent, _g("edge"))
        edge_el.set("source", edge.source)
        edge_el.set("target", edge.target)

        data = ET.SubElement(edge_el, _g("data"))
        data.set("key", "d3")
        poly = ET.SubElement(data, _y("PolyLineEdge"))
        arrows = ET.SubElement(poly, _y("Arrows"))
        arrows.set("source", "none")
        # An entangled link is a symmetric "shares code" relation, not a
        # directed call, so it carries no arrowhead.
        arrows.set("target", "none" if edge.kind == "entangled" else "standard")
        style_type, colour = _EDGE_LINE.get(edge.kind, ("line", None))
        line = ET.SubElement(poly, _y("LineStyle"))
        line.set("type", style_type)
        if colour is not None:
            line.set("color", colour)
        if edge.label:
            ET.SubElement(poly, _y("EdgeLabel")).text = edge.label
