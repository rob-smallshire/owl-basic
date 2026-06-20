"""An IF with no statement after it is the last thing the program does.

When an IF is the final statement, a branch that would fall through to "the next
statement" instead runs off the end of the program -- a terminal node, not an
error. The flow builder used to require a following statement and called
errors.internal() (a sys.exit) when there wasn't one, so `IF c THEN s` at the end
of a program crashed the compiler.
"""
from conftest import requires_dotnet_toolchain
from owl_basic.analysis import analyse


def test_if_as_last_statement_analyses():
    analyse("IF 1 PRINT 1\n", name="t")  # was: SystemExit (internal)


def test_if_else_as_last_statement_analyses():
    analyse("IF 0 ELSE PRINT 1\n", name="t")


def test_if_last_in_program_after_other_statements():
    analyse('PRINT "a"\nIF 1 PRINT "b"\n', name="t")


@requires_dotnet_toolchain
def test_if_true_branch_at_end_runs(compile_and_run):
    assert compile_and_run(analyse('IF 1 PRINT "yes"\n', name="t")).strip() == "yes"


@requires_dotnet_toolchain
def test_if_false_branch_at_end_falls_off_the_end(compile_and_run):
    # Condition false: the body is skipped and the program ends cleanly.
    assert compile_and_run(analyse('PRINT "before"\nIF 0 PRINT "skip"\n',
                                   name="t")).splitlines() == ["before"]
