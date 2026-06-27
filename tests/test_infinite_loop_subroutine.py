"""Infinite-loop idioms placed before a GOSUB'd subroutine.

``convertSubroutinesToProcedures`` turns each GOSUB'd line into a PROC, which is
sound only when GOSUB is the head's sole *foreign* entry. A subroutine placed
just after a ``REPEAT ... UNTIL FALSE`` or ``WHILE TRUE ... ENDWHILE`` loop looks
reachable by fall-through -- the loop's closer draws a CFG edge to the following
statement -- but that loop never exits, so the edge is dead. Pruning it (before
subroutine conversion) lets the head convert as the GOSUB-only routine it is.

Soundness: a loop whose exit condition is *not* a compile-time constant can
exit, so a genuine fall-through into a following subroutine is still rejected;
and the ``IF c ENDWHILE`` continue idiom (where the ENDWHILE is not the loop
exit) must keep working.
"""
import pytest

from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse_numbered_lines
from owl_basic.exceptions import CompileError


def _analyse(lines):
    return analyse_numbered_lines(lines, name="t", source_filepath="t")


# -- the fix: an infinite loop before a GOSUB'd subroutine ------------------

def test_until_false_loop_before_subroutine_compiles():
    program = _analyse([(10, " REPEAT"), (20, " GOSUB 100"), (30, " UNTIL FALSE"),
                        (100, ' PRINT "x"'), (110, " RETURN")])
    assert program is not None


def test_while_true_loop_before_subroutine_compiles():
    program = _analyse([(10, " WHILE TRUE"), (20, " GOSUB 100"), (30, " ENDWHILE"),
                        (100, ' PRINT "x"'), (110, " RETURN")])
    assert program is not None


def test_until_zero_loop_before_subroutine_compiles():
    # UNTIL 0 is the same idiom as UNTIL FALSE (FALSE is 0).
    program = _analyse([(10, " REPEAT"), (20, " GOSUB 100"), (30, " UNTIL 0"),
                        (100, ' PRINT "x"'), (110, " RETURN")])
    assert program is not None


# -- soundness: a loop that can really exit still rejects fall-through ------

def test_conditional_until_into_subroutine_still_rejected():
    # UNTIL A% can exit, so line 100 really is reached by fall-through as well as
    # by GOSUB -- that is the unsupported, ambiguous-RETURN case.
    with pytest.raises(CompileError, match="not supported"):
        _analyse([(10, " REPEAT"), (20, " GOSUB 100"), (30, " UNTIL A%"),
                  (100, ' PRINT "x"'), (110, " RETURN")])


def test_conditional_while_into_subroutine_still_rejected():
    with pytest.raises(CompileError, match="not supported"):
        _analyse([(10, " WHILE A%"), (20, " GOSUB 100"), (30, " ENDWHILE"),
                  (100, ' PRINT "x"'), (110, " RETURN")])


# -- runnable end to end (the loop exits via GOTO, the sub is GOSUB-only) ---

@requires_dotnet_toolchain
def test_until_false_loop_with_gosub_runs(compile_and_run):
    out = compile_and_run(_analyse([
        (10, " I%=0"), (20, " REPEAT"), (30, " GOSUB 100"), (40, " I%=I%+1"),
        (50, " IF I%>=3 THEN 70"), (60, " UNTIL FALSE"),
        (70, ' PRINT "done"'), (80, " END"),
        (100, " PRINT I%"), (110, " RETURN")]))
    assert out.split() == ["0", "1", "2", "done"]


@requires_dotnet_toolchain
def test_while_true_loop_with_gosub_runs(compile_and_run):
    out = compile_and_run(_analyse([
        (10, " I%=0"), (20, " WHILE TRUE"), (30, " GOSUB 100"), (40, " I%=I%+1"),
        (50, " IF I%>=3 THEN 70"), (60, " ENDWHILE"),
        (70, ' PRINT "done"'), (80, " END"),
        (100, " PRINT I%"), (110, " RETURN")]))
    assert out.split() == ["0", "1", "2", "done"]
