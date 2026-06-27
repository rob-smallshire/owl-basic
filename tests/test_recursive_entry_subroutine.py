"""A GOSUB'd subroutine whose head is also the program entry point.

When RUN starts inside a subroutine -- its head is the program's first statement
-- and the routine reaches its own head again by GOTO (a loop) and GOSUB
(recursion), main and the subroutine would otherwise share the head's blocks:
block identification walks the whole subroutine body from the main entry, so the
PROC came out bodiless ("Cannot emit a method for 'PROCSub1'"). OWL now gives the
program its own main, ``PROC PROCSubN : END``, and lets the subroutine own the
head; the outermost RETURN unwinds to that END (the BBC's "RETURN without GOSUB"
halt). Surfaced by Acorn User Tau91-b/DEC91.Recur1 and Tau93-a/APR93.Recur1 (a
recursive, GOTO-looped fractal whose whole body is line 1).
"""
from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse_numbered_lines


def _analyse(lines):
    return analyse_numbered_lines(lines, name="t", source_filepath="t")


def _kinds(program, entry):
    return [[type(s).__name__ for s in block.statements]
            for block in program.ordered_basic_blocks[entry]]


def test_entry_head_subroutine_splits_main_from_the_proc():
    # Line 10 is the entry, loops to itself (GOTO 10) and recurses (GOSUB 10).
    program = _analyse([(10, " L=L+4"), (20, " IF L=4 GOTO 10"),
                        (30, " GOSUB 10"), (40, " IF L>4 RETURN")])
    # main becomes a standalone PROC call + END; the PROC owns the head body.
    assert _kinds(program, "__owl__main") == [["CallProcedure", "End"]]
    assert program.ordered_basic_blocks["PROCSub10"][0].statements[0].__class__.__name__ \
        == "DefineProcedure"


def test_entry_head_subroutine_on_one_line_compiles(dotnet_backend):
    # The Recur1 shape: the whole routine (loop + recursion + RETURNs) is one line
    # that is also the program entry.
    program = _analyse([
        (10, " L=L+4:IF L=36 RETURN ELSE IF L=4 GOTO 10 ELSE "
             "GOSUB 10:GOSUB 10:L=L-4:IF L>4 RETURN")])
    assert dotnet_backend.emit_il(program)


def test_plain_entry_gosub_still_compiles(dotnet_backend):
    # Regression: a normal program whose first statement is a GOSUB (head != entry)
    # is unaffected by the main-entry bridge.
    program = _analyse([(10, " GOSUB 100"), (20, " END"),
                        (100, " X=X+1"), (110, " IF X<3 GOTO 100"), (120, " RETURN")])
    assert dotnet_backend.emit_il(program)


@requires_dotnet_toolchain
def test_entry_head_recursion_runs_and_halts(compile_and_run):
    # Recursion entered at the program start: N counts 1,2,3 on the way down, then
    # the outermost RETURN unwinds to END -- the program halts cleanly.
    out = compile_and_run(_analyse([(10, " N=N+1:PRINT N:IF N<3 GOSUB 10:RETURN")]))
    assert out.splitlines() == ["1", "2", "3"]
