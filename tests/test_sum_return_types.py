"""Functions whose return type is a union (sum) of several path types.

A DEF FN that returns, say, an integer on one path and a string on another has no
single concrete type; it is modelled as a sum (Integer|String) and returns a
boxed object. BBC BASIC is dynamically typed here -- the value carries its
runtime type -- so assigning a sum result to a concrete variable is allowed when
*some* member could fit, with a runtime-checked unbox: a genuine mismatch is a
run-time "Type mismatch", exactly as on the BBC. Only a sum *none* of whose
members fits the target (e.g. int|float into a string) is a compile-time error.
PRINT and other sum-accepting contexts take it directly (every branch is a
scalar). The cost is pay-for-use: only a sum-returning FN boxes, and only a
concrete assignment/comparison of its result unboxes.
"""
import logging

import pytest

from owl_basic.analysis import analyse


def _fn_return_doc(src, call_name):
    """The inferred result-type name of the first *call_name* call in *src*."""
    program = analyse(src, name="t")
    tree = program.parse_tree if hasattr(program, "parse_tree") else program
    found = []

    def walk(node):
        if node is None or not hasattr(node, "forEachChild"):
            return
        if type(node).__name__ == "UserFunc" and node.name == call_name:
            found.append(node.actualType.__doc__)
        node.forEachChild(walk)

    walk(tree)
    return found[0] if found else None

# FNm returns Integer on the N>0 path and String otherwise: a genuine Integer|String.
_INT_OR_STR = "DEFFNm(N)IF N>0 THEN=1\n=\"hi\"\n"
# FNn returns Integer or Float: both branches assign to a float.
_INT_OR_FLOAT = "DEFFNn(N)IF N>0 THEN=1\n=2.5\n"


def _errors(src):
    records = []

    class _Capture(logging.Handler):
        def emit(self, record):
            if record.levelno >= logging.ERROR:
                records.append(record.getMessage())

    handler = _Capture()
    root = logging.getLogger()
    root.addHandler(handler)
    try:
        analyse(src, name="t")
    finally:
        root.removeHandler(handler)
    return records


def test_int_or_string_prints_cleanly():
    # PRINT accepts any scalar, and both branches are scalars.
    assert _errors("PRINT FNm(1)\nEND\n" + _INT_OR_STR) == []


def test_int_or_string_assigns_to_string_with_runtime_check():
    # The string member can fit, so the assignment is allowed; if the runtime
    # value is the integer branch instead, it is a run-time Type mismatch.
    assert _errors("A$=FNm(1)\nEND\n" + _INT_OR_STR) == []


def test_int_or_string_assigns_to_numeric_with_runtime_check():
    # The integer member can fit a float, so the assignment is allowed; the string
    # branch would be a run-time Type mismatch.
    assert _errors("A=FNm(1)\nEND\n" + _INT_OR_STR) == []


def test_int_or_float_assigns_to_a_float():
    # Both branches are assignable to a float, so this is fine.
    assert _errors("A=FNn(1)\nEND\n" + _INT_OR_FLOAT) == []


def test_int_or_float_rejected_by_string_assignment():
    # Neither numeric branch fits a string, so this stays a compile-time error
    # (the runtime-unbox relaxation only applies when some member could fit).
    assert _errors("A$=FNn(1)\nEND\n" + _INT_OR_FLOAT), \
        "A$ = (int|float) should be a type mismatch"


# FNt returns Integer, Float and String across three paths.
_INT_FLOAT_STR = 'DEFFNt(N)IF N>2 THEN=1\nIF N>1 THEN=2.5\n="x"\n'


def test_three_way_sum_collapses_numerics_canonically():
    # The numeric members (Integer, Float) must collapse to Float regardless of
    # the order the return paths are walked, leaving a stable Float|String. The
    # assignment no longer errors (a member fits), so check the inferred type
    # directly proves the canonical form.
    assert _fn_return_doc("A=FNt(1)\nEND\n" + _INT_FLOAT_STR, "FNt") == "Float | String"


def test_three_way_sum_still_prints():
    assert _errors("PRINT FNt(1)\nEND\n" + _INT_FLOAT_STR) == []
