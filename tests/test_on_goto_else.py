"""ON <expr> GOTO ... ELSE <line> -- the out-of-range default jump.

`ON x GOTO l1,l2,... ELSE n` jumps to line n when x is out of range (x<1 or
x>count), exactly as `ELSE n` does in an IF: a bare line number after ELSE is an
implicit GOTO. The grammar accepted `ELSE <statements>` but not a bare line
number, so the common menu idiom failed to parse. Surfaced by The Micro User
LOGIC9, PiCalc and BDHcvrt (e.g. ON GET-48 GOTO 200,130,60 ELSE 50).
"""
from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse_numbered_lines


def _analyse(lines):
    return analyse_numbered_lines(lines, name="t", source_filepath="t")


def test_on_goto_else_line_number_parses():
    program = _analyse([(10, " X=2"), (20, " ON X GOTO 40,50 ELSE 60"),
                        (40, ' PRINT "a":END'), (50, ' PRINT "b":END'),
                        (60, ' PRINT "c":END')])
    assert program is not None


@requires_dotnet_toolchain
def test_on_goto_else_in_range(compile_and_run):
    out = compile_and_run(_analyse([
        (10, " X=2"), (20, " ON X GOTO 40,50 ELSE 60"),
        (40, ' PRINT "a":END'), (50, ' PRINT "b":END'), (60, ' PRINT "c":END')]))
    assert out.strip() == "b"


@requires_dotnet_toolchain
def test_on_goto_else_out_of_range_takes_else(compile_and_run):
    out = compile_and_run(_analyse([
        (10, " X=9"), (20, " ON X GOTO 40,50 ELSE 60"),
        (40, ' PRINT "a":END'), (50, ' PRINT "b":END'), (60, ' PRINT "c":END')]))
    assert out.strip() == "c"
