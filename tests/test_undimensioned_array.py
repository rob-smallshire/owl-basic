"""Using an array that was never DIMmed is diagnosed.

An array element access (A(i)) to an array with no DIM (and which is not a formal
array parameter) is a program error -- on a real BBC it raises at run time. The
front end used to accept it silently and the backend then emitted an
inconsistent array reference that ilasm rejected. Now it is a clean diagnostic,
so an undimensioned array is rejected rather than producing invalid IL. Surfaced
by Acorn User Tau90-a/MAY90.STRUM (uses i%(c%,k%) with no DIM i%).
"""
import pytest

from owl_basic.analysis import analyse
from owl_basic.exceptions import OwlBasicError


def _array_diagnostics(source):
    program = analyse(source, name="t")
    return [d for d in (getattr(program, "diagnostics", None) or [])
            if "dim" in d.lower()]


def test_undimensioned_array_read_is_diagnosed():
    diags = _array_diagnostics("x=A(3)\nEND\n")
    assert any("A" in d for d in diags)


def test_undimensioned_array_write_is_diagnosed():
    diags = _array_diagnostics("A(3)=5\nEND\n")
    assert any("A" in d for d in diags)


def test_two_dimensional_undimensioned_array_is_diagnosed():
    # The STRUM shape: i%(c%,k%) with no DIM i%.
    diags = _array_diagnostics("c%=1\nk%=2\nx=i%(c%,k%)\nEND\n")
    assert diags


def test_dimensioned_array_is_fine():
    assert _array_diagnostics("DIM A(10)\nA(3)=5\nPRINT A(3)\nEND\n") == []


def test_array_dimensioned_after_use_is_fine():
    # DIM may appear textually after the use; all DIMs are collected first.
    assert _array_diagnostics("PROCa\nDIM A(10)\nEND\nDEFPROCa\nA(0)=1\nENDPROC\n") == []


def test_formal_array_parameter_is_not_flagged():
    # b() is a formal array parameter, DIMmed by the caller -- not undimensioned.
    assert _array_diagnostics(
        "DIM A(10)\nPROCf(A())\nEND\nDEFPROCf(b())\nx=b(0)\nENDPROC\n") == []


def test_undimensioned_array_refuses_codegen(dotnet_backend):
    with pytest.raises(OwlBasicError):
        dotnet_backend.emit_il(analyse("A(3)=5\nEND\n", name="t"))


# --- a byte block does not provide an array of the same name ------------------
# In BBC BASIC II, `DIM b% 100` allocates a byte block and stores its base
# address in the integer scalar b%. Indexing that name as an array -- `b%(5)` --
# refers to a *separate* variable b%() that was never DIMmed, so a real BBC gives
# an `Array` error at run time. (Byte indirection `b%?5` is the correct way to
# reach the block.) Surfaced by A&B ADVRUN line 2640, where a dropped `?` turned
# `Cy%?(M%?9)` into `Cy%(M%?9)` -- the same broken shape. OWL must keep rejecting
# it rather than treating the block as an array.

def test_byte_block_used_as_an_array_is_diagnosed():
    diags = _array_diagnostics("DIM b% 100\nPRINT b%(5)\nEND\n")
    # Distinguished from a never-DIMmed typed array: the message names it a byte
    # block and the BBC "Array" error, not "never DIMmed".
    assert any("byte block" in d and "Array" in d for d in diags)
    assert not any("never DIMmed" in d for d in diags)


def test_byte_block_indirection_is_fine():
    # The block is reached by ?/! indirection, not array indexing.
    assert _array_diagnostics("DIM b% 100\nb%?5=65\nPRINT b%?5\nEND\n") == []


def test_genuinely_undimensioned_array_keeps_its_message():
    # A name with no DIM at all (no byte block) still says "never DIMmed".
    diags = _array_diagnostics("PRINT A(5)\nEND\n")
    assert any("never DIMmed" in d for d in diags)
