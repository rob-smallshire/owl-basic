"""A loop left open at the end of a routine is a benign leaked frame, not an error.

A conditional closing statement -- `IF cond NEXT`, `IF cond UNTIL ...` -- is
compilable as long as it correlates with one opener: the closing statement is the
loop's back-edge, and the path that does not take it simply exits the loop early.
In BBC BASIC that early exit leaks the loop's stack frame until control returns to
the prompt; OWL's compiled code has no such frame. So OWL warns (as it already
does for an ENDPROC/= exiting a loop) rather than rejecting "loop still open".
"""
from owl_basic.analysis import analyse
from conftest import requires_dotnet_toolchain


def _compiles(source):
    return not analyse(source, name="t").diagnostics


def test_conditional_next_early_exit_compiles():
    assert _compiles("FOR I=1 TO 9\nPRINT I\nIF I<3 NEXT\n")


def test_for_with_no_next_compiles():
    # A FOR never closed by a NEXT: in BBC BASIC the body runs once and the
    # frame leaks. It must not be rejected.
    assert _compiles("FOR I=1 TO 5\nPRINT I\n")


def test_repeat_with_early_goto_exit_compiles():
    assert _compiles("REPEAT\nPRINT 1\nIF TRUE GOTO 40\nUNTIL FALSE\nPRINT 2\n")


@requires_dotnet_toolchain
def test_conditional_next_early_exit_runs_correctly(compile_and_run):
    # `IF I<3 NEXT` loops back only while I<3, so it prints 1, 2, 3 and exits.
    out = compile_and_run(
        analyse("FOR I=1 TO 9\nPRINT I\nIF I<3 NEXT\n", name="t"), timeout=30
    )
    assert out == "1\n2\n3\n"
