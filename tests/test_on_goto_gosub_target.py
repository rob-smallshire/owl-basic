"""ON x GOTO targets a line whose first statement is a GOSUB.

The dispatcher idiom -- ON Z GOTO 510,520,... where each target line is
"GOSUBnnnn:GOTO600" -- has the ON GOTO point at GOSUB statements. GOSUB-to-PROC
conversion replaces each GOSUB with a CALL, but OnGoto.targetStatements still
held the now-disconnected GOSUB nodes (block=None), so codegen crashed with
KeyError when building the switch table. The target references are now retargeted
to the replacement calls. Surfaced by The Micro User tmu85-02.PILOT.
"""
from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse_numbered_lines


def _analyse(lines):
    return analyse_numbered_lines(lines, name="t", source_filepath="t")


_DISPATCH = [
    (10, " Z=1"),
    (20, " ON Z GOTO 40,50"),
    (30, " END"),
    (40, ' GOSUB 100:GOTO 30'),
    (50, ' GOSUB 200:GOTO 30'),
    (100, ' PRINT "a":RETURN'),
    (200, ' PRINT "b":RETURN'),
]


def test_on_goto_to_gosub_target_compiles(dotnet_backend):
    assert dotnet_backend.emit_il(_analyse(_DISPATCH))


@requires_dotnet_toolchain
def test_on_goto_to_gosub_target_runs(compile_and_run):
    # Z=1 selects line 40 -> GOSUB 100 prints "a" -> GOTO 30 ends.
    assert compile_and_run(_analyse(_DISPATCH)).strip() == "a"


@requires_dotnet_toolchain
def test_on_goto_to_gosub_target_second_branch(compile_and_run):
    lines = [(10, " Z=2")] + _DISPATCH[1:]
    assert compile_and_run(_analyse(lines)).strip() == "b"
