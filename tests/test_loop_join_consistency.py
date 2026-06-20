"""Loop correlation must give the same verdict regardless of CFG traversal order.

The correlator walks the forward control-flow graph tracking a stack of open loops.
Where two paths re-join, the loop nesting they arrive with must agree; if it does
not -- a loop opened on only one branch and still open at the join -- the program
relies on BBC BASIC's dynamic loop stack and cannot be compiled. Because outEdges
is an (unordered) set, the old code's verdict depended on which path was walked
first, so the same program could compile on one run and be rejected on the next.

These cases pin both directions: a loop opened *and closed* within one branch is
balanced at the join and must still compile, while one left open past the join
must be rejected deterministically.
"""
import pytest

from owl_basic.analysis import analyse
from owl_basic.exceptions import CompileError


def test_loop_opened_and_closed_within_a_branch_still_compiles():
    # FOR J runs entirely inside the THEN branch; both paths reach "after" and the
    # final NEXT I with the same nesting ([I]). Must NOT be mis-rejected.
    src = ('FOR I%=1 TO 2\n'
           'IF I%=1 THEN FOR J%=1 TO 3:NEXT J%\n'
           'PRINT "after"\n'
           'NEXT I%\n')
    analyse(src, name="t")  # no exception


def test_conditionally_opened_loop_closed_by_named_next_leaks_and_compiles():
    # FOR J% is opened only on the THEN branch and never gets its own NEXT, but
    # the outer NEXT I% names I%, so it unambiguously closes up to I%, discarding
    # the leaked J% frame -- exactly what BBC BASIC does. This is the same
    # early-exit-leak shape as a GOTO out of a FOR (cf. ragged-num), so it must
    # compile, not be mis-rejected as dynamic-stack reliance.
    src = ('FOR I%=1 TO 2\n'
           'IF I%=1 THEN FOR J%=1 TO 3\n'
           'PRINT "after"\n'
           'NEXT I%\n')
    analyse(src, name="t")  # no exception


def test_bare_next_closing_a_conditional_loop_is_rejected():
    # With a bare NEXT (no index) the loop to close is "the innermost", which
    # differs by path (J% on the THEN branch, I% otherwise) -- genuinely
    # ambiguous, so reject. Distinguishes the unnamed case from the named one.
    src = ('FOR I=1 TO 2:IF I FOR J=1 TO 3:PRINT J\n'
           'NEXT,\n')
    with pytest.raises(CompileError):
        analyse(src, name="t")


def test_leak_verdict_is_deterministic_across_repeated_analyses():
    # The verdict (compile, with a leaked frame) must not depend on CFG traversal
    # order: the same source analyses cleanly every time.
    src = ('FOR I%=1 TO 2\n'
           'IF I%=1 THEN FOR J%=1 TO 3\n'
           'PRINT "after"\n'
           'NEXT I%\n')
    for _ in range(8):
        analyse(src, name="t")
