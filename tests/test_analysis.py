"""The front-end analysis pipeline, end to end on Python 3.

Exercises parse -> flow analysis -> type check -> symbol tables, producing a
backend-ready Program. This is the stage beyond parsing that Phase 1's parse
corpus did not cover.
"""

import os

import pytest

from owl_basic.analysis import analyse
from owl_basic.codegen.backend import Program

HERE = os.path.dirname(os.path.abspath(__file__))


def _read(name):
    with open(os.path.join(HERE, name), encoding="latin-1") as f:
        return f.read()


def test_analyse_six_times_seven_produces_program():
    program = analyse(
        _read("six_times_seven.bbctxt"),
        name="six_times_seven",
        source_filepath="six_times_seven.bbctxt",
    )
    assert isinstance(program, Program)
    assert program.name == "six_times_seven"
    assert "__owl__main" in program.entry_points
    assert program.ordered_basic_blocks  # at least one basic block
    assert program.global_symbols is not None


@pytest.mark.parametrize(
    "filename",
    ["six_times_seven.bbctxt", "end_to_end/for_loops/for_loop_01.owl"],
)
def test_analyse_runs_without_error(filename):
    program = analyse(_read(filename), name="prog")
    assert program.ordered_basic_blocks is not None
