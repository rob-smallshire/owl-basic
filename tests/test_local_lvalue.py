"""LOCAL takes any assignable location (lvalue), not just variables and arrays.

The BBC BASIC II ROM parses each LOCAL item with parse_lvalue -- the same routine
used for LET, FOR and DEF FN/PROC formal parameters -- so a ?/!/$ indirection cell
can be made local, its contents saved on entry and restored on return. (An
indirection formal parameter is mechanically a LOCAL of that cell followed by an
assignment of the argument.)
"""
import io
import logging

from helpers import parse, walk
from owl_basic.syntax.ast import (
    DyadicByteIndirection,
    Local,
    UnaryByteIndirection,
    UnaryStringIndirection,
)


def _parse_clean(source):
    capture = io.StringIO()
    handler = logging.StreamHandler(capture)
    logging.getLogger().addHandler(handler)
    try:
        tree = parse(source)
    finally:
        logging.getLogger().removeHandler(handler)
    assert not capture.getvalue().strip(), f"parse errors: {capture.getvalue().strip()}"
    return tree


def _has(source, node_type):
    return any(isinstance(n, node_type) for n in walk(_parse_clean(source)))


def test_local_simple_variable_still_parses():
    assert _has("LOCAL A\n", Local)


def test_local_byte_indirection():
    assert _has("LOCAL ?A\n", UnaryByteIndirection)


def test_local_string_indirection():
    assert _has("LOCAL $A\n", UnaryStringIndirection)


def test_local_dyadic_byte_indirection():
    assert _has("LOCAL A?B\n", DyadicByteIndirection)


def test_local_mixed_list():
    tree = _parse_clean("LOCAL I%,?A,$B\n")
    assert any(isinstance(n, UnaryByteIndirection) for n in walk(tree))
    assert any(isinstance(n, UnaryStringIndirection) for n in walk(tree))
