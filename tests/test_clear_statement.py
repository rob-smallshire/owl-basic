"""CLEAR: discard all variables (a no-argument statement, like CLS/CLG).

``p_clear_stmt`` built a ``Clear()`` node, but no ``Clear`` class existed in the
AST, so ``from .ast import *`` left the name undefined and every CLEAR crashed
the parser with ``NameError: name 'Clear' is not defined``. Surfaced across ~22
Acorn User type-ins (e.g. Tau85-b/NOV85.P2).
"""
from helpers import parse, walk

from owl_basic.analysis import analyse
from owl_basic.syntax.ast import Clear


def test_clear_parses_to_clear_node():
    tree = parse("CLEAR\n")
    clears = [n for n in walk(tree) if isinstance(n, Clear)]
    assert len(clears) == 1


def test_clear_in_a_program_analyses():
    # CLEAR amongst other statements must get through the full front end
    # (parse, symbol table, CFG) without crashing.
    program = analyse('X = 1\nCLEAR\nPRINT "ok"\nEND\n', name="clr")
    assert program is not None
