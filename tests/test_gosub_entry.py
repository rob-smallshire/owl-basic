"""GOSUB as the program's first statement.

GOSUB is lowered by converting each GOSUB'd line into a PROC and each GOSUB
into a CALL (ConvertSubVisitor.visitGosub does replaceStatement(gosub, call)).
That rewrites the AST and CFG, but the entry_points map still pointed at the
now-disconnected Gosub when the replaced GOSUB was itself the program entry
(__owl__main -- i.e. the first statement is a GOSUB). Block identification then
started from the dead node, so the main method came out as a lone, un-lowerable
Gosub and codegen failed with "Cannot lower statement node 'Gosub'".

A GOSUB anywhere but the first statement already worked; this covers the entry
case (and matters for the GOSUB-prologue idiom, e.g. `10 GOSUB 100 : ...`).
"""
from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse_numbered_lines

_ENTRY_GOSUB = [
    (10, " GOSUB 100"),
    (20, ' PRINT "done"'),
    (30, " END"),
    (100, ' PRINT "sub"'),
    (110, " RETURN"),
]


def _first_statement_kind(program, entry):
    block = program.ordered_basic_blocks[entry][0]
    return type(block.statements[0]).__name__


def test_entry_gosub_is_converted_to_a_call():
    # The main entry block must begin with the converted CALL, not the raw
    # Gosub left behind by a stale entry-point reference.
    program = analyse_numbered_lines(_ENTRY_GOSUB, name="eg")
    assert _first_statement_kind(program, "__owl__main") == "CallProcedure"


def test_entry_gosub_main_block_keeps_the_following_statements():
    # Regression for the truncation symptom: main was just [Gosub], dropping
    # PRINT "done" / END because the walk began from the disconnected node.
    program = analyse_numbered_lines(_ENTRY_GOSUB, name="eg")
    kinds = [type(s).__name__
             for b in program.ordered_basic_blocks["__owl__main"]
             for s in b.statements]
    assert kinds == ["CallProcedure", "Print", "End"]


@requires_dotnet_toolchain
def test_entry_gosub_compiles_and_runs(compile_and_run):
    out = compile_and_run(analyse_numbered_lines(_ENTRY_GOSUB, name="eg"))
    assert out.splitlines() == ["sub", "done"]
