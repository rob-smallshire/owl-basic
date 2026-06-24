"""Indirection (`?` and `!`) binds tighter than unary minus.

In BBC BASIC the indirection operators are the highest-precedence operators, so
`-A?B` is `-(A?B)` -- read the byte (or word), then negate -- not `(-A)?B`, which
would be a negative base address. The corpus program a42cec506786 uses
`-@%?(3+x+10*z)`. OWL parsed a bare `A?B` but not a unary minus in front of it,
because dyadic indirection was reachable only as an arithmetic term, never as a
factor the unary minus could wrap.
"""
from owl_basic.analysis import analyse
from owl_basic.syntax.ast import (
    Assignment, UnaryMinus, DyadicByteIndirection, DyadicIntegerIndirection)
from helpers import walk


def _compiles(source):
    return not analyse(source, name="t").diagnostics


def test_unary_minus_before_byte_indirection_parses():
    # A?B alone already parsed; the unary minus in front is the gap.
    assert _compiles("A%=&2000\nb=-A%?5\n")


def test_unary_minus_before_indirection_with_offset_expr():
    # The corpus shape: -@%?(3+x). @% is a valid indirection base.
    assert _compiles("x=1\nb=-@%?(3+x)\n")


def test_unary_minus_indirection_negates_the_read():
    # Structurally -(A?B): a UnaryMinus wrapping the DyadicByteIndirection, not
    # an indirection of a negated base.
    program = analyse("A%=&2000\nb=-A%?5\n", name="t")
    negations = [n for n in walk(program.parse_tree) if isinstance(n, UnaryMinus)]
    assert len(negations) == 1
    assert isinstance(negations[0].factor, DyadicByteIndirection)


def test_bare_dyadic_indirection_still_parses():
    # Guard the move from arith to factor: the unadorned forms must still work,
    # as both rvalue (read) and lvalue (assignment target).
    assert _compiles("A%=&2000\nb=A%?5\n")
    assert _compiles("A%=&2000\nA%?5=9\n")
    assert _compiles("A%=&2000\nb=A%!5\n")


def _store_target(source):
    program = analyse(source, name="t")
    assigns = [n for n in walk(program.parse_tree) if isinstance(n, Assignment)]
    return assigns[-1].lValue  # the indirection store, past the A%=&2000 setup


def test_dyadic_byte_indirection_is_an_lvalue_target():
    # Moving the rvalue form to `factor` must NOT divert the LHS of an
    # assignment away from the writable path: A%?3 = v stays a dyadic-byte
    # *store* (marked isLValue), not a parse of the rvalue read.
    target = _store_target("A%=&2000\nA%?3 = 200\n")
    assert isinstance(target, DyadicByteIndirection)
    assert target.isLValue is True


def test_dyadic_word_indirection_is_an_lvalue_target():
    target = _store_target("A%=&2000\nA%!4 = 12345\n")
    assert isinstance(target, DyadicIntegerIndirection)
    assert target.isLValue is True


def test_dyadic_indirection_with_expr_offset_is_an_lvalue_target():
    target = _store_target("A%=&2000\nA%?(1+2) = 9\n")
    assert isinstance(target, DyadicByteIndirection)
    assert target.isLValue is True
