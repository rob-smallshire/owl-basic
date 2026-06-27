"""INPUT reads into any assignable l-value, not just a variable or array element.

INPUT shares the assignment store path (_store_to_lvalue), so it accepts every
target LET accepts -- including the ?/!/$ indirections. INPUT $addr reads a
string into memory; the emitter used to reject it with "INPUT item
'UnaryStringIndirection' not supported". Surfaced by The Micro User
D-MU05_05.EORENCR (INPUT "Codeword",$C%).
"""
from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse


def test_input_into_string_indirection_compiles(dotnet_backend):
    assert dotnet_backend.emit_il(analyse(
        "DIM C% 32\nINPUT $C%\nEND\n", name="t"))


def test_input_into_byte_indirection_compiles(dotnet_backend):
    assert dotnet_backend.emit_il(analyse(
        "DIM B% 8\nINPUT ?B%\nEND\n", name="t"))


@requires_dotnet_toolchain
def test_input_into_string_indirection_runs(compile_and_run):
    out = compile_and_run(analyse(
        "DIM C% 32\nINPUT $C%\nPRINT $C%\n", name="t"), stdin="hello\n")
    assert out.strip().endswith("hello")


@requires_dotnet_toolchain
def test_input_into_byte_indirection_runs(compile_and_run):
    out = compile_and_run(analyse(
        "DIM B% 8\nINPUT ?B%\nPRINT ?B%\n", name="t"), stdin="65\n")
    assert out.strip().endswith("65")


@requires_dotnet_toolchain
def test_input_into_scalar_and_array_still_work(compile_and_run):
    # Regression: the common targets are unaffected by the generalisation.
    out = compile_and_run(analyse(
        "DIM A(3)\nINPUT X,A(1)\nPRINT X;\" \";A(1)\n", name="t"),
        stdin="7\n9\n")
    # The printed values follow the "?" input prompt on the same line.
    assert out.strip().endswith("7 9")
