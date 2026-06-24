"""A loop left open at the end of a routine is a benign leaked frame, not an error.

A conditional closing statement -- `IF cond NEXT`, `IF cond UNTIL ...` -- is
compilable as long as it correlates with one opener: the closing statement is the
loop's back-edge, and the path that does not take it simply exits the loop early.
In BBC BASIC that early exit leaks the loop's stack frame until control returns to
the prompt; OWL's compiled code has no such frame. So OWL warns (as it already
does for an ENDPROC/= exiting a loop) rather than rejecting "loop still open".
"""
import pytest

from owl_basic.analysis import analyse
from conftest import requires_dotnet_toolchain


def _compiles(source):
    return not analyse(source, name="t").diagnostics


def test_conditional_next_early_exit_compiles():
    assert _compiles("FOR I=1 TO 9\nPRINT I\nIF I<3 NEXT\n")


def test_for_with_no_next_compiles():
    # A FOR never closed by a NEXT: in BBC BASIC the body runs once and the
    # frame leaks. It must not be rejected.
    assert _compiles("FOR I=1 TO 5\nPRINT I\n")


def test_repeat_with_early_goto_exit_compiles():
    assert _compiles("REPEAT\nPRINT 1\nIF TRUE GOTO 40\nUNTIL FALSE\nPRINT 2\n")


@requires_dotnet_toolchain
def test_conditional_next_early_exit_runs_correctly(compile_and_run):
    # `IF I<3 NEXT` loops back only while I<3, so it prints 1, 2, 3 and exits.
    out = compile_and_run(
        analyse("FOR I=1 TO 9\nPRINT I\nIF I<3 NEXT\n", name="t"), timeout=30
    )
    assert out == "1\n2\n3\n"


# --- the `IF c NEXT` continue idiom: a NEXT inside the body that loops back when
# taken, with a *later* NEXT closing the loop. The continue-NEXT is a back-edge;
# the loop stays open until its real close. Distinct from the sole-NEXT early-exit
# above (where the not-taken path leaks), and from a conditionally *opened* FOR
# (genuinely dynamic -- still rejected, see test_loop_correlation_errors).

def test_continue_next_before_closing_next_compiles():
    # FOR Y with a continue, then more body, then the real NEXT.
    assert _compiles("FORY=0TO2\nIFY=1 NEXT\nPRINTY\nNEXT\n")


def test_continue_next_in_middle_of_triple_nest_compiles():
    # The corpus shape (678936c066cc): FOR R / FOR Y (with an IF c NEXT continue) /
    # FOR X, all closed by NEXT,,. The continue pops nothing; NEXT,, closes X,Y,R.
    assert _compiles("FORR=0TO2\nFORY=0TO2\nIFY=1 NEXT\nFORX=0TO2\nN=1\nNEXT,,\n")


@requires_dotnet_toolchain
def test_continue_next_runs_correctly(compile_and_run):
    # IF Y=1 NEXT skips the PRINT for Y=1, so it prints 0 and 2 (the real NEXT
    # closes the loop). This is the behaviour the BBC interpreter gives.
    out = compile_and_run(
        analyse("FORY=0TO2\nIFY=1 NEXT\nPRINTY\nNEXT\n", name="t"), timeout=30)
    assert out == "0\n2\n"


def test_comma_continue_next_compiles():
    # A conditional *comma* NEXT continues several loops at once (X and Y here),
    # with the real closes downstream. The corpus plotting demos 245e11e8ea3d /
    # 6fb7ac344aff use `IF C=0 NEXT,`. Each NEXT in the chain matches the next
    # loop out (the continued ones are flagged, not popped); they stay open for
    # the real NEXT, at the end.
    assert _compiles("FORY=0TO2\nFORX=0TO2\nIFX=9 NEXT,\nPRINTX\nNEXT,\n")


@requires_dotnet_toolchain
def test_comma_continue_next_runs_correctly(compile_and_run):
    # IF X=1 NEXT, continues both X and Y when X=1 (skipping the PRINT), so for
    # Y=0..1, X=0..1 it prints every (Y,X) except those with X=1: 00, 02? no --
    # X only runs 0 TO 2; X=1 is skipped. So per Y it prints X=0 and X=2.
    out = compile_and_run(analyse(
        "FORY=0TO1\nFORX=0TO2\nIFX=1 NEXT,\nPRINTY*10+X\nNEXT,\n", name="t"),
        timeout=30)
    assert out == "0\n2\n10\n12\n"


