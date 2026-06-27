"""COUNT -- the number of characters PRINTed since the last newline.

COUNT is the print manager's running character count (reset on a CR), used for
column/word wrapping: IF COUNT>w THEN PRINT' ... It is distinct from POS (the VDU
cursor column over all output paths). It lowers to a BasicCommands.Count() call.
Surfaced by The Micro User RESULTS and WizLoad (e.g. IF COUNT+LEN w$>37 PRINT').
"""
from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse


def test_count_compiles_to_a_runtime_call(dotnet_backend):
    il = dotnet_backend.emit_il(analyse("PRINT COUNT\nEND\n", name="t"))
    assert "BasicCommands::Count" in il


@requires_dotnet_toolchain
def test_count_tracks_characters_since_newline(compile_and_run):
    # After printing "abcde" (no newline), COUNT is 5. Capture it before the next
    # newline, then print it on its own line.
    out = compile_and_run(analyse(
        'PRINT "abcde";\nA=COUNT\nPRINT\nPRINT A\n', name="t"))
    assert out.splitlines()[1] == "5"


@requires_dotnet_toolchain
def test_count_resets_to_zero_after_newline(compile_and_run):
    out = compile_and_run(analyse(
        'PRINT "hello"\nPRINT COUNT\n', name="t"))
    # "hello" ended with a newline, so COUNT is 0 at the start of the next line.
    assert out.splitlines()[1] == "0"
