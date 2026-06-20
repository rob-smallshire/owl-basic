"""EVAL cannot be statically compiled, so OWL rejects it with a clear message.

EVAL interprets a string as a BASIC expression at run time -- its result type and
behaviour are not knowable until then -- which a static compiler cannot reproduce.
Rather than mislead (it used to surface as a spurious "+ incompatible" type error
when an EVAL result met a string) OWL rejects a program using EVAL up front,
naming EVAL as the reason.
"""
import pytest

from owl_basic.analysis import analyse
from owl_basic.exceptions import CompileError


def test_eval_is_rejected_with_a_clear_message():
    with pytest.raises(CompileError) as excinfo:
        analyse('A=EVAL("1+2")\nEND\n', name="t")
    assert "EVAL" in str(excinfo.value)


def test_eval_in_string_concatenation_is_rejected_not_a_type_error():
    # The shape from the corpus: l$ = l$ + EVAL(...). The diagnostic must name
    # EVAL, not complain about the '+'.
    with pytest.raises(CompileError) as excinfo:
        analyse('A$="x"+EVAL("B$")\nEND\n', name="t")
    message = str(excinfo.value)
    assert "EVAL" in message
    assert "+" not in message
