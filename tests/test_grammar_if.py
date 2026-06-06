"""Narrowly-scoped parser tests for single-line IF (red-green-refactor).

Reproduces the regression where ``IF <cond> THEN <statement>`` (no ELSE) fails
to parse: the single-line form collides with the multi-line ``IF ... THEN ...
ENDIF`` form, so the parser waits for ENDIF and hits end-of-input.
"""

import logging

import pytest

from owl_basic.syntax import parser as _parser


class _Options:
    debug_lex = False
    verbose = False
    use_clr = False


class ParseError(Exception):
    pass


class _CaptureErrors(logging.Handler):
    def __init__(self):
        super().__init__()
        self.messages = []

    def emit(self, record):
        self.messages.append(record.getMessage())


def parse_statements(source):
    """Parse one program; raise ParseError on any syntax error.

    Returns the list of top-level statements.
    """
    handler = _CaptureErrors()
    root = logging.getLogger()
    root.addHandler(handler)
    previous_level = root.level
    root.setLevel(logging.ERROR)
    try:
        tree = _parser.parse(
            source if source.endswith("\n") else source + "\n", _Options()
        )
    finally:
        root.removeHandler(handler)
        root.setLevel(previous_level)
    errors = [m for m in handler.messages if "Syntax error" in m]
    if errors:
        raise ParseError(errors[0])
    return list(tree.statements.statements)


def _types(statements):
    return [type(s).__name__ for s in statements]


def test_if_without_then_parses():
    # Known-good guard: IF <cond> <statement> (no THEN) already works.
    assert "If" in _types(parse_statements('IF A=1 PRINT"x"'))


def test_if_then_else_parses():
    # Known-good guard: IF <cond> THEN <statement> ELSE <statement> works.
    assert "If" in _types(parse_statements('IF A=1 THEN PRINT"x" ELSE PRINT"y"'))


def test_if_then_single_statement_without_else_parses():
    # The regression: IF <cond> THEN <statement> with no ELSE.
    assert "If" in _types(parse_statements('IF A=1 THEN PRINT"x"'))


def test_if_then_function_return_without_else_parses():
    # The "IF A=X =Z" case: IF <cond> THEN =<expr> (a function return) with no ELSE.
    assert "If" in _types(parse_statements("IF N=1 THEN =1"))
