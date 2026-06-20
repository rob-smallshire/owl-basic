"""BBC BASIC allows a computed GOTO/GOSUB target -- the line number may be any
numeric expression (GOTO E%+1). OWL parses it; whether it can be *compiled*
depends on the target folding to a constant, which is a later, compile-time
concern (a non-constant target is rejected further down the pipeline).
"""
from helpers import parse, walk
from owl_basic.syntax.ast import Gosub, Goto


def test_computed_goto_parses():
    assert any(isinstance(n, Goto) for n in walk(parse("GOTO E%+1\n")))


def test_computed_gosub_parses():
    assert any(isinstance(n, Gosub) for n in walk(parse("GOSUB N*100\n")))


def test_plain_line_number_goto_still_parses():
    assert any(isinstance(n, Goto) for n in walk(parse("GOTO 100\n")))
