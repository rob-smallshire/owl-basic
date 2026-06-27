"""Indexing a DIMmed array with the wrong number of subscripts is diagnosed.

An array DIMmed with N dimensions must be indexed with N subscripts. Indexing
it with a different count is a program error -- on a real BBC it raises a
"Subscript" error at run time, and the backend would otherwise emit an array
reference of the wrong rank (e.g. int32[] against an int32[,] field), which
ilasm rejects. Now it is a clean diagnostic. Surfaced by Acorn User
Tau90-a/MAY90.STRUM, which DIMs p%(9,7) but accesses p%(c%) on one branch.

The rank of a formal array parameter is unknown (it is DIMmed by the caller),
so such arrays are never rank-checked -- no false positive.
"""
import pytest

from owl_basic.analysis import analyse
from owl_basic.exceptions import OwlBasicError


def _rank_diagnostics(source):
    program = analyse(source, name="t")
    return [d for d in (getattr(program, "diagnostics", None) or [])
            if "subscript" in d.lower()]


def test_two_d_array_indexed_with_one_subscript_is_diagnosed():
    diags = _rank_diagnostics("DIM p%(9,7)\nc%=1\np%(c%)=3\nEND\n")
    assert any("p%" in d for d in diags)


def test_one_d_array_indexed_with_two_subscripts_is_diagnosed():
    diags = _rank_diagnostics("DIM A(10)\nx=A(1,2)\nEND\n")
    assert any("A" in d for d in diags)


def test_correct_rank_is_fine():
    assert _rank_diagnostics("DIM p%(9,7)\nx=p%(1,2)\nEND\n") == []


def test_correct_one_d_rank_is_fine():
    assert _rank_diagnostics("DIM A(10)\nA(3)=5\nPRINT A(3)\nEND\n") == []


def test_formal_array_parameter_is_not_rank_checked():
    # b() is a formal parameter -- its rank is the caller's, unknown here.
    assert _rank_diagnostics(
        "DIM A(9,7)\nPROCf(A())\nEND\n"
        "DEFPROCf(b())\nx=b(0)\nENDPROC\n") == []


def test_rank_mismatch_refuses_codegen(dotnet_backend):
    with pytest.raises(OwlBasicError):
        dotnet_backend.emit_il(analyse("DIM p%(9,7)\nc%=1\np%(c%)=3\nEND\n", name="t"))
