"""An IF condition may be a full additive expression, even without THEN.

`IF C-O ...` means the condition is `C-O`. The implicit-GOTO clause (BBC's
`IF cond THEN <line>`) was written to accept any factor, so after `IF C` the
parser could read `-O` as a bare unary-minus statement (an implicit GOTO to a
computed line) instead of continuing the condition. Restricting an implicit GOTO
to a literal line number -- which is all BBC BASIC allows there -- makes
`IF C-O`/`IF C+O` parse their conditions correctly, while `IF X THEN 100` still
jumps.
"""
from helpers import walk
from owl_basic.syntax import parser
from owl_basic.syntax.ast import Goto, Minus, Plus


class _Options:
    debug_lex = False
    verbose = False
    use_clr = False


def _parse(source):
    return parser.parse(source if source.endswith("\n") else source + "\n", _Options())


def _conditions(tree):
    return [n.condition for n in walk(tree) if type(n).__name__ == "If"]


def test_if_minus_condition_without_then():
    cond = _conditions(_parse("IF C-O:O=C\n"))[0]
    assert isinstance(cond, Minus)
    assert not any(isinstance(n, Goto) for n in walk(_parse("IF C-O:O=C\n")))


def test_if_plus_condition_without_then():
    cond = _conditions(_parse("IF C+O:O=C\n"))[0]
    assert isinstance(cond, Plus)


def test_if_then_literal_line_is_still_an_implicit_goto():
    tree = _parse("IF X THEN 100\n")
    gotos = [n for n in walk(tree) if isinstance(n, Goto)]
    assert len(gotos) == 1
    assert gotos[0].targetLogicalLine.value == 100
