"""End-to-end coverage of DEF FN return-type inference through analyse().

A DEF FN's return type is inferred between two typecheck passes: the first
synthesises types with every user-function call left Pending, then return types
are inferred (HM linking for pass-through equality, a promotion-lattice fixpoint
for recursion), then the second, authoritative pass re-checks with them known.

``test_hm_bridge`` unit-tests the inferencer in isolation; these drive the *whole*
front end and assert the two outcomes that matter to a user: a function that can
be typed compiles cleanly (no logged errors, the right inferred type), and one
that cannot is rejected with a clear, function-naming CompileError -- never a
silent wrong compile, an opaque "Pending" mismatch, or a sys.exit crash.
"""
import logging

import pytest

from helpers import function_return_types
from owl_basic.analysis import analyse
from owl_basic.exceptions import CompileError
from owl_basic.owltyping.type_system import (
    ByteOwlType,
    FloatOwlType,
    IntegerOwlType,
    ObjectOwlType,
    StringOwlType,
)


def _analyse_capturing_errors(src):
    """Analyse *src*; return (program, [logged ERROR+ messages])."""
    records = []

    class _Capture(logging.Handler):
        def emit(self, record):
            if record.levelno >= logging.ERROR:
                records.append(record.getMessage())

    handler = _Capture()
    root = logging.getLogger()
    root.addHandler(handler)
    try:
        program = analyse(src, name="t")
    finally:
        root.removeHandler(handler)
    return program, records


def _clean(src):
    program, errors = _analyse_capturing_errors(src)
    assert errors == [], errors
    return function_return_types(program)


# --------------------------------------------------------------------------
# Compiles cleanly, inferred to the right type.
# --------------------------------------------------------------------------

def test_integer_literal_return():
    assert _clean("A=FNx\nEND\nDEFFNx=42\n")["FNx"] is IntegerOwlType()


def test_float_literal_return():
    assert _clean("A=FNx\nEND\nDEFFNx=3.14\n")["FNx"] is FloatOwlType()


def test_string_literal_return():
    assert _clean('A$=FNx\nEND\nDEFFNx="hi"\n')["FNx"] is StringOwlType()


def test_statement_before_return_does_not_leak_a_pending_error():
    # The regression that started this: any body statement before the `= expr`
    # used to provoke a spurious first-pass "Cannot assign Pending to Float".
    assert _clean("A=FNu(1)\nEND\nDEFFNu(X)K=X:=0\n")["FNu"] is IntegerOwlType()


def test_real_formal_drives_a_float_body():
    # The corpus starfield shape: a real (float) formal used in arithmetic.
    types = _clean("A=FNu(1)\nEND\nDEFFNu(Y)K=-1+Y/512:=Y*2\n")
    assert types["FNu"] is FloatOwlType()


def test_integer_formal_arithmetic_stays_integer():
    # int32*int32 is evaluated in 64 bits for overflow safety, but that widening
    # is transparent: the logical return type is Integer, not LongInteger (and
    # certainly never Object, which is what the unmodelled widening produced).
    assert _clean("A=FNi(1)\nEND\nDEFFNi(N%)=N%*2\n")["FNi"] is IntegerOwlType()


def test_division_is_always_float():
    assert _clean("A=FNd(7)\nEND\nDEFFNd(N)=N/2\n")["FNd"] is FloatOwlType()


def test_string_concatenation_stays_string():
    assert _clean('A$=FNc("x")\nEND\nDEFFNc(S$)=S$+"!"\n')["FNc"] is StringOwlType()


def test_numeric_plus_string_boxes_to_object():
    # BBC BASIC would Type-mismatch at run time; OWL models the mixed result as
    # Object rather than crashing the compiler.
    assert _clean('A=FNm\nEND\nDEFFNm=1+"x"\n')["FNm"] is ObjectOwlType()


def test_multiple_return_paths_promote_to_the_wider_type():
    # One path returns integer 1, the other float 2.5: the function is Float.
    types = _clean("A=FNc(1)\nEND\nDEFFNc(N)IF N>0 THEN=1\n=2.5\n")
    assert types["FNc"] is FloatOwlType()


def test_local_variable_in_body():
    assert _clean("A=FNl(2)\nEND\nDEFFNl(X)LOCAL T:T=X*2:=T\n")["FNl"] is FloatOwlType()


def test_pass_through_return_takes_the_callee_type():
    # = FNb is type *equality* with FNb (HM linking), resolved before FNb's own
    # literal return is even reached.
    types = _clean("A=FNa\nEND\nDEFFNa=FNb\nDEFFNb=5\n")
    assert types["FNa"] is IntegerOwlType()
    assert types["FNb"] is IntegerOwlType()


def test_self_recursion_with_a_base_case_resolves():
    src = ("A=FNf(5)\nEND\n"
           "DEFFNf(N)IF N<2 THEN=1\n=N*FNf(N-1)\n")
    assert _clean(src)["FNf"] is FloatOwlType()


def test_mutual_recursion_with_a_base_case_resolves():
    src = ("A=FNe(4)\nEND\n"
           "DEFFNe(N)IF N=0 THEN=1\n=FNo(N-1)\n"
           "DEFFNo(N)IF N=0 THEN=0\n=FNe(N-1)\n")
    types = _clean(src)
    assert types["FNe"] is IntegerOwlType()
    assert types["FNo"] is IntegerOwlType()


def test_nested_function_call_argument():
    assert _clean("A=FNa(FNb(2))\nEND\nDEFFNa(X)=X+1\nDEFFNb(X)=X*2\n")["FNa"] \
        is FloatOwlType()


@pytest.mark.parametrize("body,expected", [
    ("=?p%", ByteOwlType),       # byte indirection reads a byte
    ("=!p%", IntegerOwlType),    # 32-bit integer indirection
    ("=$p%", StringOwlType),     # string indirection
])
def test_indirection_return_types(body, expected):
    # The return value is read through an indirection operator; the inferencer
    # used to leave these unmodelled (Pending), which leaked an error.
    formal = body[1] + "p%"  # ?p% / !p% / $p%
    assign = "A$=" if expected is StringOwlType else "A="
    src = "%sFNr(0)\nEND\nDEFFNr(%s)%s\n" % (assign, formal, body)
    assert _clean(src)["FNr"] is expected()


# --------------------------------------------------------------------------
# Rejected gracefully with a clear, function-naming message (never a crash).
# --------------------------------------------------------------------------

def test_self_recursion_with_no_base_case_is_rejected():
    with pytest.raises(CompileError) as excinfo:
        analyse("A=FNa(1)\nEND\nDEFFNa(N)=FNa(N-1)\n", name="t")
    message = str(excinfo.value)
    assert "FNa" in message
    assert "return type" in message.lower()


def test_mutual_recursion_with_no_base_case_is_rejected():
    with pytest.raises(CompileError) as excinfo:
        analyse("A=FNa(1)\nEND\nDEFFNa(N)=FNb(N)\nDEFFNb(N)=FNa(N)\n", name="t")
    message = str(excinfo.value)
    assert "FNa" in message or "FNb" in message


def test_rejection_is_not_a_sys_exit():
    # Regression guard: an unresolved return type must raise CompileError, not
    # take down the compiler host through internal()/sys.exit.
    with pytest.raises(CompileError):
        analyse("A=FNa(1)\nEND\nDEFFNa(N)=FNa(N-1)\n", name="t")
