"""Functions whose return type is a union (sum) of several path types.

A DEF FN that returns, say, an integer on one path and a string on another has no
single concrete type. Collapsing that to the boxed Object lost information: the
type checker then accepted A$ = FNint_or_str(x) silently, even though one branch
yields a number. Modelling it as a genuine sum type Integer|String lets the rule
be structural -- a value of type A|B is assignable to T only if BOTH A and B are
assignable to T -- so:

  * a numeric var or a string var rejects an int|string (one branch never fits);
  * PRINT, which accepts any scalar, accepts it (every branch is a scalar);
  * an int|float, whose branches both fit a float, assigns to a float fine.
"""
import logging

import pytest

from owl_basic.analysis import analyse

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


def test_int_or_string_rejected_by_string_assignment():
    # The integer branch cannot become a string.
    assert _errors("A$=FNm(1)\nEND\n" + _INT_OR_STR), \
        "A$ = (int|string) should be a type mismatch"


def test_int_or_string_rejected_by_numeric_assignment():
    # The string branch cannot become a number.
    assert _errors("A=FNm(1)\nEND\n" + _INT_OR_STR), \
        "A = (int|string) should be a type mismatch"


def test_int_or_float_assigns_to_a_float():
    # Both branches are assignable to a float, so this is fine.
    assert _errors("A=FNn(1)\nEND\n" + _INT_OR_FLOAT) == []


def test_int_or_float_rejected_by_string_assignment():
    # Neither numeric branch is a string.
    assert _errors("A$=FNn(1)\nEND\n" + _INT_OR_FLOAT), \
        "A$ = (int|float) should be a type mismatch"


# FNt returns Integer, Float and String across three paths.
_INT_FLOAT_STR = 'DEFFNt(N)IF N>2 THEN=1\nIF N>1 THEN=2.5\n="x"\n'


def test_three_way_sum_collapses_numerics_canonically():
    # The numeric members (Integer, Float) must collapse to Float regardless of
    # the order the return paths are walked, leaving a stable Float|String. The
    # message naming the type proves the canonical form.
    errors = _errors("A=FNt(1)\nEND\n" + _INT_FLOAT_STR)
    assert errors, "A = (int|float|string) should be a type mismatch"
    assert "Float | String" in errors[0], errors


def test_three_way_sum_still_prints():
    assert _errors("PRINT FNt(1)\nEND\n" + _INT_FLOAT_STR) == []