# --- nested / multiple / cross-construct continue idioms -------------------
# The conditional-closer continue generalises: a closer (NEXT / ENDWHILE; and,
# via UNTIL-FALSE exit pruning, UNTIL FALSE) whose loop is re-closed downstream
# is a back-edge. This holds inside nested loops and for several continues on one
# loop. (WHILE/REPEAT here are checked at analysis; WHILE codegen is a separate
# unimplemented feature, so those are not run.)

def test_nested_for_continue_compiles():
    assert _compiles("FORL=0TO2\nFORS=0TO7\nIFS>5 NEXT\nNEXT\n")


def test_for_multiple_continues_for_one_loop_compiles():
    assert _compiles("FORS=0TO7\nIFS=4 NEXT\nIFS=2 NEXT\nNEXT\n")


def test_while_conditional_endwhile_continue_compiles():
    # IF c ENDWHILE is the BASIC V continue (jump back to the WHILE test early).
    assert _compiles("X=0\nWHILE X<9\nX=X+1\nIFX=3 ENDWHILE\nPRINTX\nENDWHILE\n")


def test_nested_while_endwhile_continue_compiles():
    assert _compiles("WHILE A<2\nA=A+1\nWHILE B<3\nB=B+1\nIFB=1 ENDWHILE\nENDWHILE\nENDWHILE\n")


def test_for_continue_inside_while_compiles():
    assert _compiles("WHILE A<2\nA=A+1\nFORS=0TO3\nIFS=1 NEXT\nNEXT\nENDWHILE\n")


@requires_dotnet_toolchain
def test_nested_for_continue_runs_correctly(compile_and_run):
    # Inner continue skips S=1; both loops close. Prints L*10+S for S in 0,2,3.
    out = compile_and_run(analyse(
        "FORL=0TO1\nFORS=0TO3\nIFS=1 NEXT\nPRINTL*10+S\nNEXT\nNEXT\n", name="t"),
        timeout=30)
    assert out.split() == ["0", "2", "3", "10", "12", "13"]


@requires_dotnet_toolchain
def test_for_multiple_continues_runs_correctly(compile_and_run):
    # IF S=1 NEXT and IF S=3 NEXT both continue the one loop, so 1 and 3 skip.
    out = compile_and_run(analyse(
        "FORS=0TO5\nIFS=1 NEXT\nIFS=3 NEXT\nPRINTS\nNEXT\n", name="t"), timeout=30)
    assert out.split() == ["0", "2", "4", "5"]


# --- cross-type closer skip: a closer (NEXT/UNTIL/ENDWHILE) closes its matching
# opener, leaking any inner open loop of a *different* kind on the way -- as the
# BBC interpreter unwinds the runtime stack to the matching frame. A conditional
# such closer is the outer loop's continue; the inner loop is abandoned on that
# path and re-entered fresh on the next outer iteration.

def test_until_false_continues_outer_repeat_from_inner_for_compiles():
    # IF c UNTIL FALSE inside a FOR continues the enclosing REPEAT, abandoning the
    # FOR. UNTIL FALSE's dead exit is pruned, so it is a pure back-edge -- no join
    # divergence at the FOR's NEXT (that NEXT is reached only on the non-continue
    # path). This is the user's canonical "UNTIL FALSE as an outer continue".
    assert _compiles("REPEAT\nI=I+1\nFORJ=0TO3\nIFJ=2 UNTIL FALSE\nNEXT\nUNTILI>2\n")


def test_closer_skips_inner_open_loop_of_other_type_compiles():
    # A bare closer matching its opener, leaking an inner still-open loop of a
    # different kind: UNTIL over an open FOR, ENDWHILE over an open FOR, NEXT over
    # an open WHILE. Each unwinds to its matching opener.
    assert _compiles("REPEAT\nFORI=0TO3\nUNTILX>1\n")
    assert _compiles("WHILE A<2\nA=A+1\nFORI=0TO3\nENDWHILE\n")
    assert _compiles("FORK=0TO2\nWHILE A<2\nA=A+1\nNEXT\n")


@requires_dotnet_toolchain
def test_until_false_continues_outer_repeat_runs_correctly(compile_and_run):
    # When I=2 and J=1 the UNTIL FALSE continues the REPEAT, abandoning FOR J; the
    # next REPEAT iteration restarts FOR J from 0. So I=1 prints 10..13, I=2 prints
    # only 20 (abandoned at J=1), I=3 prints 30..33, then UNTIL I>2 exits.
    out = compile_and_run(analyse(
        "I=0\nREPEAT\nI=I+1\nFORJ=0TO3\nIFI=2 ANDJ=1 UNTIL FALSE\nPRINTI*10+J\nNEXT\nUNTILI>2\n",
        name="t"), timeout=30)
    assert out.split() == ["10", "11", "12", "13", "20", "30", "31", "32", "33"]
