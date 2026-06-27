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


@requires_dotnet_toolchain
def test_constant_skeleton_with_runtime_variable_runs(compile_and_run):
    # The string is constant, so it is parsed and spliced; the variable it names
    # is an ordinary free reference read at run time (category 1).
    out = compile_and_run(analyse('a%=10\nPRINT EVAL("a%*2-1")\n', name="t"))
    assert out.split() == ["19"]


# --- value-hole templates: the digit idiom -------------------------------
# EVAL of a string provably containing only decimal digits is EVAL == VAL, so it
# lowers to VAL of the same argument with no run-time evaluator.

def test_digit_idiom_compiles():
    assert _compiles('DEF FNd(K)=EVAL(MID$("13264",K,1))\n')


def test_digit_idiom_lowers_to_val_not_eval(dotnet_backend):
    il = dotnet_backend.emit_il(analyse(
        'PRINT FNd(1)\nEND\nDEF FNd(K)=EVAL(MID$("13264",K,1))\n', name="t"))
    assert "BasicCommands::Val" in il


@requires_dotnet_toolchain
def test_digit_idiom_runs_correctly(compile_and_run):
    # MID$("13264",K,1) is the K-th digit; EVAL of it is that digit's value.
    out = compile_and_run(analyse(
        'PRINT FNd(1)\nPRINT FNd(3)\nPRINT FNd(5)\nEND\n'
        'DEF FNd(K)=EVAL(MID$("13264",K,1))\n', name="t"))
    assert out.split() == ["1", "2", "4"]


@requires_dotnet_toolchain
def test_eval_of_left_str_digits_runs(compile_and_run):
    out = compile_and_run(analyse('PRINT EVAL(LEFT$("789",2))\nEND\n', name="t"))
    assert out.split() == ["78"]


def test_eval_of_slice_of_non_digit_string_still_rejected():
    # The source is not a digit-only literal, so EVAL != VAL in general: residue.
    with pytest.raises(CompileError) as excinfo:
        analyse('INPUT A$\nB=EVAL(MID$(A$,1,1))\nEND\n', name="t")
    assert "EVAL" in str(excinfo.value)


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
        analyse('INPUT A$\nPRINT EVAL(A$)\n', name="t")
    assert "EVAL" in str(excinfo.value)


# --- function-by-name dispatch -------------------------------------------
# EVAL("FN" + cmd$ + "(arg)") selects a function by a runtime name from the
# program's DEF FNs. It lowers to a synthesised helper that dispatches on the
# name string; no run-time evaluator is needed.

_AREA_PERIM = ('END\n'
               'DEF FNarea(r)=r*r\n'
               'DEF FNperim(r)=4*r\n')


def test_dispatch_with_named_argument_compiles():
    assert _compiles('arg=3\ncmd$="area"\nPRINT EVAL("FN"+cmd$+"(arg)")\n'
                     + _AREA_PERIM)


def test_dispatch_leaves_no_eval_node(dotnet_backend):
    # The EVAL is gone: the emitted IL calls the synthesised dispatch helper, not
    # any run-time evaluator.
    il = dotnet_backend.emit_il(analyse(
        'arg=3\ncmd$="area"\nPRINT EVAL("FN"+cmd$+"(arg)")\n' + _AREA_PERIM,
        name="t"))
    assert "FN_eval_dispatch_0" in il


@requires_dotnet_toolchain
def test_dispatch_with_named_argument_runs(compile_and_run):
    # cmd$ selects FNarea then FNperim at run time; arg is read from the ambient
    # (here global) variable.
    out = compile_and_run(analyse(
        'arg=3\n'
        'cmd$="area"\nPRINT EVAL("FN"+cmd$+"(arg)")\n'
        'cmd$="perim"\nPRINT EVAL("FN"+cmd$+"(arg)")\n'
        + _AREA_PERIM, name="t"))
    assert out.split() == ["9", "12"]


@requires_dotnet_toolchain
def test_dispatch_reads_local_argument_dynamically(compile_and_run):
    # The helper reads the named argument from the ambient backing field. Inside a
    # PROC that declared it LOCAL, that field holds the local value (dynamic
    # scoping) and the synchronously-called helper picks it up -- LOCAL-correct.
    out = compile_and_run(analyse(
        'cmd$="area"\nPROCgo\nEND\n'
        'DEF PROCgo\nLOCAL arg\narg=5\n'
        'PRINT EVAL("FN"+cmd$+"(arg)")\nENDPROC\n'
        'DEF FNarea(r)=r*r\nDEF FNperim(r)=4*r\n', name="t"))
    assert out.split() == ["25"]


@requires_dotnet_toolchain
def test_dispatch_with_chr34_string_value_hole_runs(compile_and_run):
    # The CHR$34 + s$ + CHR$34 idiom is a string-value hole: EVAL parses the
    # quoted literal back to s$, so it is passed by value to the named function.
    out = compile_and_run(analyse(
        'op$="size"\ns$="hello"\n'
        'PRINT EVAL("FN"+op$+"("+CHR$34+s$+CHR$34+")")\n'
        'END\n'
        'DEF FNsize(t$)=LEN(t$)\n', name="t"))
    assert out.split() == ["5"]


