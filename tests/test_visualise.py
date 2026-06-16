"""Program visualisation: the graph sources, writers and the visualise CLI.

The ``cfg`` and ``blocks`` sources build a neutral graph from an analysed
program; the ``graphml`` and ``dot`` writers render it. None of this needs the
.NET toolchain, so it runs anywhere the front end does.
"""

import io
import os
import xml.etree.ElementTree as ET

import pytest
from click.testing import CliRunner

from owl_basic.analysis import analyse, analyse_numbered_lines
from owl_basic.cli import cli
from owl_basic.extension import create_extension, list_extensions
from owl_basic.visualise.model import Edge, Graph, Node

_GRAPH_SOURCE_NS = "owl_basic.graph_source"
_GRAPH_WRITER_NS = "owl_basic.graph_writer"

# A small program exercising an entry point (the implicit main / the FOR),
# a decision (IF) and a loop back-edge (NEXT -> FOR).
_PROGRAM = 'FOR I%=1 TO 10\nIF I%=5 THEN PRINT "five" ELSE PRINT I%\nNEXT I%\nEND\n'


def _analyse():
    return analyse(_PROGRAM, name="demo", source_filepath="demo.bas")


def _source(name):
    return create_extension("graph_source", _GRAPH_SOURCE_NS, name)


def _writer(name):
    return create_extension("graph_writer", _GRAPH_WRITER_NS, name)


# -- model -----------------------------------------------------------------

def test_graph_add_node_is_idempotent_on_id():
    graph = Graph()
    graph.add_node(Node("a", "first"))
    graph.add_node(Node("a", "second"))
    assert len(graph.nodes) == 1
    assert graph.node("a").label == "second"


def test_graph_children_of_groups_by_membership():
    graph = Graph()
    graph.add_node(Node("g", "grp", kind="block"))
    graph.add_node(Node("a", "a", group="g"))
    graph.add_node(Node("b", "b"))
    assert [n.id for n in graph.children_of("g")] == ["a"]
    assert [n.id for n in graph.children_of(None)] == ["g", "b"]


# -- sources ---------------------------------------------------------------

def test_cfg_labels_use_logical_line_and_source_ordinal():
    # BBC line 10 carries three statements; the label is the logical (BBC) line
    # number with a per-statement ordinal in source order, so they read
    # 10.1, 10.2, 10.3 -- not the physical line index.
    program = analyse_numbered_lines(
        [(10, "X%=1:Y%=2:PRINT X%"), (20, "END")],
        name="t", source_filepath="t.bas", strict=False,
    )
    labels = {n.label for n in _source("cfg").build(program).nodes}
    assert any(label.startswith("10.1:") for label in labels)
    assert any(label.startswith("10.2:") for label in labels)
    assert any(label.startswith("10.3:") for label in labels)
    assert any(label.startswith("20.1:") for label in labels)


def test_cfg_source_covers_every_statement_and_classifies_kinds():
    graph = _source("cfg").build(_analyse())
    kinds = {node.kind for node in graph.nodes}
    assert "entry" in kinds      # the FOR is the main entry point
    assert "decision" in kinds   # the IF
    assert "statement" in kinds  # the PRINTs / END
    # The loop produces a back-edge (NEXT -> FOR).
    assert any(edge.kind == "back" for edge in graph.edges)
    assert all(edge.kind in ("flow", "back") for edge in graph.edges)


def test_blocks_source_groups_statements_into_blocks():
    graph = _source("blocks").build(_analyse())
    blocks = [node for node in graph.nodes if node.kind == "block"]
    assert blocks
    # Every non-block node belongs to a block, and that block exists.
    block_ids = {node.id for node in blocks}
    members = [node for node in graph.nodes if node.kind != "block"]
    assert members
    assert all(node.group in block_ids for node in members)


def test_block_statements_are_a_subset_of_the_cfg():
    # Built from the SAME analysis (statement ids are unique per analysis run),
    # the blocks' statements are a subset of the cfg's: the cfg view unions the
    # AST statements with the synthetic flow nodes the blocks view also covers.
    program = _analyse()
    cfg = _source("cfg").build(program)
    blocks = _source("blocks").build(program)
    cfg_statements = {n.id for n in cfg.nodes}
    block_statements = {n.id for n in blocks.nodes if n.kind != "block"}
    assert block_statements
    assert block_statements <= cfg_statements


