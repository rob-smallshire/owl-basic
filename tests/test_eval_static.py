"""Static compilation of EVAL whose argument is statically known.

Constant-string EVAL is lowered by re-parsing the string and splicing the
expression; downstream folding then reduces it. An EVAL whose argument is not a
compile-time-constant string is left for later increments and, for now, still
rejected with the honest "needs a run-time evaluator" message. A constant string
that is not a valid BASIC expression is rejected up front, naming it.

See docs/eval-static-compilation.md.
"""
import pytest

from conftest import requires_dotnet_toolchain
from owl_basic.analysis import analyse
from owl_basic.exceptions import CompileError


def _compiles(source):
    return not analyse(source, name="t").diagnostics


def test_eval_constant_arithmetic_compiles():
    assert _compiles('PRINT EVAL("1+2")\n')


def test_eval_constant_string_leaves_no_eval_node(dotnet_backend):
    # EVAL("1+2") lowers to 1+2 which folds to 3: no run-time evaluator, just a
    # constant in the emitted IL.
    il = dotnet_backend.emit_il(analyse('PRINT EVAL("1+2")\n', name="t"))
    assert "ldc.i4 3" in il or "ldc.i4.3" in il


@requires_dotnet_toolchain
def test_eval_constant_arithmetic_runs(compile_and_run):
    assert compile_and_run(analyse('PRINT EVAL("1+2")\n', name="t")).split() == ["3"]


@requires_dotnet_toolchain
def test_eval_constant_function_folds_and_runs(compile_and_run):
    # The folder reduces SIN(RAD(30)) after the string is parsed; BBC prints 0.5.
    out = compile_and_run(analyse('PRINT EVAL("SIN(RAD(30))")\n', name="t"))
    assert out.split() == ["0.5"]


@requires_dotnet_toolchain
def test_eval_constant_string_concatenation_runs(compile_and_run):
    # The argument "2"+"+"+"3" folds to the constant string "2+3", then to 5.
    out = compile_and_run(analyse('PRINT EVAL("2"+"+"+"3")\n', name="t"))
    assert out.split() == ["5"]


@requires_dotnet_toolchain
def test_nested_eval_runs(compile_and_run):
    # EVAL("EVAL(""1+2"")"): lowering the outer exposes an inner EVAL, lowered in
    # turn. Both reduce to 3.
    out = compile_and_run(analyse('PRINT EVAL("EVAL(""1+2"")")\n', name="t"))
    assert out.split() == ["3"]


def test_eval_of_malformed_constant_string_is_rejected_naming_it():
    with pytest.raises(CompileError) as excinfo:
        analyse('PRINT EVAL("1+")\n', name="t")
    message = str(excinfo.value)
    assert "EVAL" in message
    assert "1+" in message            # the offending string is named


def test_eval_of_runtime_string_still_rejected():
    # A non-constant argument is the residue this increment does not handle; it
    # keeps the honest "needs a run-time evaluator" rejection.
    with pytest.raises(CompileError) as excinfo:
        analyse('A$="1+2"\nPRINT EVAL(A$)\n', name="t")
    assert "EVAL" in str(excinfo.value)
