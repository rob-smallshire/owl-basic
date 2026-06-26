"""A GOSUB target reached by more than just GOSUB.

``convertSubroutinesToProcedures`` turns each GOSUB'd line into a PROC. That is
sound only when GOSUB is the routine's sole *foreign* entry. The classifier
distinguishes two kinds of non-GOSUB in-edge into the head:

* an **internal** back-edge -- a GOTO from inside the routine back to its top,
  i.e. a loop -- which lowers fine as a branch within the PROC and is allowed;
* a **foreign** entry -- a main-line statement falling into the head -- which
  makes RETURN ambiguous and is rejected.

Internal vs foreign is decided by forward-reachability from the head (a GOSUB
target is a CFG root whose body is sealed by RETURNs). Surfaced by
Tau91-b/DEC91.Recur1 (a recursive, GOTO-looped subroutine).
"""
import pytest

from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse_numbered_lines
from owl_basic.exceptions import CompileError


def _analyse(lines):
    return analyse_numbered_lines(lines, name="t", source_filepath="t")


def test_subroutine_with_internal_goto_loop_is_accepted():
    # Line 100 is GOSUB'd and the GOTO 100 at line 110 loops back to its head
    # from inside the routine -- a benign loop, so the conversion is allowed.
    program = _analyse([(10, " GOSUB 100"), (20, " END"),
                        (100, " X=X+1"), (110, " IF X<3 GOTO 100"),
                        (120, " PRINT X"), (130, " RETURN")])
    assert program is not None


def test_subroutine_fallen_into_from_main_is_rejected():
    # Line 30 is GOSUB'd but also fallen into from the main line 20, which is
    # not part of the routine -- a foreign entry, so reject. Determinism: the
    # outcome must not depend on hash-seeded set ordering, so check it holds.
    for _ in range(5):
        with pytest.raises(CompileError, match="not supported"):
            _analyse([(10, " GOSUB 30"), (20, ' PRINT "a"'),
                      (30, ' PRINT "b"'), (40, " RETURN")])


def test_plain_single_entry_subroutine_still_compiles():
    program = _analyse([(10, " GOSUB 40"), (20, " END"),
                        (40, ' PRINT "s"'), (50, " RETURN")])
    assert program is not None


@requires_dotnet_toolchain
def test_internal_goto_loop_compiles_and_runs(compile_and_run):
    # The strongest check: the internal-loop subroutine doesn't just analyse,
    # it lowers and runs correctly. X counts 1,2,3 then the loop exits.
    out = compile_and_run(_analyse([
        (10, " GOSUB 100"), (20, ' PRINT "done"'), (30, " END"),
        (100, " X=X+1"), (110, " IF X<3 GOTO 100"),
        (120, " PRINT X"), (130, " RETURN")]))
    assert out.splitlines() == ["3", "done"]
