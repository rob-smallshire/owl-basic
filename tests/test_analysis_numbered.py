"""Analysis of line-numbered BBC BASIC source (red-green-refactor).

Real BBC BASIC programs (e.g. detokenised Sphinx) carry explicit line numbers,
and GOTO/GOSUB reference them. analyse() synthesizes sequential numbers for
un-numbered source; analyse_numbered_lines() must instead use the real numbers
so jump targets resolve.
"""

from owl_basic.analysis import analyse_numbered_lines
from owl_basic.codegen.backend import Program


def test_uses_the_real_line_numbers():
    lines = [(10, "A=1"), (20, "GOTO 40"), (30, "A=2"), (40, "END")]
    program = analyse_numbered_lines(lines, name="jump")
    assert isinstance(program, Program)
    assert program.line_mapper.physical_to_logical_map[:4] == [10, 20, 30, 40]


def test_goto_to_a_real_line_number_resolves():
    # With synthesized 1..N numbers, GOTO 40 would not resolve (no logical line
    # 40); with the real numbers the program must analyse cleanly.
    lines = [(10, "A=1"), (20, "GOTO 40"), (30, "A=2"), (40, "END")]
    program = analyse_numbered_lines(lines, name="jump")
    assert "__owl__main" in program.entry_points
    assert program.ordered_basic_blocks
