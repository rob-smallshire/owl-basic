"""HIMEM, LOMEM, PAGE, TOP -- the BBC memory-map pseudo-variables.

On a real BBC Micro these introspect the memory occupied by the BASIC program
itself. OWL targets .NET, where there is no such map, so the values are
ultimately meaningless -- but programs read and compare them (e.g. `HIMEM=HIMEM
-&100` to reserve space). OWL delegates to the runtime, which returns fixed,
plausible values in the correct relative order (PAGE <= TOP <= LOMEM <= HIMEM).
HIMEM/LOMEM/PAGE are assignable; TOP is read-only. PTR is a file operation and is
not covered here.
"""
from owl_basic.analysis import analyse
from owl_basic.ext.backends.dotnet.emitter import emit_program
from conftest import requires_dotnet_toolchain


def _lowers(source):
    return emit_program(analyse(source, name="t"), "t")


def test_reads_lower():
    for name in ("HIMEM", "LOMEM", "PAGE", "TOP"):
        _lowers("X=%s\nEND\n" % name)


def test_assignments_lower():
    for name in ("HIMEM", "LOMEM", "PAGE"):
        _lowers("%s=&7000\nEND\n" % name)


@requires_dotnet_toolchain
def test_values_are_in_the_correct_order(compile_and_run):
    out = compile_and_run(analyse(
        "PRINT (PAGE<=TOP) AND (TOP<=LOMEM) AND (LOMEM<=HIMEM)\n", name="t"))
    assert out.strip() == "-1"  # every comparison true (BBC TRUE = -1)


@requires_dotnet_toolchain
def test_himem_is_assignable(compile_and_run):
    out = compile_and_run(analyse("HIMEM=&7000\nPRINT HIMEM\n", name="t"))
    assert out.strip() == "28672"


@requires_dotnet_toolchain
def test_page_and_lomem_are_assignable(compile_and_run):
    out = compile_and_run(analyse(
        "PAGE=&E00\nLOMEM=&1000\nPRINT PAGE,LOMEM\n", name="t"))
    assert out.split() == ['3584', '4096']
