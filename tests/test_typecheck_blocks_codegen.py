"""A program with type errors must not be lowered to code.

Type checking reports mismatches (e.g. 1+"x", or assigning a number to a string
variable) but recovers so it can collect every diagnostic in one pass. Recovery
must not, however, let a broken program reach the code generator: lowering it
produces nonsense IL (a string reinterpreted as a float, say) that assembles and
"runs". The backend refuses to lower a program that did not type-check.
"""
import pytest

from conftest import requires_dotnet_toolchain
from owl_basic.analysis import analyse
from owl_basic.exceptions import CompileError


def test_emit_il_refuses_a_program_with_type_errors(dotnet_backend):
    program = analyse('A=1+"x"\nEND\n', name="t")
    with pytest.raises(CompileError):
        dotnet_backend.emit_il(program)


def test_string_to_numeric_assignment_is_not_lowered(dotnet_backend):
    program = analyse('A="hi"\nEND\n', name="t")
    with pytest.raises(CompileError):
        dotnet_backend.emit_il(program)


def test_clean_program_still_lowers(dotnet_backend):
    # The gate must not block a well-typed program.
    il = dotnet_backend.emit_il(analyse('PRINT 6*7\nEND\n', name="t"))
    assert "Print(int32)" in il


@requires_dotnet_toolchain
def test_type_error_never_assembles(compile_and_run):
    # The end-to-end path must raise rather than assemble garbage and run it.
    with pytest.raises(CompileError):
        compile_and_run(analyse('A=1+"x":PRINT A\nEND\n', name="t"))