@requires_dotnet_toolchain
def test_dispatch_with_staged_literal_argument_runs(compile_and_run):
    # A literal argument is staged: EVAL("FN"+cmd$+"(3)") dispatches with 3 bound
    # to the real parameter.
    out = compile_and_run(analyse(
        'cmd$="area"\nPRINT EVAL("FN"+cmd$+"(3)")\n' + _AREA_PERIM, name="t"))
    assert out.split() == ["9"]


@requires_dotnet_toolchain
def test_dispatch_unknown_name_faults_at_runtime(compile_expecting_error):
    # A runtime name matching no DEF FN faults exactly as the interpreter's EVAL
    # would: "No such FN/PROC".
    out = compile_expecting_error(analyse(
        'arg=3\ncmd$="nope"\nPRINT EVAL("FN"+cmd$+"(arg)")\n' + _AREA_PERIM,
        name="t"))
    assert "No such FN/PROC" in out


def test_dispatch_runtime_argument_structure_is_rejected():
    # The callee name is runtime (fine) but an argument is *built* from a runtime
    # string -- that is general EVAL again, so it stays rejected.
    with pytest.raises(CompileError) as excinfo:
        analyse('cmd$="area"\nINPUT arg$\n'
                'B=EVAL("FN"+cmd$+"("+arg$+")")\n' + _AREA_PERIM, name="t")
    assert "EVAL" in str(excinfo.value)


# --- hex-to-int idiom: EVAL("&" + h$) ------------------------------------
# VAL is decimal-only, so EVAL("&"+h$) is the standard way to read a hex string.
# It lowers to a runtime hex parse (EvalHexFunc) -- no run-time evaluator.

def test_hex_idiom_compiles():
    assert _compiles('h$="FF"\nPRINT EVAL("&"+h$)\n')


def test_hex_idiom_lowers_to_evalhex_not_eval(dotnet_backend):
    il = dotnet_backend.emit_il(analyse('h$="FF"\nPRINT EVAL("&"+h$)\n', name="t"))
    assert "BasicCommands::EvalHex" in il


@requires_dotnet_toolchain
def test_hex_idiom_runs(compile_and_run):
    out = compile_and_run(analyse(
        'h$="FF"\nPRINT EVAL("&"+h$)\n'
        'h$="7FFFFFFF"\nPRINT EVAL("&"+h$)\n'
        'h$="FFFFFFFF"\nPRINT EVAL("&"+h$)\n'      # 32-bit signed pattern: -1
        'h$="FG"\nPRINT EVAL("&"+h$)\n', name="t"))  # reads F, stops at G
    assert out.split() == ["255", "2147483647", "-1", "15"]


@requires_dotnet_toolchain
def test_hex_idiom_bad_hex_faults_at_runtime(compile_expecting_error):
    # A leading non-hex character (here lowercase) reads zero digits: "Bad hex",
    # exactly as EVAL("&ff") faults on the BBC.
    out = compile_expecting_error(analyse('h$="ff"\nPRINT EVAL("&"+h$)\n', name="t"))
    assert "Bad hex" in out


def test_hex_with_runtime_trailing_structure_stays_rejected():
    # "&" + h$ + "+1" keeps a runtime structure beyond the hex string -- that is
    # general EVAL again, so it stays the honest residual rejection.
    with pytest.raises(CompileError) as excinfo:
        analyse('INPUT h$\nPRINT EVAL("&"+h$+"+1")\n', name="t")
    assert "EVAL" in str(excinfo.value)


# Hex content may be more than a bare "&" + one hole: constant hex digits after
# the "&" (EVAL("&0"+h$)) and several concatenated runtime parts (EVAL("&"+a$+b$))
# are all one hex string. Surfaced by The Micro User (DRIVER, LIST1, ULTIMA).

def test_hex_with_constant_digits_after_ampersand_compiles():
    assert _compiles('INPUT h$\nPRINT EVAL("&0"+h$)\n')


def test_hex_with_multipart_runtime_string_compiles():
    assert _compiles('INPUT a$\nINPUT b$\nPRINT EVAL("&"+a$+b$)\n')


@requires_dotnet_toolchain
def test_hex_with_constant_digits_runs(compile_and_run):
    # "&0"+h$ : the leading "0" is part of the hex string.
    out = compile_and_run(analyse('h$="F"\nPRINT EVAL("&0"+h$)\n', name="t"))
    assert out.strip() == "15"


@requires_dotnet_toolchain
def test_hex_multipart_runtime_runs(compile_and_run):
    out = compile_and_run(analyse(
        'a$="F"\nb$="F"\nPRINT EVAL("&"+a$+b$)\n', name="t"))
    assert out.strip() == "255"


