"""A line number need not be followed by a space.

BBC BASIC accepts `10PRINT"hi"` (no space after the line number) just as it does
`10 PRINT "hi"`. The CLI's line-numbered dispatch split each line on its first
space, so a space-less line fed the whole line to int() and crashed with a
ValueError. The number is the leading run of digits, however it is followed.
"""
from owl_basic.cli import _analyse_source


def _write(tmp_path, text):
    path = tmp_path / "prog.bas"
    path.write_text(text, encoding="latin-1")
    return path


def test_numbered_lines_without_spaces_analyse(tmp_path):
    # Was: ValueError invalid literal for int() with base 10: '10PRINT...'.
    source = _write(tmp_path, '10PRINT"hi"\n20END\n')
    _analyse_source(source, "latin-1")


def test_numbered_lines_with_spaces_still_analyse(tmp_path):
    source = _write(tmp_path, '10 PRINT "hi"\n20 END\n')
    _analyse_source(source, "latin-1")


def test_goto_targets_a_space_less_numbered_line(tmp_path):
    # GOTO must still resolve against the space-less line numbers.
    source = _write(tmp_path, '10GOTO30\n20PRINT"skip"\n30PRINT"target":END\n')
    _analyse_source(source, "latin-1")
