"""LOCAL / PRIVATE scoping. See docs/local-semantics.md for the full model.

OWL implements whole-function dynamic scoping: a LOCAL save/restores its
variables across the *whole body* of every PROC/FN frame that owns it (the frame
whose ENDPROC/= restores them), and is a no-op where no such frame is active --
the main program, or a statement reachable from main via unstructured flow. OWL
therefore never rejects a program on LOCAL attribution.
"""
import pytest

from owl_basic.analysis import analyse, analyse_numbered_lines
from conftest import requires_dotnet_toolchain


def _compiles(source):
    return not analyse(source, name="t").diagnostics


# -- analysis: attribution never rejects -----------------------------------

def test_top_level_local_compiles_as_a_noop():
    # A LOCAL with no enclosing PROC/FN frame: the variable just stays global.
    assert _compiles("LOCAL X\nX=7\nPRINT X\n")


def test_top_level_private_compiles_as_a_noop():
    assert _compiles("PRIVATE X\nX=7\nPRINT X\n")


def test_local_inside_a_procedure_compiles():
    assert _compiles("PROCp\nEND\nDEFPROCp\nLOCAL X\nX=1\nENDPROC\n")


def test_private_inside_a_procedure_compiles():
    assert _compiles("PROCp\nEND\nDEFPROCp\nPRIVATE X\nX=1\nENDPROC\n")


def test_local_in_proc_reachable_from_main_via_goto_compiles():
    # The fractal shape: a PROC's LOCAL whose code is also reachable from MAIN by
    # an unstructured GOTO out of the PROC. No longer rejected -- a no-op on the
    # MAIN path, a save/restore within the PROC frame.
    program = analyse_numbered_lines(
        [(10, 'G=5'), (20, 'PROCp'), (30, 'PRINT G'), (40, 'END'),
         (50, 'DEFPROCp'), (60, 'LOCAL G'), (70, 'G=99'), (80, 'GOTO 30'),
         (90, 'ENDPROC')],
        name="t")
    assert not program.diagnostics


# -- runtime: the actual scoping behaviour ---------------------------------

@requires_dotnet_toolchain
def test_top_level_local_is_a_noop_at_runtime(compile_and_run):
    assert compile_and_run(analyse("LOCAL X\nX=7\nPRINT X\n", name="t")) == "7\n"


@requires_dotnet_toolchain
def test_local_save_restores_around_a_procedure(compile_and_run):
    out = compile_and_run(analyse(
        "G=1\nPROCp\nPRINT G\nEND\nDEFPROCp\nLOCAL G\nG=99\nPRINT G\nENDPROC\n",
        name="t"))
    assert out == "99\n1\n"  # local 99 inside the PROC, global 1 restored after


@requires_dotnet_toolchain
def test_consecutive_locals_merge(compile_and_run):
    # LOCAL A : LOCAL B behaves as LOCAL A, B -- both are localised.
    out = compile_and_run(analyse(
        "A=1\nB=2\nPROCp\nPRINT A,B\nEND\n"
        "DEFPROCp\nLOCAL A\nLOCAL B\nA=8:B=9\nPRINT A,B\nENDPROC\n", name="t"))
    assert out.split() == ['8', '9', '1', '2']


@requires_dotnet_toolchain
def test_nested_locals_restore_each_level(compile_and_run):
    out = compile_and_run(analyse(
        "G=1\nPROCa\nPRINT G\nEND\n"
        "DEFPROCa\nLOCAL G\nG=2\nPROCb\nPRINT G\nENDPROC\n"
        "DEFPROCb\nLOCAL G\nG=3\nPRINT G\nENDPROC\n", name="t"))
    assert out == "3\n2\n1\n"


@requires_dotnet_toolchain
def test_local_is_whole_function_not_positional(compile_and_run):
    # OWL's documented divergence from BBC: a LOCAL localises for the WHOLE
    # function, so a read *before* the LOCAL statement sees the zeroed local, not
    # the global. BBC's positional LOCAL would print 5; OWL prints 0.
    out = compile_and_run(analyse(
        "X=5\nPROCp\nEND\nDEFPROCp\nPRINT X\nLOCAL X\nENDPROC\n", name="t"))
    assert out == "0\n"


@requires_dotnet_toolchain
def test_goto_out_of_proc_leaks_the_local_like_bbc(compile_and_run):
    # A GOTO out of a PROC bypasses its ENDPROC, so the LOCAL is never restored:
    # the global keeps the local value, exactly as BBC BASIC leaks the frame.
    out = compile_and_run(analyse_numbered_lines(
        [(10, 'G=5'), (20, 'PROCp'), (30, 'PRINT G'), (40, 'END'),
         (50, 'DEFPROCp'), (60, 'LOCAL G'), (70, 'G=99'), (80, 'GOTO 30'),
         (90, 'ENDPROC')],
        name="t"))
    assert out == "99\n"
