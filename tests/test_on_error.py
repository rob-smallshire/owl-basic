"""ON ERROR parses to an OnError node (Phase 1: frontend only).

BBC BASIC installs an error handler with ``ON ERROR <statements>`` (the handler
is the rest of the line), disables it with ``ON ERROR OFF``, and -- in BASIC V
-- scopes it to a PROC/FN with ``ON ERROR LOCAL <statements>``. The frontend now
parses all three into an ``OnError`` node so these programs get past the parse;
lowering the handler to a runtime exception path is a later phase, so the dotnet
backend rejects it cleanly for now.
"""
import pytest

from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse_numbered_lines
from owl_basic.syntax.ast import LocalError, OnError, RestoreError


def _analyse(lines):
    return analyse_numbered_lines(lines, name="oe")


def _statements(program):
    # Dedupe by identity: a statement in a routine that is also the program
    # entry appears under more than one entry-point key.
    seen, out = set(), []
    for blocks in program.ordered_basic_blocks.values():
        for b in blocks:
            for s in b.statements:
                if id(s) not in seen:
                    seen.add(id(s))
                    out.append(s)
    return out


def _only_on_error(program):
    nodes = [s for s in _statements(program) if isinstance(s, OnError)]
    assert len(nodes) == 1, f"expected one OnError, got {len(nodes)}"
    return nodes[0]


def test_on_error_goto_parses():
    node = _only_on_error(_analyse([(10, " ON ERROR GOTO 500"), (20, " END"),
                                    (500, ' PRINT "oops"'), (510, " END")]))
    assert node.handler is not None and not node.off


def test_on_error_with_statement_handler_parses():
    # The handler is the whole rest of the line (PROCerr : END).
    node = _only_on_error(_analyse([(10, " ON ERROR PROCerr:END"), (20, " END"),
                                    (30, " DEFPROCerr"), (40, " ENDPROC")]))
    assert node.handler is not None


def test_on_error_off_parses():
    node = _only_on_error(_analyse([(10, " ON ERROR OFF"), (20, " END")]))
    assert node.off


def test_on_error_local_parses():
    node = _only_on_error(_analyse([
        (10, " DEFPROCx"),
        (20, ' ON ERROR LOCAL PRINT "e":ENDPROC'),
        (30, " ENDPROC")]))
    assert node.handler is not None and node.local


@pytest.mark.parametrize("handler", ["GOTO 500", "PROCerr:END", "OFF", "REPORT:END"])
def test_handler_forms_get_past_the_parse(handler):
    # The point of Phase 1: these no longer fail to parse.
    program = _analyse([(10, " ON ERROR " + handler), (20, " END"),
                        (500, " END")])
    assert any(isinstance(s, OnError) for s in _statements(program))


@requires_dotnet_toolchain
def test_on_error_goto_recovers_from_a_runtime_error(compile_and_run):
    # A real runtime error (SQR of a negative -> NegativeRootException) jumps to
    # the installed handler line, which prints and ends.
    out = compile_and_run(_analyse([
        (10, " ON ERROR GOTO 100"),
        (20, " A = SQR(-1)"),
        (30, ' PRINT "not reached"'),
        (40, " END"),
        (100, ' PRINT "recovered"'),
        (110, " END"),
    ]))
    assert out.splitlines() == ["recovered"]


@requires_dotnet_toolchain
def test_on_error_catches_a_clr_division_by_zero(compile_and_run):
    # Integer DIV by zero lowers to raw CIL div, which throws
    # System.DivideByZeroException -- not an OwlRuntime error. ON ERROR must
    # still catch it (BBC catches every runtime error), so the handler runs
    # rather than the program crashing.
    out = compile_and_run(_analyse([
        (10, " ON ERROR GOTO 100"),
        (20, " B%=0"),
        (30, " A%=100 DIV B%"),
        (40, ' PRINT "not reached"'),
        (50, " END"),
        (100, ' PRINT "caught"'),
        (110, " END"),
    ]))
    assert out.splitlines() == ["caught"]


