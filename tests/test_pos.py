"""POS reports the text cursor column. It must track all output, not just
PRINT: ragged-num emits its words with VDU and then uses IF POS <> 0 : PRINT to
end each line, so POS has to follow VDU output too.
"""
from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse


@requires_dotnet_toolchain
def test_pos_tracks_vdu_output(compile_and_run):
    # VDU 65,66,67 prints ABC and leaves the cursor at column 3.
    out = compile_and_run(analyse("VDU 65,66,67\nPRINT POS\nEND\n", name="pos_vdu"))
    assert out.splitlines() == ["ABC3"]


@requires_dotnet_toolchain
def test_pos_resets_after_newline(compile_and_run):
    # A newline returns the cursor to column 0.
    out = compile_and_run(analyse("VDU 65,66\nPRINT\nPRINT POS\nEND\n", name="pos_nl"))
    assert out.splitlines() == ["AB", "0"]
