"""Integration guard for the ragged-num corpus program (optimal line breaking
by dynamic programming). It exercises byte-block DIM, ?addr indirection as an
r-value, integer arrays, READ/DATA/RESTORE, @% formatting, POS, VDU, CLS,
multi-statement IF and ENDPROC-inside-a-loop -- so that the whole program
assembles end to end.
"""
from helpers import analyse_fixture


def test_ragged_num_compiles(dotnet_backend):
    il = dotnet_backend.emit_il(analyse_fixture("ragged-num.bbctxt"))
    assert ".entrypoint" in il
