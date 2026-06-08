"""Wide (64-bit) integers: the `%%` type and the int32/int64 boundary cases.

Tracks issue #4 (the `%%` 64-bit integer type, the `%%` sigil as in some modern
BBC BASICs). The int64 *arithmetic-widening* of ordinary `%` expressions and
narrowing-on-store are issue #6, covered separately once they land.
"""
from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse


@requires_dotnet_toolchain
def test_long_integer_variable_roundtrip(compile_and_run):
    # A %% variable holds a value far beyond the 32-bit range.
    out = compile_and_run(analyse("A%% = 1234567890123\nPRINT A%%\nEND\n", name="ll1"))
    assert out.splitlines() == ["1234567890123"]


@requires_dotnet_toolchain
def test_integer_literal_exceeding_int32_is_wide(compile_and_run):
    # A literal too big for int32 is itself a 64-bit integer.
    out = compile_and_run(analyse("PRINT 5000000000\nEND\n", name="ll2"))
    assert out.splitlines() == ["5000000000"]


@requires_dotnet_toolchain
def test_long_integer_max(compile_and_run):
    # The full positive int64 range round-trips.
    out = compile_and_run(analyse("A%% = 9223372036854775807\nPRINT A%%\nEND\n", name="ll3"))
    assert out.splitlines() == ["9223372036854775807"]


@requires_dotnet_toolchain
def test_long_integer_min(compile_and_run):
    out = compile_and_run(analyse("A%% = -9223372036854775808\nPRINT A%%\nEND\n", name="ll4"))
    assert out.splitlines() == ["-9223372036854775808"]


@requires_dotnet_toolchain
def test_long_integer_arithmetic_stays_wide(compile_and_run):
    # Arithmetic on %% operands stays 64-bit and does not wrap at 32 bits.
    out = compile_and_run(analyse(
        "A%% = 3000000000\nB%% = A%% + A%%\nPRINT B%%\nEND\n", name="ll5"))
    assert out.splitlines() == ["6000000000"]


@requires_dotnet_toolchain
def test_long_integer_widens_from_int(compile_and_run):
    # A 32-bit operand widens into a %% expression without loss.
    out = compile_and_run(analyse(
        "A%% = 4000000000\nB% = 5\nC%% = A%% + B%\nPRINT C%%\nEND\n", name="ll6"))
    assert out.splitlines() == ["4000000005"]


def test_emit_il_uses_int64_for_long_integer(dotnet_backend):
    # The %% variable lowers to a CIL int64 static field, loaded with ldc.i8.
    il = dotnet_backend.emit_il(analyse("A%% = 5000000000\nPRINT A%%\nEND\n", name="ll7"))
    assert "int64 i_A" in il
    assert "ldc.i8 5000000000" in il
