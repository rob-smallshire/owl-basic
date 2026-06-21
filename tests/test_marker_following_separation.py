"""A separable statement directly after a marker (REPEAT/DEF...) compiles.

When a statement that the separation pass splits -- READ, DIM, multi-variable
NEXT -- directly follows a marker without a colon (e.g. `REPEAT READ X`), it is
the marker's `followingStatement`, not a list element. Separation replaced it
with a StatementList there; the marker-normalisation in simplification then
moved that StatementList into the parent list *after* the flattening pass, so it
reached the flow graph un-flattened and crashed (TypeError, then AttributeError
'StatementList' has no clearInEdges). Now the StatementList is spliced in
statement by statement.
"""
from owl_basic.analysis import analyse
from conftest import requires_dotnet_toolchain


def _compiles(source):
    return not analyse(source, name="t").diagnostics


def test_read_directly_after_repeat_compiles():
    assert _compiles("REPEAT READ X:VDU RND(X);:UNTIL 0\nDATA 1,2,3\n")


def test_multi_variable_read_after_repeat_compiles():
    assert _compiles("REPEAT READ A,B:PRINT A,B:UNTIL 0\nDATA 1,2,3,4\n")


def test_dim_directly_after_repeat_compiles():
    assert _compiles("REPEAT DIM A(3):UNTIL 0\n")


def test_read_in_a_for_body_still_compiles():
    # The list-element path (READ separated by a colon, in a list) must still work.
    assert _compiles("FOR I=1 TO 2:READ X:NEXT\nDATA 1,2\n")


@requires_dotnet_toolchain
def test_read_after_marker_runs_correctly(compile_and_run):
    # Terminating form: read three values via a FOR/READ and print them.
    out = compile_and_run(
        analyse("FOR I=1 TO 3:READ X:PRINT X:NEXT\nDATA 7,8,9\n", name="t"),
        timeout=30,
    )
    assert out == "7\n8\n9\n"
