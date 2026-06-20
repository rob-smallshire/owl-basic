"""A DEF FN's return type is inferred between two typecheck passes: the first
synthesises types with every user-function call left Pending, then return types
are inferred, then the second pass re-checks with those types known.

The first pass must therefore not *report* diagnostics: with calls still Pending,
a call result assigned to a typed variable, or a return value checked against the
not-yet-known return type, looks like a mismatch only because inference has not
run. Those spurious errors (and, via typeError -> internal(), a hard sys.exit)
were leaking out of the first pass for any function whose body did more than a
single bare `= expr`. Only the second, authoritative pass should speak.
"""
import logging

import pytest

from owl_basic.analysis import analyse


def _analysis_errors(src):
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


def test_function_with_statement_before_return_is_clean():
    # A body statement before the `= expr` return must not provoke a first-pass
    # "Cannot assign Pending to Float" once inference has run.
    assert _analysis_errors("A=FNU(1)\nEND\nDEFFNU(X)K=X:=0\n") == []


def test_function_using_a_formal_in_arithmetic_is_clean():
    # The shape the corpus starfields use: a real formal driving the body.
    src = ("A=FNU(1)\nEND\n"
           "DEFFNU(Y)K=-1+Y/512:=0\n")
    assert _analysis_errors(src) == []


def test_integer_function_result_assigned_to_float_is_clean():
    assert _analysis_errors("A=FNU(1)\nEND\nDEFFNU(X)=0\n") == []


def test_return_value_matches_inferred_type_no_spurious_mismatch():
    # The `= expr` must not be reported as "incompatible" with the (Pending)
    # return type during the first pass.
    errors = _analysis_errors("A=FNU(1)\nEND\nDEFFNU(X)K=X:=0\n")
    assert not any("ReturnFromFunction" in m for m in errors), errors
