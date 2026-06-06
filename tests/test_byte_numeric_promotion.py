"""Numeric operator typing must promote BYTE operands.

A byte value (e.g. from ``?addr`` indirection) acts as an integer in BBC BASIC
arithmetic, so operator typing follows the promotion lattice
``byte < integer < float``. The type checker previously had no byte rule (a
standing ``TODO: Handle byte types``), so e.g. ``byte * integer`` was left
untyped; any enclosing operator then failed with "has no type information".
That was the Sphinx line-368 blocker ("Cannot apply * to Byte and Integer").

One focused test per culprit combination.
"""

from owl_basic.analysis import analyse
from owl_basic.owltyping.type_system import (
    ByteOwlType,
    FloatOwlType,
    IntegerOwlType,
)
from owl_basic.owltyping.typecheck_visitor import TypecheckVisitor
from owl_basic.syntax.ast import Minus, Multiply, Plus


def _operand(owl_type):
    from owl_basic.syntax.ast import LiteralInteger

    node = LiteralInteger(value=0)
    node.actualType = owl_type
    return node


def _result_type(operator_class, lhs_type, rhs_type):
    operator = operator_class()
    operator.lhs = _operand(lhs_type)
    operator.rhs = _operand(rhs_type)
    TypecheckVisitor({}).determineNumericResultType(operator)
    return operator.actualType


def test_byte_times_integer_is_integer():
    assert _result_type(Multiply, ByteOwlType(), IntegerOwlType()) is IntegerOwlType()


def test_integer_times_byte_is_integer():
    assert _result_type(Multiply, IntegerOwlType(), ByteOwlType()) is IntegerOwlType()


def test_byte_plus_integer_is_integer():
    assert _result_type(Plus, ByteOwlType(), IntegerOwlType()) is IntegerOwlType()


def test_byte_minus_byte_is_integer():
    # Byte arithmetic widens to integer (?a - ?b can be negative / exceed a byte).
    assert _result_type(Minus, ByteOwlType(), ByteOwlType()) is IntegerOwlType()


def test_byte_times_float_is_float():
    assert _result_type(Multiply, ByteOwlType(), FloatOwlType()) is FloatOwlType()


def test_float_times_byte_is_float():
    assert _result_type(Multiply, FloatOwlType(), ByteOwlType()) is FloatOwlType()


def test_byte_arithmetic_program_analyses_without_fatal():
    # A%?0 is a (dyadic) byte indirection; mixing it with integers under an
    # enclosing + must type, not abort. This is the shape of Sphinx line 368.
    analyse("A%=100\nB%=A%?0*2+1\n", "t")