def test_hex_with_non_hex_constant_text_stays_rejected():
    # "&" + h$ + ":1" -- the ":1" is not hex digits, so it is structure, not part
    # of the hex string: stay the honest residual rejection.
    with pytest.raises(CompileError):
        analyse('INPUT h$\nPRINT EVAL("&"+h$+":1")\n', name="t")


# --- STR$ value-hole: EVAL(STR$(e) + ...) --------------------------------
# Sound now that VAL scans the same number syntax as the expression parser:
# EVAL(STR$(e)+"+1") == VAL(STR$(e))+1. The STR$->parse round-trip is *kept*
# (reduced to VAL(STR$(e))), not cancelled to e -- so it agrees with EVAL even
# when STR$ is lossy. OWL's unary minus binds tighter than every binary
# operator, so a leading sign in STR$'s output groups as a unit exactly as VAL
# collapses it -- the reduction is precedence-safe in any position.

def test_str_template_compiles():
    assert _compiles('n=5\nPRINT EVAL(STR$(n)+"+1")\n')


def test_str_template_lowers_to_val_of_str(dotnet_backend):
    il = dotnet_backend.emit_il(analyse('n=5\nPRINT EVAL(STR$(n)+"+1")\n', name="t"))
    assert "BasicCommands::Val" in il          # the round-trip is kept...
    assert "BasicCommands::StrString" in il     # ...VAL of STR$, not a bare splice


@requires_dotnet_toolchain
def test_str_template_runs(compile_and_run):
    out = compile_and_run(analyse(
        'n=5\nPRINT EVAL(STR$(n)+"+1")\n'              # 6
        'a=3\nb=4\nPRINT EVAL(STR$(a)+"+"+STR$(b))\n'   # 7 (two holes)
        'm=5\nPRINT EVAL(STR$(m)+"*2")\n'              # 10
        'k=-5\nPRINT EVAL(STR$(k)+"*2")\n'             # -10 (sign in the hole)
        'p=3\nPRINT EVAL(STR$(p)+"^2")\n', name="t"))  # 9 (precedence-safe)
    assert out.split() == ["6", "7", "10", "-10", "9"]


def test_str_template_with_non_str_hole_stays_rejected():
    # A bare runtime string is not STR$(e); reducing it would be general EVAL.
    with pytest.raises(CompileError) as excinfo:
        analyse('INPUT A$\nB=EVAL(A$+"+1")\n', name="t")
    assert "EVAL" in str(excinfo.value)


def test_str_template_lexical_merge_stays_rejected():
    # STR$(n)+"0" fuses the formatted number with the appended digit
    # (EVAL("50") != VAL(STR$(5))...), so it is not soundly reducible.
    with pytest.raises(CompileError) as excinfo:
        analyse('n=5\nB=EVAL(STR$(n)+"0")\n', name="t")
    assert "EVAL" in str(excinfo.value)


def test_variable_by_name_reflective_write_stays_rejected():
    # FNassign2's callee is constant; the runtime thing is an l-value selected by
    # a string and passed by RETURN. That reflective write is out of scope for #9
    # and stays rejected.
    with pytest.raises(CompileError) as excinfo:
        analyse(
            'PROCassign("x$", "hi")\nEND\n'
            'DEF PROCassign(a$, b$)\n'
            'unused=EVAL("FNassign2(" + a$ + "," + CHR$34 + b$ + CHR$34 + ")")\n'
            'ENDPROC\n'
            'DEF FNassign2(RETURN a$, b$)\n'
            'a$=b$\n'
            '=0\n', name="t")
    assert "EVAL" in str(excinfo.value)


# --- function-by-name dispatch with a fixed prefix -----------------------
# EVAL("FNpart" + n$) names a family FNpart0, FNpart1, ... : a fixed prefix
# between "FN" and the runtime suffix. Dispatch folds the prefix into the runtime
# name, so it reduces to the by-name-dispatch case. Surfaced by The Micro User
# (EVAL("FNpart" + MID$(M$,X,1))).

_PARTS = ('END\n'
          'DEF FNpart0=10\n'
          'DEF FNpart1=20\n'
          'DEF FNpart2=30\n')


def test_dispatch_with_fixed_prefix_compiles():
    assert _compiles('n$="1"\nPRINT EVAL("FNpart"+n$)\n' + _PARTS)


def test_dispatch_with_fixed_prefix_leaves_no_eval_node(dotnet_backend):
    il = dotnet_backend.emit_il(analyse(
        'n$="1"\nPRINT EVAL("FNpart"+n$)\n' + _PARTS, name="t"))
    assert "FN_eval_dispatch_0" in il


@requires_dotnet_toolchain
def test_dispatch_with_fixed_prefix_runs(compile_and_run):
    out = compile_and_run(analyse(
        'n$="0"\nPRINT EVAL("FNpart"+n$)\n'
        'n$="2"\nPRINT EVAL("FNpart"+n$)\n' + _PARTS, name="t"))
    assert out.split() == ["10", "30"]
