"""ON <expr> PROC..., the computed procedure call.

BBC BASIC's ``ON n PROCa,PROCb,...`` calls the n-th procedure (1-based), the
PROC sibling of ``ON n GOSUB``. An optional ``ELSE`` gives the out-of-range
action: ``ELSE <statements>`` runs them, a bare ``ELSE`` makes out-of-range a
no-op, and no ELSE at all raises the ON-range error. Surfaced by Acorn User
Tau89-b/JUL89.Galaxy: ``ON phase% PROCsetup,PROCsimulation ELSE``.
"""
from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse_numbered_lines


def _analyse(lines):
    return analyse_numbered_lines(lines, name="t", source_filepath="t")


_PROCS = [(100, " DEFPROCa"), (110, ' PRINT "a"'), (120, " ENDPROC"),
          (130, " DEFPROCb"), (140, ' PRINT "b"'), (150, " ENDPROC")]


def test_on_proc_with_empty_else_parses():
    # The Galaxy shape: a bare trailing ELSE (out-of-range no-op).
    program = _analyse([(10, " phase%=1"),
                        (20, " ON phase% PROCsetup,PROCsimulation ELSE"), (30, " END"),
                        (100, " DEFPROCsetup"), (110, " ENDPROC"),
                        (130, " DEFPROCsimulation"), (140, " ENDPROC")])
    assert program is not None


@requires_dotnet_toolchain
def test_on_proc_calls_the_nth_procedure(compile_and_run):
    out = compile_and_run(_analyse(
        [(10, " FOR I%=1 TO 2"), (20, " ON I% PROCa,PROCb"), (30, " NEXT"),
         (40, " END")] + _PROCS))
    assert out.split() == ["a", "b"]


@requires_dotnet_toolchain
def test_on_proc_out_of_range_bare_else_is_noop(compile_and_run):
    out = compile_and_run(_analyse(
        [(10, " X%=5"), (20, " ON X% PROCa,PROCb ELSE"), (30, ' PRINT "after"'),
         (40, " END")] + _PROCS))
    assert out.split() == ["after"]


@requires_dotnet_toolchain
def test_on_proc_out_of_range_else_clause_runs(compile_and_run):
    out = compile_and_run(_analyse(
        [(10, " X%=9"), (20, ' ON X% PROCa,PROCb ELSE PRINT "none"'), (30, " END")]
        + _PROCS))
    assert out.split() == ["none"]


@requires_dotnet_toolchain
def test_on_proc_passes_arguments(compile_and_run):
    out = compile_and_run(_analyse(
        [(10, " ON 2 PROCshow(11),PROCshow(22)"), (20, " END"),
         (100, " DEFPROCshow(n%)"), (110, " PRINT n%"), (120, " ENDPROC")]))
    assert out.split() == ["22"]
