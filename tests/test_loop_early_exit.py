"""Leaving a loop early through a procedure/program terminal. The loop
correlation pass treated any terminal statement reached with loops still open
as an error, but ENDPROC / END / =<expr> / STOP inside a loop are legitimate
early exits (ragged-num's PROCtokenise does IF ... THEN ENDPROC inside its
REPEAT). One focused test per construct.

A procedure exit (ENDPROC / =<expr>) reached with a FOR or REPEAT still open
leaks that loop's frame in the BBC interpreter -- legal but poor form -- so the
correlation pass emits a strong warning naming the open loops. A program exit
(END / STOP) returns to the prompt, which resets the loop stacks, so it stays
silent.
"""
import logging

from conftest import requires_dotnet_toolchain

from owl_basic import errors
from owl_basic.analysis import analyse


@requires_dotnet_toolchain
def test_endproc_inside_a_repeat_loop(compile_and_run):
    # PROCf loops until N% reaches 3, then ENDPROCs out of the REPEAT.
    out = compile_and_run(analyse(
        'PROCf\nPRINT "back ";N%\nEND\n'
        'DEF PROCf\nREPEAT\nN% = N% + 1\nIF N% = 3 THEN ENDPROC\nUNTIL FALSE\nENDPROC\n',
        name="early_endproc"))
    assert out.splitlines() == ["back 3"]


@requires_dotnet_toolchain
def test_end_inside_a_loop(compile_and_run):
    # END inside a loop terminates the program from within the loop.
    out = compile_and_run(analyse(
        'N% = 0\nREPEAT\nN% = N% + 1\nPRINT N%\nIF N% = 2 THEN END\nUNTIL FALSE\n',
        name="early_end"))
    assert out.splitlines() == ["1", "2"]


def test_endproc_inside_repeat_warns_naming_the_loop(caplog):
    # ENDPROC out of an open REPEAT leaks the loop frame in the interpreter:
    # the warning must name ENDPROC and the REPEAT it abandons.
    errors.error_log.clear()
    with caplog.at_level(logging.WARNING):
        analyse(
            'PROCf\nEND\n'
            'DEF PROCf\nREPEAT\nIF TRUE THEN ENDPROC\nUNTIL FALSE\nENDPROC\n',
            name="warn_endproc_repeat")
    messages = [r.getMessage() for r in caplog.records]
    assert any("ENDPROC" in m and "REPEAT loop" in m for m in messages), messages


def test_endproc_inside_for_names_the_index(caplog):
    # The warning names the FOR control variable so the offending loop is
    # identifiable in a procedure that opens several.
    errors.error_log.clear()
    with caplog.at_level(logging.WARNING):
        analyse(
            'PROCf\nEND\n'
            'DEF PROCf\nFOR I% = 1 TO 10\nIF I% = 3 THEN ENDPROC\nNEXT\nENDPROC\n',
            name="warn_endproc_for")
    messages = [r.getMessage() for r in caplog.records]
    assert any("ENDPROC" in m and "FOR I% loop" in m for m in messages), messages


def test_end_inside_loop_emits_no_leak_warning(caplog):
    # END returns to the prompt, which resets the loop stacks: no leak, so no
    # warning about an unceremonious exit.
    errors.error_log.clear()
    with caplog.at_level(logging.WARNING):
        analyse(
            'REPEAT\nIF TRUE THEN END\nUNTIL FALSE\n',
            name="warn_end_silent")
    messages = [r.getMessage() for r in caplog.records]
    assert not any("reclaimed only by its own" in m for m in messages), messages