@requires_dotnet_toolchain
def test_no_error_leaves_the_handler_unrun(compile_and_run):
    out = compile_and_run(_analyse([
        (10, " ON ERROR GOTO 100"),
        (20, ' PRINT "normal"'),
        (30, " END"),
        (100, ' PRINT "handler"'),
        (110, " END"),
    ]))
    assert out.splitlines() == ["normal"]


@requires_dotnet_toolchain
def test_statement_handler_runs_on_error(compile_and_run):
    # ON ERROR PROCerr:END -- the handler is arbitrary statements (call a PROC,
    # then END). On error the handler runs: PROCerr prints, then END stops.
    out = compile_and_run(_analyse([
        (10, " ON ERROR PROCerr:END"),
        (20, " A=SQR(-1)"),
        (30, ' PRINT "not reached"'),
        (40, " END"),
        (50, " DEFPROCerr"),
        (60, ' PRINT "caught"'),
        (70, " ENDPROC"),
    ]))
    assert out.splitlines() == ["caught"]


@requires_dotnet_toolchain
def test_statement_handler_with_several_statements_runs(compile_and_run):
    out = compile_and_run(_analyse([
        (10, " ON ERROR PRINT" + '"a"' + ":PRINT" + '"b"' + ":END"),
        (20, " A=SQR(-1)"),
        (30, " END"),
    ]))
    assert out.splitlines() == ["a", "b"]


@requires_dotnet_toolchain
def test_no_error_skips_the_statement_handler(compile_and_run):
    # Normal flow must run line 20, not fall into the handler on line 10.
    out = compile_and_run(_analyse([
        (10, " ON ERROR PROCerr:END"),
        (20, ' PRINT "normal"'),
        (30, " END"),
        (40, " DEFPROCerr"),
        (50, ' PRINT "handler"'),
        (60, " ENDPROC"),
    ]))
    assert out.splitlines() == ["normal"]


@requires_dotnet_toolchain
def test_statement_handler_ending_in_goto_recovers(compile_and_run):
    # A handler that does cleanup then GOTOs a recovery line (CLOSE#0:GOTO ...).
    out = compile_and_run(_analyse([
        (10, ' ON ERROR PRINT"cleanup":GOTO 100'),
        (20, " A=SQR(-1)"),
        (30, " END"),
        (100, ' PRINT "recovered"'),
        (110, " END"),
    ]))
    assert out.splitlines() == ["cleanup", "recovered"]


@requires_dotnet_toolchain
def test_report_and_err_in_a_handler(compile_and_run):
    # REPORT prints the error message; ERR is its number. Integer DIV by zero is
    # BBC error 18, "Division by zero". (These need no line tracking.)
    out = compile_and_run(_analyse([
        (10, ' ON ERROR REPORT:PRINT" err=";ERR:END'),
        (20, " A=1 DIV 0"),
        (30, " END"),
    ]))
    assert out.splitlines() == ["Division by zero err=18"]


@requires_dotnet_toolchain
def test_report_str_returns_the_message(compile_and_run):
    out = compile_and_run(_analyse([
        (10, " ON ERROR PRINT REPORT$:END"),
        (20, " A=1 DIV 0"),
        (30, " END"),
    ]))
    assert out.splitlines() == ["Division by zero"]


@requires_dotnet_toolchain
def test_on_error_local_is_scoped_to_the_proc(compile_and_run):
    # ON ERROR LOCAL installs a handler scoped to the enclosing PROC. The error
    # in PROCtest is caught by its local handler (which ENDPROCs); control
    # returns to the caller. This works because the error dispatch is emitted
    # per method, so an ON ERROR in a PROC is naturally PROC-scoped.
    out = compile_and_run(_analyse([
        (10, " PROCtest"),
        (20, ' PRINT "after proc"'),
        (30, " END"),
        (40, " DEFPROCtest"),
        (50, ' ON ERROR LOCAL PRINT"local handler":ENDPROC'),
        (60, " A=SQR(-1)"),
        (70, ' PRINT "not reached"'),
        (80, " ENDPROC"),
    ]))
    assert out.splitlines() == ["local handler", "after proc"]


