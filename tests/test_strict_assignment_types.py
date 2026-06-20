"""Strict string/numeric assignment checking.

BBC BASIC keeps strings and numbers firmly apart: A$ holds only strings, A holds
only numbers, and mixing them is a Type mismatch. OWL's type system modelled
StringOwlType as a subtype of the boxed ObjectOwlType and so inherited Object's
"convertible to/from anything", silently accepting A$=5 and A=FNstring. These
pin the stricter behaviour: such mismatches are reported, never silently
miscompiled, and the front end never crashes (sys.exit) doing so.
"""
import logging

import pytest

from owl_basic.analysis import analyse


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


# --- a string variable rejects a numeric value -----------------------------

def test_string_var_rejects_numeric_literal():
    assert _errors('A$=5\n'), "A$=5 should be a type mismatch"


def test_string_var_rejects_numeric_function_result():
    assert _errors('A$=FNf\nEND\nDEFFNf=3.14\n'), \
        "assigning a float function result to a string variable should error"


# --- a numeric variable rejects a string value -----------------------------

def test_numeric_var_rejects_string_literal():
    assert _errors('A="hi"\n'), 'A="hi" should be a type mismatch'


def test_numeric_var_rejects_string_function_result():
    assert _errors('A=FNs\nEND\nDEFFNs="hi"\n'), \
        "assigning a string function result to a numeric variable should error"


# --- legitimate same-category assignments stay clean -----------------------

def test_string_var_accepts_string():
    assert _errors('A$="hi"\n') == []


def test_string_var_accepts_string_function_result():
    assert _errors('A$=FNs\nEND\nDEFFNs="hi"\n') == []


def test_numeric_var_accepts_numeric_function_result():
    assert _errors('A=FNf\nEND\nDEFFNf=3.14\n') == []


# --- a numeric/string mix in an expression is graceful, never a crash ------

def test_numeric_plus_string_does_not_crash():
    # `1 + "x"` is a Type mismatch in BBC BASIC; OWL must report it (or box it)
    # without leaving the node untyped and crashing on "no type information".
    # The contract under test is "no sys.exit", which pytest enforces by the
    # call simply returning.
    _errors('A=FNm\nEND\nDEFFNm=1+"x"\n')
