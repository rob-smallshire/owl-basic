"""Numeric/clock/format features surfaced by real BBC BASIC benchmark programs
(the bench.ssd disc): DIV/MOD, the transcendental math family, STR$, TIME, and
PRINT TAB. Plus a check that two of those real benchmarks compile end to end.
"""
import os

from conftest import requires_dotnet_toolchain
from helpers import FIXTURES_DIRPATH

from owl_basic.analysis import analyse, analyse_numbered_lines
from owl_basic.bbc_basic.detokenizer import detokenize_lines


@requires_dotnet_toolchain
def test_integer_div_and_mod(compile_and_run):
    out = compile_and_run(analyse("PRINT 17 DIV 5\nPRINT 17 MOD 5\nEND\n", name="divmod"))
    assert out.splitlines() == ["3", "2"]


@requires_dotnet_toolchain
def test_transcendental_functions(compile_and_run):
    # e; ln(e)=1; 4*atn(1)=pi; cos(0)=1; sin(0)=0  (scaled and floored).
    out = compile_and_run(analyse(
        "PRINT INT(EXP(1) * 1000)\nPRINT INT(LN(EXP(1)) * 1000)\n"
        "PRINT INT(ATN(1) * 4 * 1000)\nPRINT INT(COS(0))\nPRINT INT(SIN(0))\nEND\n",
        name="trig"))
    assert out.splitlines() == ["2718", "1000", "3141", "1", "0"]


@requires_dotnet_toolchain
def test_str_string(compile_and_run):
    out = compile_and_run(analyse('PRINT STR$(42)\nA$ = STR$(3.5)\nPRINT A$\nEND\n', name="strs"))
    assert out.splitlines() == ["42", "3.5"]


@requires_dotnet_toolchain
def test_time_reads_and_writes(compile_and_run):
    # TIME is the centisecond clock; set it, then read it back.
    out = compile_and_run(analyse("TIME = 5000\nPRINT (TIME >= 5000)\nEND\n", name="time"))
    assert out.splitlines() == ["-1"]


def test_print_tab_emits_a_cursor_move(dotnet_backend):
    il = dotnet_backend.emit_il(analyse('PRINT TAB(5);"X"\nEND\n', name="tab"))
    assert "TabH(int32)" in il


@requires_dotnet_toolchain
def test_real_benchmarks_compile(dotnet_backend):
    """Two real benchmark programs from bench.ssd (tokenised) detokenise,
    analyse and emit assembled-quality CIL."""
    for name in ("CLKSP3", "WHETBAS"):
        path = os.path.join(FIXTURES_DIRPATH, "data", "benchmarks", name + ".bbc")
        program = analyse_numbered_lines(
            detokenize_lines(open(path, "rb").read()), name=name.lower())
        il = dotnet_backend.emit_il(program)
        assert ".entrypoint" in il, name


@requires_dotnet_toolchain
def test_print_spc(compile_and_run):
    # SPC(n) prints n spaces.
    out = compile_and_run(analyse('PRINT "a";SPC(3);"b"\nEND\n', name="spc"))
    assert out == "a   b\n"
