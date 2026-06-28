"""Passing a multidimensional array to a PROC/FN.

A whole array A() can be passed to a routine (by reference, BBC semantics). This
worked for 1-D arrays but rejected multidimensional ones ("passing a
multidimensional array as a parameter is not supported"). The rank now flows
through: the actual's rank from its DIM (the registered field), the formal's from
how it is indexed in the body. Surfaced by Acorn User JigArc.
"""
from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse


_PROC = ("DIM A(2,2)\nA(1,1)=5\nPROCf(A())\nEND\n"
         "DEFPROCf(b())\nPRINT b(1,1)\nENDPROC\n")


def test_2d_array_to_proc_compiles(dotnet_backend):
    assert dotnet_backend.emit_il(analyse(_PROC, name="t"))


def test_2d_array_to_fn_compiles(dotnet_backend):
    assert dotnet_backend.emit_il(analyse(
        "DIM A(2,2)\nA(0,1)=9\nPRINT FNsum(A())\nEND\n"
        "DEFFNsum(b())=b(0,1)\n", name="t"))


@requires_dotnet_toolchain
def test_2d_array_to_proc_reads_element(compile_and_run):
    out = compile_and_run(analyse(_PROC, name="t"))
    assert out.strip() == "5"


@requires_dotnet_toolchain
def test_2d_array_param_is_by_reference(compile_and_run):
    # Modifying the array element through the formal changes the caller's array
    # (BBC arrays pass by reference).
    out = compile_and_run(analyse(
        "DIM A(2,2)\nPROCset(A())\nPRINT A(2,2)\nEND\n"
        "DEFPROCset(b())\nb(2,2)=42\nENDPROC\n", name="t"))
    assert out.strip() == "42"


@requires_dotnet_toolchain
def test_1d_array_parameter_still_works(compile_and_run):
    # Regression: 1-D array parameters are unaffected.
    out = compile_and_run(analyse(
        "DIM A(3)\nA(2)=8\nPRINT FNget(A())\nEND\n"
        "DEFFNget(b())=b(2)\n", name="t"))
    assert out.strip() == "8"
