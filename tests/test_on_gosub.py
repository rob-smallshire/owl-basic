"""ON x GOSUB a, b, c -- call the x-th subroutine (1-based), then continue.

The computed analogue of ON x GOTO, but each target is GOSUB'd (so execution
resumes after the ON GOSUB when the subroutine RETURNs). Each target line becomes
PROCSub<line> via the usual GOSUB->PROC machinery; the switch routes to the
matching call. Surfaced by ~6 Acorn User type-ins (e.g. ON dir%+1 GOSUB ...).
"""
import pytest

from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse_numbered_lines
from owl_basic.syntax.ast import OnGosub


def _analyse(lines):
    return analyse_numbered_lines(lines, name="ogs")


def test_on_gosub_parses_to_an_ongosub_node():
    program = _analyse([(10, " ON X GOSUB 100,200"), (20, " END"),
                        (100, " RETURN"), (200, " RETURN")])
    nodes = [s for blocks in program.ordered_basic_blocks.values()
             for b in blocks for s in b.statements if isinstance(s, OnGosub)]
    assert len(nodes) >= 1


@requires_dotnet_toolchain
def test_on_gosub_calls_the_selected_subroutine(compile_and_run):
    # X=2 -> the second target (line 200) is GOSUB'd; it RETURNs to "back".
    out = compile_and_run(_analyse([
        (10, " X=2"),
        (20, " ON X GOSUB 100,200"),
        (30, ' PRINT "back":END'),
        (100, ' PRINT "one":RETURN'),
        (200, ' PRINT "two":RETURN'),
    ]))
    assert out.splitlines() == ["two", "back"]


@requires_dotnet_toolchain
def test_on_gosub_first_target(compile_and_run):
    out = compile_and_run(_analyse([
        (10, " X=1"),
        (20, " ON X GOSUB 100,200"),
        (30, ' PRINT "back":END'),
        (100, ' PRINT "one":RETURN'),
        (200, ' PRINT "two":RETURN'),
    ]))
    assert out.splitlines() == ["one", "back"]


@requires_dotnet_toolchain
def test_on_gosub_repeated_target(compile_and_run):
    # A repeated target (ON section% GOSUB 980,980,990,980 idiom) calls the same
    # subroutine for several selector values.
    out = compile_and_run(_analyse([
        (10, " X=3"),
        (20, " ON X GOSUB 100,100,200,100"),
        (30, ' PRINT "back":END'),
        (100, ' PRINT "a":RETURN'),
        (200, ' PRINT "b":RETURN'),
    ]))
    assert out.splitlines() == ["b", "back"]