# -- writers ---------------------------------------------------------------

def _render(source_name, writer_name):
    graph = _source(source_name).build(_analyse())
    stream = io.StringIO()
    _writer(writer_name).write(graph, stream)
    return stream.getvalue()


def test_graphml_is_well_formed_and_yfiles_styled():
    for source_name in ("cfg", "blocks"):
        text = _render(source_name, "graphml")
        root = ET.fromstring(text)  # parses => well-formed
        assert root.tag.endswith("}graphml")
        assert "yworks" in text  # carries yFiles graphics


def test_graphml_blocks_use_yed_group_nodes():
    text = _render("blocks", "graphml")
    assert 'yfiles.foldertype="group"' in text


def test_dot_is_a_digraph_with_nodes_and_edges():
    for source_name in ("cfg", "blocks"):
        text = _render(source_name, "dot")
        assert text.startswith("digraph")
        assert "->" in text
        assert text.rstrip().endswith("}")


def test_dot_blocks_emit_clusters():
    text = _render("blocks", "dot")
    assert "subgraph \"cluster_" in text


def test_dot_back_edges_are_dashed():
    text = _render("cfg", "dot")
    assert "style=dashed" in text


# -- CLI -------------------------------------------------------------------

def test_visualise_writes_a_default_named_file():
    # With no -o, the graph is written to <source-stem>.<view><ext> in the
    # current directory; use an isolated filesystem to keep cwd clean.
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("prog.bas", "w") as f:
            f.write(_PROGRAM)
        result = runner.invoke(cli, ["visualise", "cfg", "prog.bas"])
        assert result.exit_code == 0, result.output
        assert os.path.exists("prog.cfg.graphml")


def test_visualise_infers_format_from_output_extension(tmp_path):
    source = tmp_path / "prog.bas"
    source.write_text(_PROGRAM)
    out = tmp_path / "graph.dot"
    result = CliRunner().invoke(cli, ["visualise", "blocks", str(source), "-o", str(out)])
    assert result.exit_code == 0, result.output
    assert out.read_text().startswith("digraph")


def test_visualise_to_stdout(tmp_path):
    source = tmp_path / "prog.bas"
    source.write_text(_PROGRAM)
    result = CliRunner().invoke(
        cli, ["visualise", "cfg", str(source), "-f", "dot", "-o", "-"]
    )
    assert result.exit_code == 0, result.output
    assert result.output.startswith("digraph")


def test_visualise_rejects_an_unknown_view(tmp_path):
    source = tmp_path / "prog.bas"
    source.write_text(_PROGRAM)
    result = CliRunner().invoke(cli, ["visualise", "nope", str(source)])
    assert result.exit_code != 0


def test_graph_sources_and_writers_are_listed():
    sources = CliRunner().invoke(cli, ["graph-sources"])
    assert sources.exit_code == 0
    assert {"cfg", "blocks"} <= set(sources.output.split())
    writers = CliRunner().invoke(cli, ["graph-writers"])
    assert writers.exit_code == 0
    assert {"graphml", "dot"} <= set(writers.output.split())


def test_registered_extension_names():
    assert set(list_extensions(_GRAPH_SOURCE_NS)) == {"cfg", "blocks", "callgraph"}
    assert set(list_extensions(_GRAPH_WRITER_NS)) == {"graphml", "dot"}


def test_edge_dataclass_defaults():
    edge = Edge("a", "b")
    assert edge.kind == "flow"
    assert edge.label is None


# -- call graph ------------------------------------------------------------

