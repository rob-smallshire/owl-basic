"""EVAL of a *run-time* string is not yet supported, and is rejected clearly.

A constant-string EVAL is compiled statically (see test_eval_static). But an EVAL
whose argument is only known at run time -- a string variable, input, etc. --
needs an embedded run-time expression evaluator (as the interpreter has) and a
dynamic result type, a project of its own OWL does not yet provide. Rather than
mislead (it used to surface as a spurious "+ incompatible" type error when an EVAL
result met a string) OWL rejects such a program up front, naming EVAL. The message
states the missing capability, not that EVAL is impossible.
"""
import pytest

from owl_basic.analysis import analyse
from owl_basic.exceptions import CompileError


def test_runtime_string_eval_is_rejected_with_a_clear_message():
    with pytest.raises(CompileError) as excinfo:
        analyse('B$ = "1+2"\nA = EVAL(B$)\nEND\n', name="t")
    assert "EVAL" in str(excinfo.value)


def test_eval_in_string_concatenation_is_rejected_not_a_type_error():
    # The shape from the corpus: l$ = l$ + EVAL(...). With a run-time argument the
    # diagnostic must name EVAL, not complain about the '+'.
    with pytest.raises(CompileError) as excinfo:
        analyse('C$ = "B$"\nA$ = "x" + EVAL(C$)\nEND\n', name="t")
    message = str(excinfo.value)
    assert "EVAL" in message
    assert "+" not in message
