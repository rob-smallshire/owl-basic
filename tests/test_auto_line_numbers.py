"""An un-numbered BBC BASIC program is AUTO-numbered 10, 20, 30, ... and its
GOTO/GOSUB statements target those line numbers.

The BBC ROM (and OWL's decoder.py for the tokenised/numbered path) number with
AUTO defaults start=10, step=10. analysis._synthesize_line_numbers used 1-based
numbers instead, so GOSUB110 in an un-numbered program found no line 110 and the
flow pass crashed with ValueError (list.index x not in list).
"""
from conftest import requires_dotnet_toolchain
from owl_basic.analysis import analyse


def test_unnumbered_gosub_target_resolves_without_crash():
    # Was: ValueError list.index in the flow graph (no line 20 in a 1-based map).
    analyse('GOSUB20:PRINT "after":END\nPRINT "sub":RETURN\n', name="t")


@requires_dotnet_toolchain
def test_goto_to_auto_line_number(compile_and_run):
    # line 10 jumps past line 20 to line 30.
    src = 'GOTO30:PRINT "skipped"\nEND\nPRINT "target":END\n'
    assert compile_and_run(analyse(src, name="t")).strip() == "target"
