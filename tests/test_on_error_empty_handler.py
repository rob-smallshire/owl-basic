"""ON ERROR with an empty handler -- "on error, resume at the next statement".

`ON ERROR:` (nothing after it on the line) installs an empty handler: on an
error, BBC jumps to the ON ERROR, runs the empty handler, and falls through to
the following line. So the handler's landing point is the statement after the
ON ERROR. The emitter only handled handlers with a first statement, so the empty
form failed with "ON ERROR handler ... cannot be lowered". Surfaced by The Micro
User tmu90-07/08.ULTIMA (ON ERROR: followed by MODE7 cleanup).
"""
from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse_numbered_lines


def _analyse(lines):
    return analyse_numbered_lines(lines, name="t", source_filepath="t")


def test_empty_on_error_handler_compiles(dotnet_backend):
    program = _analyse([(10, " ON ERROR:"), (20, ' PRINT "ok"'), (30, " END")])
    assert dotnet_backend.emit_il(program)


@requires_dotnet_toolchain
def test_empty_on_error_resumes_at_following_statement(compile_and_run):
    # On the division error at line 40, control resumes at line 30 (the statement
    # after ON ERROR). N guards against an infinite loop: the second pass ends.
    out = compile_and_run(_analyse([
        (10, " N=0"),
        (20, " ON ERROR:"),
        (30, ' N=N+1:IF N=2 THEN PRINT "recovered":END'),
        (40, " X%=1 DIV 0"),    # integer DIV by zero raises (float /0 is Infinity)
    ]))
    assert out.strip() == "recovered"
