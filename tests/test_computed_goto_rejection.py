"""A GOTO/GOSUB/ON GOTO target must be a constant line number.

OWL's grammar accepts a general expression after GOTO/GOSUB (some BASICs allow a
computed jump), but a static compiler resolves jump targets at compile time, so a
non-constant target -- GOTO X, GOSUB -X -- cannot be compiled. It used to crash
the flow builder (`'Variable' object has no attribute 'value'`); it must instead
be rejected gracefully, naming the constant-line-number requirement.
"""
import pytest

from owl_basic.analysis import analyse
from owl_basic.exceptions import CompileError


def test_computed_goto_to_a_variable_is_rejected():
    with pytest.raises(CompileError) as excinfo:
        analyse("X=2\nGOTOX\n", name="t")
    assert "constant" in str(excinfo.value).lower()


def test_computed_goto_to_an_expression_is_rejected():
    with pytest.raises(CompileError):
        analyse("X=10\nGOTO-X\n", name="t")


def test_computed_gosub_is_rejected():
    with pytest.raises(CompileError):
        analyse("X=2\nGOSUB-X\n", name="t")


def test_constant_goto_still_works():
    # A literal line-number target compiles fine.
    analyse('GOTO20:PRINT "skipped"\nPRINT "target":END\n', name="t")
