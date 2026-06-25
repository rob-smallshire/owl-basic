"""Constant folding of operators and functions, verified through to codegen.

The host-side evaluator (owl_basic.constant_folding) is invoked from the type
checker (`_foldConstant`), which replaces a pure-constant subtree with a literal
before code generation. These tests assert both that folding *happens* (the
emitted IL is identical to the hand-written literal) and that the folded value
matches the one the runtime computes -- a constant-vs-variable differential, so a
folder that disagreed with the runtime (e.g. wrong truncation direction for DIV,
or wrong sign for MOD) would be caught.

See docs/eval-static-compilation.md (the constant-folding foundation).
"""
import pytest

from conftest import requires_dotnet_toolchain
from owl_basic.analysis import analyse


def _il(dotnet_backend, source):
    return dotnet_backend.emit_il(analyse(source, name="t"))


def _folds_to(dotnet_backend, expression_source, literal_source):
    """The expression compiles to exactly the IL of the hand-written literal."""
    return (_il(dotnet_backend, "PRINT %s\n" % expression_source)
            == _il(dotnet_backend, "PRINT %s\n" % literal_source))


# --- regression: existing reach (unary functions already fold) -------------

def test_standalone_transcendental_folds(dotnet_backend):
    assert "System.Math::Sin" not in _il(dotnet_backend, "PRINT SIN(RAD(30))\n")


def test_standalone_abs_folds(dotnet_backend):
    assert _folds_to(dotnet_backend, "ABS(-5)", "5")


# --- TRUE / FALSE / unary plus --------------------------------------------

def test_true_false_fold_compositionally(dotnet_backend):
    assert _folds_to(dotnet_backend, "2*TRUE", "-2")     # TRUE = -1
    assert _folds_to(dotnet_backend, "1+FALSE", "1")     # FALSE = 0


@requires_dotnet_toolchain
def test_true_false_run(compile_and_run):
    out = compile_and_run(analyse(
        "PRINT TRUE\nPRINT FALSE\nPRINT 2*TRUE\n", name="t"))
    assert out.split() == ["-1", "0", "-2"]


# --- integer DIV / MOD -----------------------------------------------------

def test_div_mod_fold(dotnet_backend):
    assert _folds_to(dotnet_backend, "7 DIV 2", "3")
    assert _folds_to(dotnet_backend, "7 MOD 3", "1")


@requires_dotnet_toolchain
def test_div_mod_fold_matches_runtime(compile_and_run):
    # DIV truncates toward zero and MOD takes the sign of the dividend; check the
    # folded constant agrees with the runtime computation on negative operands.
    folded = compile_and_run(analyse(
        "PRINT 7 DIV 2\nPRINT -7 DIV 2\nPRINT 7 MOD 3\n"
        "PRINT -7 MOD 3\nPRINT 7 MOD -3\n", name="t"))
    runtime = compile_and_run(analyse(
        "A%=7\nB%=2\nC%=-7\nD%=3\nE%=-3\n"
        "PRINT A% DIV B%\nPRINT C% DIV B%\nPRINT A% MOD D%\n"
        "PRINT C% MOD D%\nPRINT A% MOD E%\n", name="t"))
    assert folded.split() == runtime.split()
    assert folded.split() == ["3", "-3", "1", "-1", "1"]


# --- bitwise AND / OR / EOR / NOT -----------------------------------------

def test_bitwise_fold(dotnet_backend):
    assert _folds_to(dotnet_backend, "5 AND 3", "1")
    assert _folds_to(dotnet_backend, "5 OR 2", "7")
    assert _folds_to(dotnet_backend, "5 EOR 1", "4")
    assert _folds_to(dotnet_backend, "NOT 0", "-1")


@requires_dotnet_toolchain
def test_bitwise_fold_matches_runtime(compile_and_run):
    folded = compile_and_run(analyse(
        "PRINT 5 AND 3\nPRINT 5 OR 2\nPRINT 5 EOR 1\nPRINT NOT 0\nPRINT NOT 5\n",
        name="t"))
    runtime = compile_and_run(analyse(
        "A%=5\nB%=3\nC%=2\nD%=1\nZ%=0\n"
        "PRINT A% AND B%\nPRINT A% OR C%\nPRINT A% EOR D%\nPRINT NOT Z%\nPRINT NOT A%\n",
        name="t"))
    assert folded.split() == runtime.split()
    assert folded.split() == ["1", "7", "4", "-1", "-6"]


# --- relational operators (yield -1 / 0) -----------------------------------

def test_relational_fold(dotnet_backend):
    assert _folds_to(dotnet_backend, "1=1", "-1")
    assert _folds_to(dotnet_backend, "1=2", "0")
    assert _folds_to(dotnet_backend, "2<3", "-1")
    assert _folds_to(dotnet_backend, "2<=2", "-1")
    assert _folds_to(dotnet_backend, "3>=4", "0")
    assert _folds_to(dotnet_backend, "1<>2", "-1")


@requires_dotnet_toolchain
def test_relational_fold_matches_runtime(compile_and_run):
    exprs = ["1=1", "1=2", "2<3", "3<2", "2<=2", "3>=4", "1<>2", "2<>2"]
    folded = compile_and_run(analyse(
        "".join("PRINT %s\n" % e for e in exprs), name="t"))
    assert folded.split() == ["-1", "0", "-1", "0", "-1", "0", "-1", "0"]


# --- string functions of constants -----------------------------------------

def test_numeric_string_functions_fold(dotnet_backend):
    assert _folds_to(dotnet_backend, 'LEN("hello")', "5")
    assert _folds_to(dotnet_backend, 'ASC("A")', "65")
    assert _folds_to(dotnet_backend, 'INSTR("HELLO","L")', "3")


def test_string_valued_functions_fold_to_literal(dotnet_backend):
    # The runtime helper is gone; the result is a string literal.
    il = _il(dotnet_backend, 'PRINT LEFT$("HELLO",2)\n')
    assert "BasicCommands::LeftStr" not in il
    assert _il(dotnet_backend, 'PRINT LEFT$("HELLO",2)\n') == _il(
        dotnet_backend, 'PRINT "HE"\n')
    assert _il(dotnet_backend, 'PRINT MID$("HELLO",2,3)\n') == _il(
        dotnet_backend, 'PRINT "ELL"\n')


@requires_dotnet_toolchain
def test_string_functions_fold_and_run(compile_and_run):
    out = compile_and_run(analyse(
        'PRINT LEN("hello")\n'
        'PRINT ASC("A")\n'
        'PRINT LEFT$("HELLO",2)\n'
        'PRINT RIGHT$("HELLO",2)\n'
        'PRINT MID$("HELLO",2,3)\n'
        'PRINT STRING$(3,"ab")\n'
        'PRINT INSTR("HELLO","LO")\n'
        'PRINT VAL("3.5")+1\n', name="t"))
    assert out.split("\n") == ["5", "65", "HE", "LO", "ELL", "ababab", "4", "4.5", ""]
