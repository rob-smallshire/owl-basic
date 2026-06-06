"""Numeric literal lexing, including BBC BASIC's lone-dot quirk.

In BBC BASIC a bare ``.`` is the number 0 (``PRINT .`` prints 0), so digits are
optional on both sides of the decimal point. Sphinx relies on this for its
deliberate game-over infinite loop ``REPEAT UNTIL .`` (UNTIL 0, never true).
"""

from owl_basic.syntax import grammar
from helpers import parse


def _parses(source):
    parse(source)
    return not grammar.syntax_errors


def test_lone_dot_is_a_zero_literal():
    assert _parses("A = .")
    assert _parses("REPEAT UNTIL .")


def test_float_forms_with_optional_digits():
    for number in (".5", "5.", "5.5", "0.5", "2.5E3", ".5E-2"):
        assert _parses("X = " + number), number


def test_integers_and_floats_still_distinct():
    assert _parses("X% = 42")
    assert _parses("X = 3.14")
