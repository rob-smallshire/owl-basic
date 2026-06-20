"""A DEF FN/PROC formal parameter may be any assignable location (lvalue), not
just a simple variable.

The BBC BASIC II ROM parses each formal with ``parse_lvalue`` -- the very routine
that parses the left-hand side of LET and FOR -- so variables, array elements and
``?``/``!``/``$`` indirection are all legal formals. Binding is by reference: the
argument is assigned into the lvalue, its prior contents saved and restored across
the call (so e.g. ``DEF FNd(X,$@%)`` writes the string argument to the address in
@% for the duration of the call). This mirrors that: a formal is OWL's ``writable``.
"""
import io
import logging

from helpers import parse, walk
from owl_basic.syntax.ast import (
    DefineFunction,
    DefineProcedure,
    DyadicByteIndirection,
    Indexer,
    UnaryByteIndirection,
    UnaryIntegerIndirection,
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


def test_simple_variable_formal_still_parses():
    tree = _parse_clean("DEFFNx(A)=A\n")
    assert any(isinstance(n, DefineFunction) for n in walk(tree))


def test_byte_indirection_formal():
    assert _has("DEFFNx(?A)=1\n", UnaryByteIndirection)


def test_word_indirection_formal():
    assert _has("DEFFNx(!A)=1\n", UnaryIntegerIndirection)


def test_string_indirection_formal():
    assert _has('DEFFNx($A)="z"\n', UnaryStringIndirection)


def test_string_indirection_through_pseudovar_formal():
    # The rheolism case: DEF FNd(X, $@%) -- a string written to the address in @%.
    assert _has('DEFFNd(X,$@%)=1\n', UnaryStringIndirection)


def test_dyadic_byte_indirection_formal():
    assert _has("DEFPROCx(A?B):ENDPROC\n", DyadicByteIndirection)


def test_array_element_formal():
    assert _has("DEFFNx(A(I))=1\n", Indexer)


def test_proc_byte_indirection_formal():
    assert _has("DEFPROCx(?A):ENDPROC\n", UnaryByteIndirection)
