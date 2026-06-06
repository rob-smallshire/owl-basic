"""Strict vs lenient handling of unparseable lines (red-green-refactor).

A real BBC BASIC program can contain lines the interpreter merely stores and
only errors on at RUN time (often dead branches). By default the compiler treats
an unparseable line as a compile error (the grown-up-compiler norm); a lenient
option recovers per line so the rest of the program still compiles.
"""

import pytest

from owl_basic.analysis import analyse_numbered_lines
from owl_basic.exceptions import CompileError

_GOOD = (10, "A=1")
_BAD = (20, "X=(")  # unmatched parenthesis: a genuine syntax error
_END = (30, "END")


def test_strict_is_the_default_and_rejects_unparseable_lines():
    with pytest.raises(CompileError):
        analyse_numbered_lines([_GOOD, _BAD, _END], name="t")


def test_lenient_compiles_around_an_unparseable_line():
    program = analyse_numbered_lines([_GOOD, _BAD, _END], name="t", strict=False)
    assert "__owl__main" in program.entry_points
    assert program.ordered_basic_blocks


def test_a_fully_valid_program_is_unaffected_by_strict():
    program = analyse_numbered_lines([_GOOD, _END], name="t")  # strict default
    assert "__owl__main" in program.entry_points
