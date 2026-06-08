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

from owl_basic.analysis import analyse


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


# --- bounds: DIM A(N) is valid for subscripts 0..N inclusive ------------------

@requires_dotnet_toolchain
def test_boundary_subscripts_are_valid(compile_and_run):
    out = compile_and_run(analyse(
        "DIM A%(3)\nA%(0) = 10\nA%(3) = 40\nPRINT A%(0) + A%(3)\nEND\n", name="bound"))
    assert out.splitlines() == ["50"]


@requires_dotnet_toolchain
def test_subscript_above_range_errors(compile_expecting_error):
    # A%(4) is out of range for DIM A%(3); it must error, not corrupt memory.
    err = compile_expecting_error(analyse("DIM A%(3)\nA%(4) = 1\nEND\n", name="hi"))
    assert "Index" in err or "range" in err.lower()


@requires_dotnet_toolchain
def test_negative_subscript_errors(compile_expecting_error):
    compile_expecting_error(analyse("DIM A%(3)\nPRINT A%(-1)\nEND\n", name="negidx"))


@requires_dotnet_toolchain
def test_multidimensional_subscript_out_of_range_errors(compile_expecting_error):
    compile_expecting_error(analyse("DIM B%(2,2)\nB%(3,0) = 1\nEND\n", name="md"))


# --- re-DIM is a Bad DIM ------------------------------------------------------

def test_emit_il_has_redim_guard(dotnet_backend):
    il = dotnet_backend.emit_il(analyse("DIM A%(3)\nEND\n", name="guard"))
    assert "brfalse dim_ok" in il
    assert "[OwlRuntime]OwlRuntime.BadDimException::.ctor(int32)" in il


@requires_dotnet_toolchain
def test_redimensioning_an_array_is_a_bad_dim(compile_expecting_error):
    err = compile_expecting_error(analyse("DIM A%(3)\nDIM A%(3)\nEND\n", name="redim"))
    assert "Bad DIM" in err


# --- DIM byte blocks: an address into the shared map, used via indirection ----

def test_emit_il_lowers_dim_byte_block(dotnet_backend):
    il = dotnet_backend.emit_il(analyse("DIM b% 100\nb%?0 = 65\nEND\n", name="blkil"))
    assert "call int32 [OwlRuntime]OwlRuntime.MemoryMap::Allocate(int32)" in il
    assert "stsfld int32 i_b" in il        # base address stored in b%


@requires_dotnet_toolchain
def test_dim_byte_block_round_trips_via_indirection(compile_and_run):
    out = compile_and_run(analyse(
        "DIM b% 100\nb%?0 = 65\nb%?100 = 66\nPRINT b%?0\nPRINT b%?100\nEND\n",
        name="blk"))
    assert out.splitlines() == ["65", "66"]   # b?0 .. b?100 are all in the block


@requires_dotnet_toolchain
def test_two_byte_blocks_do_not_overlap(compile_and_run):
    out = compile_and_run(analyse(
        "DIM p% 10\nDIM q% 10\np%?0 = 1\nq%?0 = 2\nPRINT p%?0\nPRINT q%?0\nEND\n",
        name="two"))
    assert out.splitlines() == ["1", "2"]     # writing q didn't clobber p
