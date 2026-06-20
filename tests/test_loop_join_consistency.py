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


def test_loop_left_open_past_a_join_is_rejected():
    # FOR J is opened only on the THEN branch and is still open where the branches
    # re-join, so the nesting differs by path: reject, not a crash.
    src = ('FOR I%=1 TO 2\n'
           'IF I%=1 THEN FOR J%=1 TO 3\n'
           'PRINT "after"\n'
           'NEXT I%\n')
    with pytest.raises(CompileError):
        analyse(src, name="t")


def test_rejection_is_deterministic_across_repeated_analyses():
    # The verdict must not depend on set iteration order: same answer every time.
    src = ('FOR I%=1 TO 2\n'
           'IF I%=1 THEN FOR J%=1 TO 3\n'
           'PRINT "after"\n'
           'NEXT I%\n')
    for _ in range(8):
        with pytest.raises(CompileError):
            analyse(src, name="t")
