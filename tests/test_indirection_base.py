"""The base of a ?/! indirection may be any factor, not just a simple variable.

`base?offset` reads the byte at base+offset; `base!offset` the integer. The base
is an address-valued l-value primary -- commonly an array element (A%(i)?j), not
only a bare variable. The grammar restricted it to a variable, so the
array-element idiom failed to parse. Surfaced by The Micro User
HOOKED/MCL/SEVENS/5ALIVE2/5DATA (e.g. U%(z%)?bw%, HAND%(C%)?L%).
"""
from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse


def test_array_element_base_byte_indirection_parses():
    assert analyse("DIM A%(8)\nx=A%(1)?2\nEND\n", name="t") is not None


def test_array_element_base_and_offset_parses():
    assert analyse("DIM A%(8),B%(8)\nx=A%(1)?B%(2)\nEND\n", name="t") is not None


def test_array_element_base_pling_parses():
    assert analyse("DIM A%(8)\nx=A%(1)!4\nEND\n", name="t") is not None


@requires_dotnet_toolchain
def test_array_element_base_indirection_reads_memory(compile_and_run):
    # A%(1) holds a base address; A%(1)?3 reads the byte written at base+3.
    out = compile_and_run(analyse(
        "DIM mem 16\n"
        "DIM A%(2)\n"
        "A%(1)=mem\n"
        "?(mem+3)=65\n"
        "PRINT A%(1)?3\n", name="t"))
    assert out.strip() == "65"
