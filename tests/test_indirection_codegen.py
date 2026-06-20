"""Codegen for ?/!/$/| indirection as both r-value and l-value (store).

Byte ``?`` was already supported; integer ``!``, string ``$`` and float ``|``
indirection had no emitter (``$A="x"`` / ``!A=5`` raised CodeGenerationError).
These round-trip a value through an address in the OwlRuntime address space.
"""
from conftest import requires_dotnet_toolchain
from owl_basic.analysis import analyse

# A heap-safe address well clear of OwlRuntime's allocator base (0x100).
_ADDR = "A%=&1000:"


@requires_dotnet_toolchain
def test_byte_indirection_round_trip(compile_and_run):
    assert compile_and_run(analyse(_ADDR + "?A%=200:PRINT?A%\n", name="t")).strip() == "200"


@requires_dotnet_toolchain
def test_integer_indirection_round_trip(compile_and_run):
    out = compile_and_run(analyse(_ADDR + "!A%=1000000:PRINT!A%\n", name="t"))
    assert out.strip() == "1000000"


@requires_dotnet_toolchain
def test_dyadic_integer_indirection(compile_and_run):
    out = compile_and_run(analyse(_ADDR + "A%!4=12345:PRINTA%!4\n", name="t"))
    assert out.strip() == "12345"


@requires_dotnet_toolchain
def test_string_indirection_round_trip(compile_and_run):
    out = compile_and_run(analyse(_ADDR + '$A%="HELLO":PRINT$A%\n', name="t"))
    assert out.strip() == "HELLO"


@requires_dotnet_toolchain
def test_string_indirection_length(compile_and_run):
    out = compile_and_run(analyse(_ADDR + '$A%="HELLO":PRINTLEN$A%\n', name="t"))
    assert out.strip() == "5"


@requires_dotnet_toolchain
def test_float_indirection_round_trip(compile_and_run):
    out = compile_and_run(analyse(_ADDR + "|A%=3.5:PRINT|A%\n", name="t"))
    assert out.strip() == "3.5"
