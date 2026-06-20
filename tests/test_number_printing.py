"""PRINT of integers, two pre-existing OwlRuntime print-format bugs.

* ~ (hex) printed a leading-zero-padded width (PRINT ~255 -> 0000000FF) instead
  of the minimal BBC form (FF); a top-bit-set value prints its 32-bit pattern.
* A 10-digit integer printed in scientific form (PRINT 2000000000 ->
  2.00000000E+09) because Print(int) used the real-number "G9" format; it should
  print in full, as Print(long) already does.
"""
from conftest import requires_dotnet_toolchain
from owl_basic.analysis import analyse


def _out(compile_and_run, src):
    return compile_and_run(analyse(src, name="t")).strip()


@requires_dotnet_toolchain
def test_tilde_hex_minimal_digits(compile_and_run):
    assert _out(compile_and_run, "PRINT ~255\n") == "FF"


@requires_dotnet_toolchain
def test_tilde_hex_top_bit_set_pattern(compile_and_run):
    assert _out(compile_and_run, "PRINT ~&AABBCCDD\n") == "AABBCCDD"


@requires_dotnet_toolchain
def test_tilde_hex_all_ones(compile_and_run):
    assert _out(compile_and_run, "PRINT ~&FFFFFFFF\n") == "FFFFFFFF"


@requires_dotnet_toolchain
def test_large_decimal_integer_prints_in_full(compile_and_run):
    assert _out(compile_and_run, "PRINT 2000000000\n") == "2000000000"


@requires_dotnet_toolchain
def test_int32_max_prints_in_full(compile_and_run):
    assert _out(compile_and_run, "PRINT &7FFFFFFF\n") == "2147483647"


@requires_dotnet_toolchain
def test_small_integer_unchanged(compile_and_run):
    assert _out(compile_and_run, "PRINT 49\n") == "49"
