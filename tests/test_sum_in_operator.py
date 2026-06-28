"""A polymorphic (sum) FN result used as an operator or argument operand.

Completes the sum-type story: assignment and comparison already narrow a sum
result to a concrete type with a runtime-checked unbox; so does using it as an
operand to an operator (NOT, +, ...) or a PROC/FN argument. The operand-
compatibility check rejected a sum when not every member fit; now it is allowed
when *some* member fits, inserting the unbox. Surfaced by Acorn User Gus
(UNTIL NOT FNask(...) where FNask returns Integer|String).
"""
from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse


# FNp returns a number on the "N" path and a string otherwise: an Integer|String.
_POLY = ("END\n"
         "DEFFNp(t$)\n"
         'IF t$="S" THEN ="hi" ELSE =42\n')


def test_sum_under_not_compiles(dotnet_backend):
    assert dotnet_backend.emit_il(analyse(
        'REPEAT:UNTIL NOT FNp("N")\n' + _POLY, name="t"))


def test_sum_in_arithmetic_compiles(dotnet_backend):
    assert dotnet_backend.emit_il(analyse('x=FNp("N")+1\n' + _POLY, name="t"))


def test_concrete_fn_in_operator_still_does_not_box(dotnet_backend):
    # Pay-for-use: a concrete-return FN under an operator neither boxes nor unboxes.
    il = dotnet_backend.emit_il(analyse(
        "x=FNn(1)+1\nEND\nDEFFNn(r)=r*r\n", name="t"))
    assert "box " not in il and "::AsInt" not in il and "::AsFloat" not in il


@requires_dotnet_toolchain
def test_sum_in_arithmetic_runs(compile_and_run):
    out = compile_and_run(analyse('PRINT FNp("N")+1\n' + _POLY, name="t"))
    assert out.strip() == "43"


@requires_dotnet_toolchain
def test_sum_under_not_runs(compile_and_run):
    # NOT 42 = -43 (bitwise complement); proves the sum unboxed to an integer.
    out = compile_and_run(analyse('PRINT NOT FNp("N")\n' + _POLY, name="t"))
    assert out.strip() == "-43"
