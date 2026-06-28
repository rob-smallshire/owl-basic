"""Whole-array operations on multidimensional arrays.

A%() = <expr> assigns every element (BASIC V): a scalar fills, a same-shape array
copies, a mix applies element-wise. This was implemented for 1-D only and rejected
multidimensional targets. Now the element loop nests over every dimension.
Surfaced by Acorn User JigArc (Grid$() = "#" on a 2-D string array).
"""
from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse


def test_2d_fill_compiles(dotnet_backend):
    assert dotnet_backend.emit_il(analyse("DIM A(2,2)\nA()=7\nEND\n", name="t"))


def test_2d_string_fill_compiles(dotnet_backend):
    # The JigArc shape: fill a 2-D string array with a scalar.
    assert dotnet_backend.emit_il(analyse('DIM G$(1,1)\nG$()="#"\nEND\n', name="t"))


def test_3d_fill_compiles(dotnet_backend):
    assert dotnet_backend.emit_il(analyse("DIM A(2,2,2)\nA()=1\nEND\n", name="t"))


@requires_dotnet_toolchain
def test_2d_scalar_fill_runs(compile_and_run):
    out = compile_and_run(analyse(
        "DIM A(2,2)\nA()=7\nPRINT A(0,0);\" \";A(2,2);\" \";A(1,1)\n", name="t"))
    assert out.split() == ["7", "7", "7"]


@requires_dotnet_toolchain
def test_2d_string_fill_runs(compile_and_run):
    out = compile_and_run(analyse(
        'DIM G$(1,1)\nG$()="#"\nPRINT G$(0,0);G$(1,1);G$(0,1)\n', name="t"))
    assert out.strip() == "###"


@requires_dotnet_toolchain
def test_2d_array_copy_runs(compile_and_run):
    out = compile_and_run(analyse(
        "DIM A(2,2)\nDIM B(2,2)\nB(1,1)=9\nB(0,2)=4\nA()=B()\n"
        "PRINT A(1,1);\" \";A(0,2);\" \";A(2,0)\n", name="t"))
    assert out.split() == ["9", "4", "0"]


@requires_dotnet_toolchain
def test_1d_whole_array_still_works(compile_and_run):
    # Regression: the 1-D fill/copy path is unaffected.
    out = compile_and_run(analyse(
        "DIM A(3)\nA()=5\nPRINT A(0);\" \";A(3)\n", name="t"))
    assert out.split() == ["5", "5"]
