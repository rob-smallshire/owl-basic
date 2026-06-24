"""A `=value` after a relational condition is a function return.

Verified against the BBC BASIC ROM: relationals do not chain, so `a>b=c` is the
relational `a>b` followed by a *separate* `=c`; and `IF a>b =c` is therefore
`IF (a>b) THEN =c` -- a conditional function return -- not the equality condition
`IF ((a>b)=c)`. A single relational `IF a=b` stays the equality condition. The
recursive-fractal corpus program 899aee14fe2d uses `IF cond =0` to clip a shape.

Workarounds OWL already accepts -- `IF cond THEN =0` and `IF cond:=0` -- pin the
intended behaviour; this is the bare implicit-THEN form after a relational.
"""
import pytest

from owl_basic.analysis import analyse
from owl_basic.syntax.ast import If, Equal, GreaterThan, ReturnFromFunction
from helpers import walk
from conftest import requires_dotnet_toolchain


def _one_if(source):
    program = analyse(source, name="t")
    assert not program.diagnostics
    ifs = [n for n in walk(program.parse_tree) if isinstance(n, If)]
    assert len(ifs) == 1
    return ifs[0]


def test_conditional_return_after_relational_condition_parses():
    iff = _one_if("DEFFNt(x):IF x>0 =1\n=2\n")
    # The condition is the relational; the clause is a function return.
    assert isinstance(iff.condition, GreaterThan)
    returns = [n for n in walk(iff) if isinstance(n, ReturnFromFunction)]
    assert returns, "the =1 should be a function return in the IF's clause"


def test_single_relational_if_stays_an_equality_condition():
    # IF a=b must remain the equality condition (one relational), not a return.
    iff = _one_if("DEFFNt(x):IF x=1 PRINT 9\n=2\n")
    assert isinstance(iff.condition, Equal)


@requires_dotnet_toolchain
def test_conditional_return_runs_correctly(compile_and_run):
    out = compile_and_run(analyse(
        "PRINT FNt(5)\nPRINT FNt(-5)\nEND\nDEFFNt(x):IF x>0 =1\n=2\n", name="t"))
    assert out.split() == ['1', '2']  # x>0 returns 1; otherwise falls to =2


def test_relationals_do_not_chain():
    # Verified on the BBC ROM: PRINT 1>2>3 prints just `1>2` (0) then errors on
    # the dangling `>3`. A bare relational is not an operand for another, so OWL
    # rejects the chain rather than parsing `((1>2)>3)`.
    from owl_basic.exceptions import CompileError
    with pytest.raises(CompileError):
        analyse("PRINT 1>2>3\n", name="t")


def test_parenthesised_relationals_nest():
    # Parentheses make `(1>2)` a primary, so it *can* be a relational operand:
    # `(1>2)>3` is legal (the BBC ROM prints 0). Same for `(3>2)=0`.
    assert not analyse("PRINT (1>2)>3\n", name="t").diagnostics
    assert not analyse("A=(3>2)=0\n", name="t").diagnostics
