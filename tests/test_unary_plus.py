"""Unary + is the identity on any scalar, strings included.

BBC BASIC's unary + is a no-op that accepts a string as well as a number, so
``+A$`` is ``A$`` and ``R6$++C$`` means ``R6$ + C$`` (string concatenation) --
verified on a real BBC Micro. OWL had typed unary + as numeric-only, leaving a
string operand untyped and crashing the type checker. Unary - stays numeric: a
string operand is a clean Type mismatch (as on the BBC), not a crash.
"""
import pytest

from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse
from owl_basic.exceptions import CompileError


@requires_dotnet_toolchain
def test_unary_plus_on_a_string_is_identity(compile_and_run):
    out = compile_and_run(analyse('C$="hi"\nPRINT +C$\nEND\n', name="up"))
    assert out.splitlines() == ["hi"]


@requires_dotnet_toolchain
def test_double_plus_is_concatenation(compile_and_run):
    # The Adventure idiom R6$++C$ == R6$ + (+C$) == R6$ + C$, exactly as a real
    # BBC Micro evaluates "HELLO" ++ " WORLD".
    out = compile_and_run(analyse(
        'R6$="HELLO"\nC$=" WORLD"\nPRINT R6$++C$\nEND\n', name="up"))
    assert out.splitlines() == ["HELLO WORLD"]


@requires_dotnet_toolchain
def test_unary_plus_on_a_number_is_identity(compile_and_run):
    out = compile_and_run(analyse('A=+5\nPRINT A\nEND\n', name="up"))
    assert out.strip() == "5"


def test_unary_minus_on_a_string_is_rejected():
    # -A$ is a Type mismatch on the BBC; OWL must reject it cleanly (a recorded
    # diagnostic that makes codegen refuse), not crash with a None type.
    from owl_basic.ext.backends.dotnet.emitter import emit_program
    program = analyse('C$="b"\nZ$=-C$\nEND\n', name="up")
    assert program.diagnostics
    with pytest.raises(CompileError):
        emit_program(program, "up")


def test_unary_minus_on_a_string_literal_is_rejected_not_a_crash():
    # The constant folder must treat -"a" as not-constant (return None), not try
    # to negate a Python str. The type checker then rejects it cleanly.
    program = analyse('X=-"a"\nEND\n', name="up")
    assert program.diagnostics
