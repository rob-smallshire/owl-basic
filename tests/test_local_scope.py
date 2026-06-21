"""LOCAL / PRIVATE are only valid inside a function or procedure.

A misplaced LOCAL/PRIVATE used to crash the symbol-table visitor: it called
``errors.fatalError`` -- but ``errors`` was never imported (NameError), and
``fatalError`` calls ``sys.exit`` anyway (a hard exit, not a diagnostic). The
PRIVATE arm additionally referenced ``local.lineNum`` in ``visitPrivate`` (the
parameter is ``private``). Both now raise a graceful CompileError.

The check is also no longer over-strict: a LOCAL *inside* a procedure whose code
is shared with the main program (e.g. via an unstructured GOTO) lists MAIN among
its entry points yet is perfectly legal, so only a LOCAL whose *sole* entry point
is MAIN -- a genuine top-level LOCAL -- is rejected.
"""
import pytest

from owl_basic.analysis import analyse
from owl_basic.exceptions import CompileError


def test_top_level_local_is_a_graceful_rejection():
    # Was: NameError / sys.exit. Now a CompileError naming LOCAL.
    with pytest.raises(CompileError) as excinfo:
        analyse("LOCAL X\nPRINT X\n", name="t")
    assert "LOCAL" in str(excinfo.value)


def test_top_level_private_is_a_graceful_rejection():
    # Was a double crash (undefined `errors`, and `local` in visitPrivate).
    with pytest.raises(CompileError) as excinfo:
        analyse("PRIVATE X\nPRINT X\n", name="t")
    assert "PRIVATE" in str(excinfo.value)


def test_local_inside_a_procedure_compiles():
    program = analyse("PROCp\nEND\nDEFPROCp\nLOCAL X\nX=1\nENDPROC\n", name="t")
    assert not program.diagnostics


def test_private_inside_a_procedure_compiles():
    program = analyse("PROCp\nEND\nDEFPROCp\nPRIVATE X\nX=1\nENDPROC\n", name="t")
    assert not program.diagnostics