@requires_dotnet_toolchain
def test_on_error_local_restores_the_outer_handler_on_return(compile_and_run):
    # The global handler set in Main is still in effect after PROCtest returns,
    # so the later error in Main reaches it.
    out = compile_and_run(_analyse([
        (10, " ON ERROR GOTO 200"),
        (20, " PROCtest"),
        (30, " B=SQR(-1)"),
        (40, " END"),
        (50, " DEFPROCtest"),
        (60, ' ON ERROR LOCAL PRINT"local":ENDPROC'),
        (70, " C=SQR(-1)"),
        (80, " ENDPROC"),
        (200, ' PRINT "global handler"'),
        (210, " END"),
    ]))
    assert out.splitlines() == ["local", "global handler"]


@requires_dotnet_toolchain
def test_on_error_local_handler_sees_the_procs_locals(compile_and_run):
    # The handler runs inside the PROC, so its LOCAL variables are intact.
    out = compile_and_run(_analyse([
        (10, " PROCtest"),
        (20, " END"),
        (30, " DEFPROCtest"),
        (40, " LOCAL x"),
        (50, " x=42"),
        (60, ' ON ERROR LOCAL PRINT"caught x=";x:ENDPROC'),
        (70, " D=SQR(-1)"),
        (80, " ENDPROC"),
    ]))
    assert out.splitlines() == ["caught x=42"]


def test_local_error_and_restore_error_parse():
    # The BASIC V save/restore-error-context idiom: LOCAL ERROR saves the
    # caller's handler, ON ERROR LOCAL installs a PROC-scoped one, RESTORE ERROR
    # hands the caller's back. Both directives parse to their own nodes.
    program = _analyse([
        (10, " PROCfred"),
        (20, " END"),
        (30, " DEFPROCfred"),
        (40, " LOCAL ERROR"),
        (50, ' ON ERROR LOCAL PRINT"local":RESTORE ERROR:ENDPROC'),
        (60, " RESTORE ERROR"),
        (70, " ENDPROC")])
    stmts = _statements(program)
    assert any(isinstance(s, LocalError) for s in stmts)
    assert any(isinstance(s, RestoreError) for s in stmts)


@requires_dotnet_toolchain
def test_local_error_idiom_restores_the_global_handler(compile_and_run):
    # LclEr2's structure: a global handler in Main, and PROCfred that saves the
    # context (LOCAL ERROR), installs its own (ON ERROR LOCAL), then restores on
    # the way out. OWL's per-method dispatch makes the save/restore automatic, so
    # LOCAL/RESTORE ERROR are no-ops: PROCfred's error is caught locally, and the
    # later error in Main reaches the global handler.
    out = compile_and_run(_analyse([
        (10, " ON ERROR PRINT" + '"global"' + ":END"),
        (20, " PROCfred"),
        (30, " B=SQR(-1)"),
        (40, " END"),
        (50, " DEFPROCfred"),
        (60, " LOCAL ERROR"),
        (70, ' ON ERROR LOCAL PRINT"local":RESTORE ERROR:ENDPROC'),
        (80, " A=SQR(-1)"),
        (90, " RESTORE ERROR"),
        (100, " ENDPROC")]))
    assert out.splitlines() == ["local", "global"]


@requires_dotnet_toolchain
def test_erl_is_a_stub_returning_zero(compile_and_run):
    # ERL (the error line) is not tracked yet -- it returns 0 by design (see
    # docs/on-error-erl.md). Pinned so the stub is explicit.
    out = compile_and_run(_analyse([
        (10, " ON ERROR PRINT ERL:END"),
        (20, " A=1 DIV 0"),
        (30, " END"),
    ]))
    assert out.splitlines() == ["0"]
