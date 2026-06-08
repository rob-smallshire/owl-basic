"""Array support in the dotnet backend: DIM, element read/write.

BBC ``DIM A(N)`` makes a 0..N array (N+1 elements). One-dimensional arrays are
CIL vectors (``newarr`` + ``ldelem``/``stelem``); multidimensional arrays have no
opcodes, so they use the runtime-synthesised ``.ctor``/``Get``/``Set`` methods on
the rectangular array type ``T[,]`` (see the legacy cil_visitor and
https://stackoverflow.com/questions/2555769). A scalar ``A%`` and an array
``A%()`` are distinct BBC variables, so they get distinct backing fields.
"""

from conftest import requires_dotnet_toolchain
from helpers import analyse_fixture


def test_emit_il_lowers_one_dimensional_array(dotnet_backend):
    il = dotnet_backend.emit_il(analyse_fixture("arrays.bbctxt"))
    # A%() is a global int vector, distinct from any scalar A%.
    assert ".field static int32[] arr_i_A" in il
    assert "newarr int32" in il
    # DIM A%(3) allocates 3+1 elements: size expr then +1.
    assert "ldc.i4.1\n        add" in il
    assert "stelem.i4" in il          # A%(1) = ...
    assert "ldelem.i4" in il          # ... = A%(1)


def test_emit_il_lowers_multidimensional_array(dotnet_backend):
    il = dotnet_backend.emit_il(analyse_fixture("arrays.bbctxt"))
    assert ".field static int32[,] arr_i_B" in il
    assert "newobj instance void int32[,]::.ctor(int32, int32)" in il
    assert "call instance void int32[,]::Set(int32, int32, int32)" in il
    assert "call instance int32 int32[,]::Get(int32, int32)" in il


def test_emit_il_lowers_float_array(dotnet_backend):
    il = dotnet_backend.emit_il(analyse_fixture("arrays.bbctxt"))
    assert ".field static float64[] arr_f_F" in il
    assert "stelem.r8" in il
    assert "ldelem.r8" in il


@requires_dotnet_toolchain
def test_arrays_compile_and_run(compile_and_run):
    out = compile_and_run(analyse_fixture("arrays.bbctxt"))
    assert out.splitlines() == ["84", "7", "2.5"]
