"""A REPEAT closed by several constant UNTILs correlates and compiles.

BBC BASIC's REPEAT...UNTIL is not one-to-one: one REPEAT can be closed by many
UNTILs, and `UNTIL FALSE` always loops back (it never exits). The IFS-fractal
idiom from the corpus relies on this -- an inner REPEAT whose body has several
`IF cond ...:UNTIL FALSE` loop-back tests and a final `UNTIL TRUE` exit:

    REPEAT
      ...
      IF c1 ...: UNTIL FALSE   ' loop back when c1
      IF c2 ...: UNTIL FALSE   ' loop back when c2
      UNTIL TRUE               ' otherwise exit

Every UNTIL maps unambiguously to that one REPEAT, so the program is statically
compilable. OWL used to reject it falsely ("UNTIL has no REPEAT to close"): its
correlation propagated a 'loop already closed' stack down the runtime-dead
fall-through edge of an `UNTIL FALSE`. Pruning that dead edge fixes it.
"""
from owl_basic.analysis import analyse
from owl_basic.syntax.ast import Until


def _analyses(source):
    return analyse(source, name="t")


def test_repeat_with_until_false_loop_back_and_until_true_exit():
    # The minimal shape of the fractal inner loop: a conditional UNTIL FALSE
    # (loops back) and an UNTIL TRUE (exits). Must not be a false rejection.
    program = _analyses(
        "REPEAT\n"
        "IF A% UNTIL FALSE\n"   # loop back when A%
        "UNTIL TRUE\n"          # otherwise exit
        "PRINT 1\n"
    )
    assert program is not None
    assert not program.diagnostics


def test_nested_repeats_with_constant_untils_compiles():
    # Two REPEATs, the inner closed by several UNTIL FALSE loop-backs and an
    # UNTIL TRUE exit, the outer by an UNTIL FALSE -- the corpus IFS shape.
    program = _analyses(
        "REPEAT\n"
        "REPEAT\n"
        "IF B%<1 UNTIL FALSE\n"
        "IF B%<2 UNTIL FALSE\n"
        "UNTIL TRUE\n"
        "UNTIL FALSE\n"
    )
    assert program is not None
    assert not program.diagnostics


def test_until_zero_is_treated_as_until_false():
    # The corpus writes `U.0` / `U.1` (literal 0/1), not the keywords.
    program = _analyses(
        "REPEAT\n"
        "IF A% UNTIL 0\n"
        "UNTIL 1\n"
    )
    assert program is not None
    assert not program.diagnostics


def test_genuine_unmatched_until_is_still_rejected():
    # An UNTIL with no REPEAT at all must still be a graceful rejection.
    from owl_basic.exceptions import CompileError
    import pytest
    with pytest.raises(CompileError):
        _analyses("PRINT 1\nUNTIL FALSE\nPRINT 2\n")
