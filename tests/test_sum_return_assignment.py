"""Assigning a polymorphic (sum-typed) FN result to a concrete l-value.

A DEF FN that returns different types on different paths is inferred as a sum
(e.g. Integer | String) and returns a boxed object. Assigning that result to a
concrete variable used to be rejected ("Cannot assign Integer | String to
String") by the all-members convertibility rule. It is now allowed with a
runtime-checked unbox (As*): the value carries its runtime type, and a genuine
mismatch is a BBC "Type mismatch". Surfaced by The Micro User BLACKJA/To->VIW
(FNinput returning a string or a number by argument).

Cost is pay-for-use: only a sum-returning FN boxes and only a concrete
assignment of its result unboxes; an ordinary FN call has neither.
"""
from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse


_POLY = ("END\n"
         "DEFFNpoly(t$)\n"
         'IF t$="S" THEN ="hi" ELSE =42\n')


def test_sum_to_string_compiles(dotnet_backend):
    assert dotnet_backend.emit_il(analyse('A$=FNpoly("S")\n' + _POLY, name="t"))


def test_sum_to_integer_compiles(dotnet_backend):
    assert dotnet_backend.emit_il(analyse('N%=FNpoly("N")\n' + _POLY, name="t"))


def test_concrete_return_fn_still_does_not_box(dotnet_backend):
    # Pay-for-use: an ordinary concrete-return FN neither boxes nor unboxes.
    il = dotnet_backend.emit_il(analyse(
        "x=FNarea(3)\nPRINT x\nEND\nDEFFNarea(r)=r*r\n", name="t"))
    assert "box " not in il
    assert "::AsFloat" not in il and "::AsInt" not in il


@requires_dotnet_toolchain
def test_sum_to_string_runs(compile_and_run):
    out = compile_and_run(analyse('A$=FNpoly("S")\nPRINT A$\n' + _POLY, name="t"))
    assert out.strip() == "hi"


@requires_dotnet_toolchain
def test_sum_to_integer_runs(compile_and_run):
    out = compile_and_run(analyse('N%=FNpoly("N")\nPRINT N%\n' + _POLY, name="t"))
    assert out.strip() == "42"