# A program exercising every call-graph edge kind: a PROC called twice, an FN,
# a GOSUB (-> promoted procedure), an inter-routine GOTO (longjump), a computed
# ON GOTO into another routine, an undefined PROC (-> unknown sink) and a
# machine-code CALL (-> external sink).
_SPAGHETTI = [
    (10, "PROCgreet"), (20, "PROCgreet"), (30, "X%=FNsq(3)"), (40, "GOSUB 1000"),
    (50, "PROCjump"), (60, "PROCdispatch"), (70, "END"),
    (200, "DEF PROCgreet"), (210, 'PRINT "hi"'), (220, "ENDPROC"),
    (300, "DEF FNsq(n)"), (310, "=n*n"),
    # A reachable GOTO out of the routine (longjump), plus an undefined PROC
    # and a machine-code CALL.
    (400, "DEF PROCjump"), (410, "PROCmissing"), (420, "CALL &FFEE"),
    (430, "GOTO 70"), (440, "ENDPROC"),
    # A reachable computed jump into another routine's body.
    (500, "DEF PROCdispatch"), (510, "ON Z% GOTO 210"), (520, "ENDPROC"),
    (1000, 'PRINT "sub"'), (1010, "RETURN"),
]


def _callgraph():
    program = analyse_numbered_lines(
        _SPAGHETTI, name="spaghetti", source_filepath="spaghetti.bas", strict=False
    )
    return _source("callgraph").build(program)


def _edges_of(graph, kind):
    return [(e.source, e.target) for e in graph.edges if e.kind == kind]


def test_callgraph_nodes_are_the_routines_and_sinks():
    graph = _callgraph()
    by_kind = {}
    for node in graph.nodes:
        by_kind.setdefault(node.kind, set()).add(node.id)
    assert by_kind["main"] == {"__owl__main"}
    assert "PROCgreet" in by_kind["proc"]
    assert "FNsq" in by_kind["fn"]
    assert "PROCSub1000" in by_kind["sub"]      # the promoted GOSUB target
    assert by_kind["sink"] == {"__unknown__", "__external__"}


def test_callgraph_call_edges_and_multiplicity():
    graph = _callgraph()
    calls = _edges_of(graph, "call")
    assert ("__owl__main", "PROCgreet") in calls
    assert ("__owl__main", "FNsq") in calls          # FN call detected
    assert ("__owl__main", "PROCSub1000") in calls    # converted GOSUB
    # PROCgreet is called twice; the edge is deduped and labelled with a count.
    greet = [e for e in graph.edges
             if (e.source, e.target) == ("__owl__main", "PROCgreet")]
    assert len(greet) == 1
    assert greet[0].label == "x2"


def test_callgraph_flags_unstructured_transfers():
    graph = _callgraph()
    # GOTO 70 leaves PROCjump for main: a longjump.
    assert ("PROCjump", "__owl__main") in _edges_of(graph, "longjump")
    # ON Z% GOTO 210 jumps into PROCgreet's body: a computed cross-routine jump.
    assert ("PROCdispatch", "PROCgreet") in _edges_of(graph, "computed")
    # CALL &FFEE -> the external sink; PROCmissing is undefined -> unknown sink.
    assert ("PROCjump", "__external__") in _edges_of(graph, "external")
    assert ("PROCjump", "__unknown__") in _edges_of(graph, "call")


def test_callgraph_renders_in_both_formats():
    graph = _callgraph()
    dot = io.StringIO()
    _writer("dot").write(graph, dot)
    assert "color=red" in dot.getvalue()     # longjump styling
    graphml = io.StringIO()
    _writer("graphml").write(graph, graphml)
    text = graphml.getvalue()
    ET.fromstring(text)                       # well-formed
    assert "#FF0000" in text                  # longjump colour


def test_visualise_callgraph_via_cli(tmp_path):
    listing = "\n".join("%d %s" % (n, t) for n, t in _SPAGHETTI) + "\n"
    source = tmp_path / "spaghetti.bas"
    source.write_text(listing)
    out = tmp_path / "cg.dot"
    result = CliRunner().invoke(
        cli, ["visualise", "callgraph", str(source), "-o", str(out), "-e", "latin-1"]
    )
    assert result.exit_code == 0, result.output
    assert out.read_text().startswith("digraph")


def test_callgraph_is_registered():
    assert "callgraph" in list_extensions(_GRAPH_SOURCE_NS)


# -- per-routine scoping ---------------------------------------------------

# A program with a routine to scope to (the bare _PROGRAM has only MAIN).
_WITH_PROC = (
    'PROCgreet\nPROCgreet\nX%=1\nEND\n'
    'DEF PROCgreet\nPRINT "hi"\nPRINT "there"\nENDPROC\n'
)


