"""Jump-table subroutines that fall through from one GOSUB target into the next.

A common BBC idiom is an ``ON x GOSUB l1,l2,...`` whose one-line handlers fall
through into each other: a handler with no RETURN runs on into the following
handler, which does RETURN. The later handler is therefore reached both by GOSUB
(it is its own table entry) and by fall-through from the earlier one.

convertSubroutinesToProcedures turns each GOSUB'd line into a PROC, sound only
when GOSUB is the head's sole foreign entry. Rather than reject the fall-through,
OWL bridges it: the fall-through edge becomes an explicit ``PROC PROCSub<head>``
call followed by ENDPROC, so the chain of ENDPROCs unwinds to the single GOSUB
frame -- the same destination the BBC's RETURN reaches -- with no return stack.

The terminator after the bridging call depends on context: ENDPROC inside another
subroutine (there is a GOSUB frame to return to), END on the main line (no frame:
the BBC RETURN would be "RETURN without GOSUB", which halts). A fall-through from
unreachable code is bridged the same way and simply never executed.
"""
from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse_numbered_lines


def _analyse(lines):
    return analyse_numbered_lines(lines, name="t", source_filepath="t")


def test_fallthrough_jump_table_compiles():
    # 100 (no RETURN) falls into 200 (RETURN); both are ON GOSUB targets.
    program = _analyse([(10, " ON X% GOSUB 100,200"), (20, " END"),
                        (100, ' PRINT "a"'),
                        (200, ' PRINT "b"'), (210, " RETURN")])
    assert program is not None


def test_plain_gosub_fallthrough_compiles():
    # The same chaining with plain GOSUBs rather than ON GOSUB.
    program = _analyse([(10, " GOSUB 100"), (20, " GOSUB 200"), (30, " END"),
                        (100, ' PRINT "a"'),
                        (200, ' PRINT "b"'), (210, " RETURN")])
    assert program is not None


def test_dead_code_before_subroutine_compiles():
    # Line 50 follows an ENDPROC (40), so it is unreachable; its fall-through into
    # the GOSUB'd head 100 is a phantom. Bridging it is harmless and 100 converts.
    program = _analyse([(10, " GOSUB 100"), (20, " END"),
                        (30, " DEFPROCa"), (40, " ENDPROC"),
                        (50, " REM dead code after ENDPROC"),
                        (100, ' PRINT "s"'), (110, " RETURN")])
    assert program is not None


def test_main_line_fallthrough_into_subroutine_compiles():
    # A fall-through into a GOSUB'd head from the main line has no GOSUB frame; on
    # a real BBC the RETURN is "RETURN without GOSUB", which halts. It is bridged
    # to PROC PROCSub<head> : END -- run the routine, then stop -- rather than
    # rejected (a common shape: a program that forgot END before its subroutines).
    program = _analyse([(10, " GOSUB 100"), (20, ' PRINT "main"'),
                        (100, ' PRINT "s"'), (110, " RETURN")])
    assert program is not None


def test_goto_into_subroutine_head_compiles_via_longjump():
    # A *branch* (GOTO) into a GOSUB'd head is a cross-method jump, which
    # convertLongjumpsToExceptions turns into an exception, so the head keeps no
    # foreign fall-through edge and converts -- independent of the bridge.
    program = _analyse([(10, " GOSUB 100"), (20, " GOTO 100"), (30, " END"),
                        (100, ' PRINT "s"'), (110, " RETURN")])
    assert program is not None


@requires_dotnet_toolchain
def test_fallthrough_chain_runs(compile_and_run):
    # GOSUB 100 prints "a" then falls into 200 -> "b" then RETURN; GOSUB 200
    # prints "b" then RETURN. So the output is a, b, b.
    out = compile_and_run(_analyse([
        (10, " GOSUB 100"), (20, " GOSUB 200"), (30, " END"),
        (100, ' PRINT "a"'),
        (200, ' PRINT "b"'), (210, " RETURN")]))
    assert out.split() == ["a", "b", "b"]


@requires_dotnet_toolchain
def test_main_line_fallthrough_runs_then_ends(compile_and_run):
    # GOSUB 100 -> "s"; back to 20 -> "main"; then the main line falls into 100,
    # which is bridged to PROC PROCSub100 : END -> "s", then stop. So: s, main, s.
    out = compile_and_run(_analyse([
        (10, " GOSUB 100"), (20, ' PRINT "main"'),
        (100, ' PRINT "s"'), (110, " RETURN")]))
    assert out.split() == ["s", "main", "s"]


@requires_dotnet_toolchain
def test_three_way_fallthrough_chain_runs(compile_and_run):
    # A -> B -> C chain: GOSUB 100 prints a,b,c; GOSUB 200 prints b,c; GOSUB 300
    # prints c. Nested PROC calls unwind through every ENDPROC to the one caller.
    out = compile_and_run(_analyse([
        (10, " GOSUB 100"), (20, " GOSUB 200"), (30, " GOSUB 300"), (40, " END"),
        (100, ' PRINT "a"'),
        (200, ' PRINT "b"'),
        (300, ' PRINT "c"'), (310, " RETURN")]))
    assert out.split() == ["a", "b", "c", "b", "c", "c"]
