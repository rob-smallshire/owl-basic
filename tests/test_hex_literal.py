"""BBC BASIC & hex constants are signed bit patterns, not magnitudes.

Confirmed from the BASIC II ROM (factor_hex, &AE6D): hex digits are folded into a
32-bit cell with no overflow check, so an 8-digit value with the top bit set is
negative -- &AABBCCDD = -1430532899 -- and is accepted, then stored by raw
truncation. OWL had valued it as the positive 2864434397 and rejected narrowing
it to a 32-bit Integer.

These assert the *value* via comparisons (which yield small -1/0 results),
avoiding two unrelated pre-existing print-format bugs this surfaced: ~ pads hex
with a leading zero, and PRINT shows a large integer in float form.
"""
import pytest

from conftest import requires_dotnet_toolchain
from owl_basic.analysis import analyse


def test_top_bit_set_hex_assigns_without_range_error():
    # Was: CompileError "constant 2864434397 is out of range for Integer".
    analyse("A%=&AABBCCDD\n", name="t")


def _out(compile_and_run, src):
    return compile_and_run(analyse(src, name="t")).strip()


@requires_dotnet_toolchain
def test_top_bit_set_hex_is_negative(compile_and_run):
    assert _out(compile_and_run, "PRINT &AABBCCDD = -1430532899\n") == "-1"  # TRUE


@requires_dotnet_toolchain
def test_all_ones_hex_is_minus_one(compile_and_run):
    assert _out(compile_and_run, "PRINT &FFFFFFFF\n") == "-1"


@requires_dotnet_toolchain
def test_stored_hex_round_trips_through_word_indirection(compile_and_run):
    # !addr store of a top-bit-set hex now succeeds (was "out of range").
    assert _out(compile_and_run, "DIM b% 8:!b%=&AABBCCDD:PRINT !b% = -1430532899\n") == "-1"


@requires_dotnet_toolchain
@pytest.mark.xfail(
    reason="~ hex print pads with a leading zero (0AABBCCDD vs AABBCCDD) -- a "
    "separate, pre-existing OwlRuntime print-format bug, not the hex value",
    strict=True,
)
def test_tilde_hex_prints_minimal_digits(compile_and_run):
    assert _out(compile_and_run, "PRINT ~&AABBCCDD\n") == "AABBCCDD"
