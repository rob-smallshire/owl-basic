"""Compile-time constant folding of integer arithmetic (issue #6, first slice).

A constant integer expression is folded in the compiler. Because folding is
done in arbitrary precision and the result is typed by magnitude, a product
that overflows 32 bits becomes a 64-bit literal (PRINT 100000*80500 ->
8050000000) instead of wrapping.

The first group are guard rails: constant subexpressions in array indices, FOR
bounds, DIV/MOD etc. must keep working exactly as before folding. The second
group is the new folding behaviour.
"""
from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse


# --- guard rails: behaviour that must be preserved ------------------------

@requires_dotnet_toolchain
def test_constant_array_index_still_works(compile_and_run):
    out = compile_and_run(analyse(
        "DIM A%(10)\nA%(2+3) = 7\nPRINT A%(5)\nEND\n", name="cf_idx"))
    assert out.splitlines() == ["7"]


@requires_dotnet_toolchain
def test_constant_for_bound_still_works(compile_and_run):
    out = compile_and_run(analyse(
        "FOR I% = 1 TO 1+2\nPRINT I%\nNEXT\nEND\n", name="cf_for"))
    assert out.splitlines() == ["1", "2", "3"]


@requires_dotnet_toolchain
def test_constant_div_and_mod_still_works(compile_and_run):
    out = compile_and_run(analyse(
        "PRINT 100 DIV 7\nPRINT 100 MOD 7\nEND\n", name="cf_divmod"))
    assert out.splitlines() == ["14", "2"]


@requires_dotnet_toolchain
def test_negative_and_nested_constants(compile_and_run):
    out = compile_and_run(analyse(
        "PRINT 10 - 25\nPRINT 2 * 3 + 4\nEND\n", name="cf_nest"))
    assert out.splitlines() == ["-15", "10"]


@requires_dotnet_toolchain
def test_in_range_product_stays_int32(compile_and_run):
    # A product that fits int32 is unchanged.
    out = compile_and_run(analyse("PRINT 1000 * 1000\nEND\n", name="cf_small"))
    assert out.splitlines() == ["1000000"]


# --- new behaviour: overflow folds to a 64-bit literal --------------------

@requires_dotnet_toolchain
def test_product_exceeding_int32_folds_wide(compile_and_run):
    out = compile_and_run(analyse("PRINT 100000 * 80500\nEND\n", name="cf_wide"))
    assert out.splitlines() == ["8050000000"]


@requires_dotnet_toolchain
def test_sum_past_int32_folds_wide(compile_and_run):
    out = compile_and_run(analyse("PRINT 2147483647 + 1\nEND\n", name="cf_sum"))
    assert out.splitlines() == ["2147483648"]


@requires_dotnet_toolchain
def test_large_product_folds_wide(compile_and_run):
    out = compile_and_run(analyse("PRINT 1000000 * 1000000\nEND\n", name="cf_big"))
    assert out.splitlines() == ["1000000000000"]


def test_emit_il_folds_constant_product(dotnet_backend):
    # The multiply is folded away to a single wide literal; no `mul` remains.
    il = dotnet_backend.emit_il(analyse("PRINT 100000 * 80500\nEND\n", name="cf_il"))
    assert "ldc.i8 8050000000" in il
