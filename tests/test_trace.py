"""TRACE parses to a no-op.

TRACE ON/OFF/<line> drives the BBC interpreter's interactive line trace, which
has no meaning for a compiled program. OWL parses every form so the ~4 Acorn
User type-ins that sprinkle TRACE through their code get past the parse, and
lowers it to nothing. Pinned so it stays a no-op rather than an error.
"""
import pytest

from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse_numbered_lines
from owl_basic.syntax.ast import Trace


def _analyse(lines):
    return analyse_numbered_lines(lines, name="tr")


def _statements(program):
    seen, out = set(), []
    for blocks in program.ordered_basic_blocks.values():
        for b in blocks:
            for s in b.statements:
                if id(s) not in seen:
                    seen.add(id(s))
                    out.append(s)
    return out


@pytest.mark.parametrize("form", ["TRACE", "TRACE ON", "TRACE OFF", "TRACE 100"])
def test_trace_forms_parse_to_a_trace_node(form):
    program = _analyse([(10, " " + form), (20, " END"), (100, " END")])
    assert any(isinstance(s, Trace) for s in _statements(program))


@requires_dotnet_toolchain
def test_trace_is_a_no_op_at_runtime(compile_and_run):
    # TRACE ON ... TRACE OFF surround ordinary statements and change nothing.
    out = compile_and_run(_analyse([
        (10, " TRACE ON"),
        (20, ' PRINT "a"'),
        (30, " TRACE OFF"),
        (40, ' PRINT "b"'),
        (50, " END"),
    ]))
    assert out.splitlines() == ["a", "b"]
