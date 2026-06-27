"""The DIM block target (DIM P% n) is an l-value, not a read.

`DIM S% &A0` sets S% to the base address of a reserved block, so S% is a write
target. The grammar did not mark it as an l-value, so when a constant had been
assigned to the same name earlier (S%=&D00 : ... : DIM S% &A0) constant
propagation treated the DIM target as a read and substituted the literal --
turning the target into a LiteralInteger and crashing the symbol-table pass
(AssertionError: ... is not a variable). Marking it an l-value both stops the
substitution and disqualifies the name from being a uniform constant (it is
assigned twice). Surfaced by The Micro User AZZOD.
"""
from owl_basic.analysis import analyse


def test_dim_block_target_after_constant_assignment_compiles(dotnet_backend):
    il = dotnet_backend.emit_il(analyse(
        "S%=&D00\nDIM S% &A0\n?S%=65\nEND\n", name="t"))
    assert il


def test_dim_block_target_analyses_cleanly():
    program = analyse("S%=&D00\nDIM S% &A0\n?S%=65\nEND\n", name="t")
    assert (getattr(program, "diagnostics", None) or []) == []
