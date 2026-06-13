"""Leaving a loop early through a procedure/program terminal. The loop
correlation pass treated any terminal statement reached with loops still open
as an error, but ENDPROC / END / =<expr> / STOP inside a loop are legitimate
early exits (ragged-num's PROCtokenise does IF ... THEN ENDPROC inside its
REPEAT). One focused test per construct.
"""
from conftest import requires_dotnet_toolchain

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
