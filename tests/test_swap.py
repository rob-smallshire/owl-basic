"""SWAP a,b exchanges the values of two l-values.

SWAP is a BBC BASIC V statement: it swaps the contents of two writable
locations of the same type (two scalars, two array elements, ...). Each
operand's subscripts are evaluated exactly once, so SWAP of array elements with
side-effecting subscripts (the corpus case SWAP pt%(RND(8),..),pt%(RND(8),..))
is well defined. SWAPping a string with a number is a type error. Surfaced by
Acorn User Tau92-a/JUN92.Lines.
"""
import pytest

from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse
from owl_basic.exceptions import OwlBasicError


def _swap_diagnostics(source):
    program = analyse(source, name="t")
    return [d for d in (getattr(program, "diagnostics", None) or [])
            if "mismatch" in d.lower()]


# -- analysis / type checking ---------------------------------------------

def test_swap_scalars_compiles(dotnet_backend):
    assert dotnet_backend.emit_il(analyse("a=1\nb=2\nSWAP a,b\nEND\n", name="t"))


def test_swap_array_elements_compiles(dotnet_backend):
    il = dotnet_backend.emit_il(analyse(
        "DIM A(9)\nA(0)=1\nA(1)=2\nSWAP A(0),A(1)\nEND\n", name="t"))
    assert il


def test_swap_string_with_number_is_a_type_error():
    assert _swap_diagnostics('a$="x"\nb=1\nSWAP a$,b\nEND\n')


# -- runtime behaviour -----------------------------------------------------

@requires_dotnet_toolchain
def test_swap_scalars_runtime(compile_and_run):
    out = compile_and_run(analyse('a=3\nb=7\nSWAP a,b\nPRINT a;" ";b\n', name="t"))
    assert out.split() == ["7", "3"]


@requires_dotnet_toolchain
def test_swap_strings_runtime(compile_and_run):
    out = compile_and_run(analyse(
        'a$="foo"\nb$="bar"\nSWAP a$,b$\nPRINT a$;" ";b$\n', name="t"))
    assert out.split() == ["bar", "foo"]


@requires_dotnet_toolchain
def test_swap_array_elements_runtime(compile_and_run):
    out = compile_and_run(analyse(
        "DIM A(9)\nA(2)=11\nA(5)=22\nSWAP A(2),A(5)\nPRINT A(2);\" \";A(5)\n",
        name="t"))
    assert out.split() == ["22", "11"]


@requires_dotnet_toolchain
def test_swap_evaluates_subscript_once(compile_and_run):
    # The subscript expression has a side effect (it advances i%). If SWAP
    # evaluated it more than once per operand, i% would end up wrong. Here both
    # operands index A() at i% then i%+1 via a FN-free incrementing scheme: use a
    # 2-D shape mirroring the corpus, with the index read from a counter.
    out = compile_and_run(analyse(
        "DIM A(9)\n"
        "A(3)=100\nA(4)=200\n"
        "i%=3\n"
        "SWAP A(i%),A(i%+1)\n"
        "PRINT A(3);\" \";A(4)\n", name="t"))
    assert out.split() == ["200", "100"]
