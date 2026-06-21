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


# -- codegen: the correlated loop must lower to correct, terminating code ----

from conftest import requires_dotnet_toolchain  # noqa: E402


@requires_dotnet_toolchain
def test_constant_until_loop_lowers_and_terminates(compile_and_run):
    # One REPEAT, an UNTIL FALSE loop-back inside an IF and an UNTIL TRUE exit:
    # the counter must run to C%=5 and stop (not spin forever). This is the
    # end-to-end guard that the multi-UNTIL loop lowers correctly.
    out = compile_and_run(
        analyse(
            "C%=0\n"
            "REPEAT\n"
            "C%=C%+1\n"
            "IF C%<5 UNTIL FALSE\n"   # loop back while C%<5
            "UNTIL TRUE\n"            # then exit
            "PRINT C%\n",
            name="t",
        ),
        timeout=30,
    )
    assert out == "5\n"


@requires_dotnet_toolchain
def test_program_named_with_a_leading_digit_assembles(compile_and_run):
    # Corpus programs are named by share id (e.g. "5df6cac4d936"); a leading
    # digit is an invalid IL identifier for .assembly/.module and must be made
    # valid, or ilasm rejects the whole module.
    out = compile_and_run(analyse("PRINT 6*7\n", name="5df6cac4d936"), timeout=30)
    assert out == "42\n"
