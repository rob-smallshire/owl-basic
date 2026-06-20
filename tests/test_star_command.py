"""A ``*FX``/``*CAT`` star command passes the rest of its line to the OS, so it
consumes to end-of-line and is always the *final* statement on a line. BBC BASIC
lets it follow other statements, with or without a separating colon -- the
no-colon form (``REPEAT*FX19``) is a common byte-saver in tweet-sized programs.
"""
from helpers import parse
from owl_basic.syntax.ast import StarCommand


def _statements(source):
    return [s for s in parse(source).statements.statements if s is not None]


def test_star_command_alone():
    stmts = _statements("*FX19\n")
    assert len(stmts) == 1 and isinstance(stmts[0], StarCommand)


def test_star_command_after_statement_without_colon():
    # REPEAT*FX19 -- no colon before the star (the byte-saving form).
    stmts = _statements("REPEAT*FX19\n")
    assert [type(s).__name__ for s in stmts] == ["Repeat", "StarCommand"]


def test_star_command_after_statement_with_colon():
    stmts = _statements("A=1:*FX19\n")
    assert len(stmts) == 2 and isinstance(stmts[-1], StarCommand)


def test_star_command_is_always_the_final_statement():
    stmts = _statements('PRINT"hi":*CAT\n')
    assert isinstance(stmts[-1], StarCommand)


def test_any_star_command_not_just_fx_and_cat():
    # *HELP (and any other *command) is a star command, not only *FX / *CAT.
    stmts = _statements("*HELP\n")
    assert len(stmts) == 1 and isinstance(stmts[0], StarCommand)
    assert "HELP" in stmts[0].command


def test_multiplication_is_not_a_star_command():
    from owl_basic.syntax.ast import Multiply
    from helpers import walk
    tree = parse("A=B*C\n")
    assert not any(isinstance(n, StarCommand) for n in walk(tree))
    assert any(isinstance(n, Multiply) for n in walk(tree))


def test_times_assign_still_parses():
    # A*=2 is multiply-assign, not a star command.
    stmts = _statements("A*=2\n")
    assert not any(isinstance(s, StarCommand) for s in stmts)


def test_star_help_analyses_cleanly():
    from owl_basic.analysis import analyse
    analyse("*HELP\n", name="t")