def _analyse_proc():
    return analyse(_WITH_PROC, name="withproc", source_filepath="withproc.bas")


def _scoped(source_name, routine):
    return _source(source_name).build(_analyse_proc(), {"routine": routine})


def test_cfg_scope_keeps_only_the_routine_and_its_internal_edges():
    full = _source("cfg").build(_analyse_proc())
    scoped = _scoped("cfg", "PROCgreet")
    assert 0 < len(scoped.nodes) < len(full.nodes)
    scoped_ids = {n.id for n in scoped.nodes}
    # Every retained edge stays within the scope (no dangling targets).
    for edge in scoped.edges:
        assert edge.source in scoped_ids and edge.target in scoped_ids


def test_blocks_scope_restricts_to_one_routines_blocks():
    full_blocks = [n for n in _source("blocks").build(_analyse_proc()).nodes
                   if n.kind == "block"]
    scoped_blocks = [n for n in _scoped("blocks", "PROCgreet").nodes
                     if n.kind == "block"]
    assert 0 < len(scoped_blocks) < len(full_blocks)


def test_callgraph_scope_is_the_routine_neighbourhood():
    scoped = _scoped("callgraph", "PROCgreet")
    ids = {n.id for n in scoped.nodes}
    assert "PROCgreet" in ids
    # Every edge touches the scoped routine.
    assert scoped.edges
    for edge in scoped.edges:
        assert "PROCgreet" in (edge.source, edge.target)
    # MAIN calls PROCgreet, so it is pulled in as a neighbour.
    assert "__owl__main" in ids


def test_scope_accepts_main_alias():
    # 'MAIN' resolves to the __owl__main entry point.
    scoped = _scoped("cfg", "MAIN")
    assert scoped.nodes


def test_scope_rejects_unknown_routine():
    from owl_basic.exceptions import OwlBasicError
    with pytest.raises(OwlBasicError) as excinfo:
        _scoped("cfg", "PROCnope")
    assert "PROCgreet" in str(excinfo.value)   # error lists the real routines


def test_routines_command_lists_routines(tmp_path):
    source = tmp_path / "prog.bas"
    source.write_text(_WITH_PROC)
    result = CliRunner().invoke(cli, ["routines", str(source), "-e", "latin-1"])
    assert result.exit_code == 0, result.output
    listed = result.output.split()
    assert "MAIN" in listed
    assert "PROCgreet" in listed


def test_visualise_routine_in_default_filename():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("prog.bas", "w") as f:
            f.write(_PROGRAM)
        result = runner.invoke(cli, ["visualise", "cfg", "prog.bas", "-r", "MAIN"])
        assert result.exit_code == 0, result.output
        assert os.path.exists("prog.cfg.MAIN.graphml")


def test_callgraph_exposes_sphinx_spaghetti():
    # The whole of Sphinx Adventure (the de-protected, compilable .bbc) is real
    # unstructured BASIC: its call graph is not a tree. This locks in that the
    # anomaly edges are detected and that longjump targets resolve to genuine
    # routines (a regression guard for the routine-tag mapping).
    import os
    from helpers import FIXTURES_DIRPATH
    from owl_basic.analysis import analyse_numbered_lines
    from owl_basic.bbc_basic.detokenizer import detokenize_lines

    sphinx = os.path.join(FIXTURES_DIRPATH, "data", "sphinx2-deprotected.bbc")
    data = open(sphinx, "rb").read()
    program = analyse_numbered_lines(detokenize_lines(data), name="sphinx")
    graph = _source("callgraph").build(program)

    routine_ids = {n.id for n in graph.nodes if n.kind != "sink"}
    assert "__owl__main" in routine_ids
    # Sphinx is genuinely unstructured: cross-routine GOTOs and shared code.
    assert _edges_of(graph, "longjump")
    assert _edges_of(graph, "entangled")
    # Every longjump/computed edge connects two real routines (no mis-mapped
    # tags leaking a bogus target).
    for kind in ("longjump", "computed", "call"):
        for source, target in _edges_of(graph, kind):
            assert source in routine_ids
            assert target in routine_ids or target in ("__unknown__", "__external__")
