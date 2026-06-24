"""The dotnet backend's textual-CIL emitter.

The CIL-text generation runs everywhere (pure Python). The compile-and-run
tests are skipped unless the full .NET toolchain is present (see conftest:
``dotnet``, a CoreCLR ``ilasm`` and a freshly built net10 ``OwlRuntime.dll``).
"""

from conftest import requires_dotnet_toolchain
from helpers import analyse_fixture

from owl_basic.analysis import analyse, analyse_numbered_lines


def _statement_types(program):
    return [
        type(statement).__name__
        for blocks in program.ordered_basic_blocks.values()
        for block in blocks
        for statement in block.statements
    ]


def test_emit_il_lowers_print_and_arithmetic(dotnet_backend):
    il = dotnet_backend.emit_il(analyse_fixture("six_times_seven.bbctxt"))
    assert 'ldstr "Bah!"' in il
    assert "[OwlRuntime]OwlRuntime.BasicCommands::Print(string)" in il
    # The constant 6*7 is folded to 42 at compile time, so no `mul` remains.
    assert "ldc.i4 42" in il
    assert "\n        mul" not in il
    assert "[OwlRuntime]OwlRuntime.BasicCommands::Print(int32)" in il
    assert ".entrypoint" in il


def test_emit_il_lowers_scalar_integer_variables(dotnet_backend):
    il = dotnet_backend.emit_il(analyse_fixture("scalar_variables.bbctxt"))
    # A% and B% are global (BBC variables are global by default) -> static fields.
    assert ".field static int32 i_A" in il
    assert ".field static int32 i_B" in il
    assert "stsfld int32 i_A" in il
    assert "stsfld int32 i_B" in il
    assert "ldsfld int32 i_A" in il
    assert "ldsfld int32 i_B" in il


def test_emit_il_lowers_string_and_float_variables(dotnet_backend):
    il = dotnet_backend.emit_il(analyse_fixture("string_float_variables.bbctxt"))
    assert ".field static string s_S" in il    # S$
    assert ".field static float64 f_N" in il   # N
    assert ".field static float64 f_C" in il   # C, assigned from an integer literal
    assert "conv.r8" in il                     # integer -> float cast for C = 6


def test_emit_il_lowers_if_with_relational_condition(dotnet_backend):
    il = dotnet_backend.emit_il(analyse_fixture("conditional.bbctxt"))
    assert "cgt" in il             # A% > 5
    assert "\n        neg" in il   # converted to a BBC boolean (0 / -1)
    # The clauses live in their own labelled blocks, reached by a branch.
    assert "BB_0:" in il
    assert ("brtrue " in il) or ("brfalse " in il)


def test_emit_il_lowers_procedure_as_separate_method(dotnet_backend):
    il = dotnet_backend.emit_il(analyse_fixture("procedure.bbctxt"))
    # The PROC becomes its own static method, called from Main.
    assert ".method static void PROCgreet() cil managed" in il
    assert ".method static void Main() cil managed" in il
    assert "call void PROCgreet()" in il
    # Exactly one entry point.
    assert il.count(".entrypoint") == 1


def test_emit_il_lowers_procedure_with_parameters(dotnet_backend):
    il = dotnet_backend.emit_il(analyse_fixture("procedure_param.bbctxt"))
    # Formal parameters become typed method arguments, read with ldarg.
    assert ".method static void PROCsquare(int32 A0) cil managed" in il
    assert "ldarg.0" in il
    assert "call void PROCsquare(int32)" in il


def test_emit_il_makes_a_variable_used_across_procedures_global(dotnet_backend):
    il = dotnet_backend.emit_il(analyse_fixture("global_var.bbctxt"))
    # score% is set in main and updated in PROCbonus, so it must be one shared
    # static field, not a per-method local.
    assert ".field static int32 i_score" in il
    assert "ldsfld int32 i_score" in il
    assert "stsfld int32 i_score" in il
    assert "stloc" not in il   # nothing here is method-local


def test_emit_il_lowers_byte_indirection(dotnet_backend):
    il = dotnet_backend.emit_il(analyse_fixture("byte_indirection.bbctxt"))
    # ? indirection goes through OwlRuntime's address-space byte array.
    assert "call uint8[] [OwlRuntime]OwlRuntime.MemoryMap::get_Memory()" in il
    assert "stelem.i1" in il   # writes
    assert "ldelem.u1" in il   # reads (unsigned: 0..255)


def test_emit_il_lowers_print_manipulators(dotnet_backend):
    il = dotnet_backend.emit_il(analyse_fixture("print_manipulators.bbctxt"))
    # ' forces a NewLine; the runtime call is present for it.
    assert "NewLine()" in il


@requires_dotnet_toolchain
def test_print_manipulators_compile_and_run(compile_and_run):
    # "A";"B" -> AB ; "C"'"D" -> C/D ; "no newline"; (suppressed) ; "joined"
    stdout = compile_and_run(analyse_fixture("print_manipulators.bbctxt"))
    assert stdout == "AB\nC\nD\nno newlinejoined\n"


def test_emit_il_lowers_function_methods(dotnet_backend):
    il = dotnet_backend.emit_il(analyse_fixture("functions.bbctxt"))
    # FNs become value-returning methods, with the return type inferred (HM).
    assert ".method static int32 FNdouble(int32 A0) cil managed" in il
    assert ".method static float64 FNhalf(float64 A0) cil managed" in il
    assert "call int32 FNfact(int32)" in il          # recursive call
    assert ".method static int32 FNfact(int32 A0) cil managed" in il


@requires_dotnet_toolchain
def test_function_methods_compile_and_run(compile_and_run):
    # FNdouble(21)=42 (int), FNhalf(7)=3.5 (float), FNfact(5)=120 (recursive)
    stdout = compile_and_run(analyse_fixture("functions.bbctxt"))
    assert stdout.split("\n") == ["42", "3.5", "120", ""]


def test_emit_il_lowers_string_comparison(dotnet_backend):
    il = dotnet_backend.emit_il(analyse_fixture("string_compare.bbctxt"))
    assert "System.String::Equals(string, string)" in il
    assert "System.String::Compare(string, string)" in il


@requires_dotnet_toolchain
def test_string_comparison_compile_and_run(compile_and_run):
    # a$="apple",b$="banana": a$="apple"->eq, a$<b$->less, a$<>b$->diff
    stdout = compile_and_run(analyse_fixture("string_compare.bbctxt"))
    assert stdout.split() == ["eq", "less", "diff"]


_LONGJUMP_PROGRAM = [
    (10, 'PRINT "start"'), (20, "PROCjump"), (30, 'PRINT "unreached"'),
    (40, 'PRINT "landed"'), (50, "END"),
    (60, "DEFPROCjump"), (70, "GOTO 40"), (80, "ENDPROC"),
]


def test_emit_il_lowers_longjump(dotnet_backend):
    il = dotnet_backend.emit_il(analyse_numbered_lines(_LONGJUMP_PROGRAM, name="lj"))
    # The GOTO out of the PROC throws; Main catches and dispatches to the target.
    assert "newobj instance void [OwlRuntime]OwlRuntime.LongJumpException::.ctor(int32)" in il
    assert "throw" in il
    assert "catch [OwlRuntime]OwlRuntime.LongJumpException" in il
    assert "L_40:" in il
    assert "beq L_40" in il


@requires_dotnet_toolchain
def test_longjump_out_of_proc_compiles_and_runs(compile_and_run):
    # PROCjump does GOTO 40 (out of the PROC, into Main); control resumes at
    # line 40, so "unreached" between the call and line 40 is skipped.
    stdout = compile_and_run(analyse_numbered_lines(_LONGJUMP_PROGRAM, name="lj"))
    assert stdout.split() == ["start", "landed"]


# A backward GOTO into a loop region makes the whole region one strongly-connected
# component; the approximate topological order then places this FOR's NEXT block
# before the FOR's own block. Codegen pre-registers every FOR's state up front, so
# the NEXT still resolves it (execution stays correct -- branches carry control
# flow). Before that, _stmt_Next hit a KeyError. Reduced from corpus program
# e2aabf59fba8 (a Hamming-code demo looping forever via GOTO 2).
_GOTO_LOOP_PROGRAM = [
    (1, "MODE 2"),
    (2, "CLS:N=RND(2^16):PROCS(N,2):M=N:Q=0:FOR K=0 TO 15:"
        "IF(K AND(K-1))AND(M AND 1)=1:Q=Q EOR K"),
    (3, "M=M DIV 2:NEXT:PROCS(Q,1):FOR I=0 TO 3:N=N OR((Q AND 1)*2):"
        "Q=Q DIV 2:NEXT:Z=5:GOTO 2"),
    (4, 'DEFPROCS(N,L):FOR K=0 TO 4^L-1:M=((N DIV(2^K))AND 1):'
        'IF(K MOD 4)=3:PRINT""'),
    (5, "NEXT:ENDPROC"),
]


def test_emit_il_for_with_next_block_ordered_before_it(dotnet_backend):
    il = dotnet_backend.emit_il(analyse_numbered_lines(_GOTO_LOOP_PROGRAM, name="gl"))
    assert "FOR_body" in il   # the loops lowered; no KeyError on the early NEXT


# Lines 30/40 sit physically before DEFPROC but are reachable only from PROCp
# (via GOTO 30), so the CFG tags them as part of PROCp and the GOTO stays an
# ordinary in-scope branch -- no LongJump, no throw.
_DISPLACED_PROC_PROGRAM = [
    (10, "PROCp"), (20, "END"), (30, 'PRINT "B"'), (40, "ENDPROC"),
    (50, "DEFPROCp"), (60, 'PRINT "A"'), (70, "GOTO 30"),
]


def test_displaced_proc_body_goto_is_not_a_longjump(dotnet_backend):
    program = analyse_numbered_lines(_DISPLACED_PROC_PROGRAM, name="intra")
    assert "LongJump" not in _statement_types(program)
    assert "Goto" in _statement_types(program)
    assert "LongJumpException" not in dotnet_backend.emit_il(program)  # no machinery


@requires_dotnet_toolchain
def test_displaced_proc_body_goto_compiles_and_runs(compile_and_run):
    program = analyse_numbered_lines(_DISPLACED_PROC_PROGRAM, name="intra")
    assert compile_and_run(program).split() == ["A", "B"]


def test_emit_il_lowers_mode(dotnet_backend):
    il = dotnet_backend.emit_il(analyse_fixture("mode.bbctxt"))
    assert "call void [OwlRuntime]OwlRuntime.BasicCommands::Mode(int32)" in il


@requires_dotnet_toolchain
def test_mode_compiles_and_runs(compile_and_run):
    # MODE 7 then PRINT: the runtime falls back to the raw console headless,
    # so text still appears.
    assert "hi" in compile_and_run(analyse_fixture("mode.bbctxt"))


@requires_dotnet_toolchain
def test_lomem_compiles_and_runs(compile_and_run):
    # LOMEM is a pseudo-variable backed by an OwlRuntime property: write/read.
    assert "1000" in compile_and_run(analyse_fixture("lomem.bbctxt"))


@requires_dotnet_toolchain
def test_int_function_compiles_and_runs(compile_and_run):
    # INT floors toward negative infinity: INT(3.7)=3, INT(-2.3)=-3
    stdout = compile_and_run(analyse_fixture("int_function.bbctxt"))
    assert stdout.split() == ["3", "-3"]


def test_emit_il_lowers_simple_functions(dotnet_backend):
    il = dotnet_backend.emit_il(analyse_fixture("simple_functions.bbctxt"))
    assert "System.Math::Abs(int32)" in il
    assert "System.Math::Abs(float64)" in il
    assert "System.Math::Sign(int32)" in il
    assert "\n        not" in il          # NOT
    assert "ldc.i4.m1" in il              # TRUE
    assert "BasicCommands::Sqr(float64)" in il


@requires_dotnet_toolchain
def test_simple_functions_compile_and_run(compile_and_run):
    # ABS(-5)=5, ABS(-2.5)=2.5, SGN(-3)=-1, NOT 0=-1, TRUE=-1, FALSE=0, SQR(9)=3
    stdout = compile_and_run(analyse_fixture("simple_functions.bbctxt"))
    assert stdout.split("\n") == ["5", "2.5", "-1", "-1", "-1", "0", "3", ""]


def test_emit_il_lowers_val(dotnet_backend):
    il = dotnet_backend.emit_il(analyse_fixture("val_function.bbctxt"))
    assert "BasicCommands::Val(string)" in il


@requires_dotnet_toolchain
def test_val_compiles_and_runs(compile_and_run):
    # VAL reads the leading numeric literal: 42; 3.5 (stops at x); 0 (no number).
    # It scans an E exponent too, and must backtrack when the E has no exponent
    # digits -- VAL("123E") is 123, not an error and not 123*10^something.
    stdout = compile_and_run(analyse_fixture("val_function.bbctxt"))
    assert stdout.split() == ["42", "3.5", "0", "123", "123", "12300", "12300"]


@requires_dotnet_toolchain
def test_val_overflow_faults_too_big(compile_expecting_error):
    # VAL of a literal beyond the float range faults "Too big" (BBC error 20),
    # rather than yielding an infinity.
    out = compile_expecting_error(analyse('PRINT VAL("1E999")\nEND\n', name="t"))
    assert "too big" in out.lower()


def test_emit_il_lowers_string_functions(dotnet_backend):
    il = dotnet_backend.emit_il(analyse_fixture("string_functions.bbctxt"))
    assert "System.String::Concat(string, string)" in il
    assert "System.String::get_Length()" in il
    assert "BasicCommands::LeftStr(string, int32)" in il
    assert "BasicCommands::RightStr(string, int32)" in il
    assert "BasicCommands::MidStr(string, int32, int32)" in il
    assert "BasicCommands::Chr(int32)" in il
    assert "BasicCommands::Asc(string)" in il
    assert "BasicCommands::Instr(string, string)" in il


@requires_dotnet_toolchain
def test_string_functions_compile_and_run(compile_and_run):
    stdout = compile_and_run(analyse_fixture("string_functions.bbctxt"))
    assert stdout.split("\n") == [
        "5", "HE", "LO", "ELL", "A", "65", "3", "foobar", "",
    ]


def test_emit_il_lowers_input(dotnet_backend):
    il = dotnet_backend.emit_il(analyse_fixture("input_demo.bbctxt"))
    assert "newarr [System.Runtime]System.Type" in il
    assert "::Input(bool, class [System.Runtime]System.Type[])" in il
    assert "Queue`1<object>::Dequeue()" in il
    assert "castclass [System.Runtime]System.String" in il   # string var
    assert "unbox.any int32" in il                           # integer var


@requires_dotnet_toolchain
def test_input_compiles_and_runs(compile_and_run):
    # INPUT a$ (hello), INPUT n% (21->42), INPUT x%,y% (3,4 from one line ->7)
    stdout = compile_and_run(
        analyse_fixture("input_demo.bbctxt"), stdin="hello\n21\n3,4\n"
    )
    # Each INPUT prints a '?' prompt; check the echoed/computed values.
    assert "got hello" in stdout      # string input
    assert "42" in stdout             # n%=21 -> 42
    assert stdout.rstrip().endswith("7")   # x%+y% = 3+4 from one line "3,4"


@requires_dotnet_toolchain
def test_input_reprompts_until_enough_values(compile_and_run):
    # INPUT x%,y% is one read of two values; given one value per line it must
    # re-prompt for the second (the runtime loops until it has both).
    program = analyse_numbered_lines(
        [(10, "INPUT x%, y%"), (20, "PRINT x% + y%"), (30, "END")], name="rp"
    )
    stdout = compile_and_run(program, stdin="3\n4\n")
    assert stdout.count("?") == 2          # prompted twice
    assert stdout.rstrip().endswith("7")


def test_emit_il_lowers_data_read_restore(dotnet_backend):
    il = dotnet_backend.emit_il(analyse_fixture("data_read.bbctxt"))
    # DATA becomes a static string array, READ reads/parses it, RESTORE rewinds.
    assert ".field static string[] __data" in il
    assert "newarr [System.Runtime]System.String" in il
    assert "ldelem.ref" in il
    # Numeric READ uses BBC VAL semantics (empty/garbage -> 0), not a strict Parse.
    assert "BasicCommands::Val(string)" in il
    assert "stsfld int32 __dataIndex" in il


@requires_dotnet_toolchain
def test_data_empty_items_preserved(compile_and_run):
    # Empty DATA items between adjacent commas (or a trailing comma) are
    # significant: N commas yield N+1 items, keeping sequential READ aligned.
    # "DATA ,,x" -> ["","","x"]; "DATA ,7" -> ["","7"]. A numeric READ of an
    # empty item yields 0 (BBC VAL semantics), not an error.
    stdout = compile_and_run(analyse_fixture("data_empty_items.bbctxt"))
    assert "[][][x]" in stdout
    lines = [l.strip() for l in stdout.splitlines() if l.strip()]
    assert lines[-2:] == ["0", "7"]


@requires_dotnet_toolchain
def test_data_read_restore_compiles_and_runs(compile_and_run):
    # DATA 10,20,hello : READ a% (10), c$ ("20") : RESTORE : READ d% (10)
    stdout = compile_and_run(analyse_fixture("data_read.bbctxt"))
    assert stdout.split() == ["10", "20", "10"]


@requires_dotnet_toolchain
def test_dynamic_restore_compiles_and_runs(compile_and_run):
    # RESTORE ln% (a variable) rewinds via an inline jump table over DATA lines.
    lines = [
        (10, "DATA 11, 22"), (20, "DATA 33, 44"), (30, "ln% = 20"),
        (40, "RESTORE ln%"), (50, "READ a%"), (60, "PRINT a%"), (70, "END"),
    ]
    program = analyse_numbered_lines(lines, name="dynr")
    assert compile_and_run(program).strip() == "33"


@requires_dotnet_toolchain
def test_restore_to_line_compiles_and_runs(compile_and_run):
    # RESTORE 20 rewinds to the DATA on line 20, so READ c% gets 33.
    lines = [
        (10, "DATA 11, 22"), (20, "DATA 33, 44"),
        (30, "READ a%"), (40, "READ b%"), (50, "RESTORE 20"), (60, "READ c%"),
        (70, "PRINT a%"), (80, "PRINT b%"), (90, "PRINT c%"), (100, "END"),
    ]
    program = analyse_numbered_lines(lines, name="restoreline")
    assert compile_and_run(program).split() == ["11", "22", "33"]


def test_emit_il_run_resets_globals(dotnet_backend):
    program = analyse_numbered_lines(
        [(10, "n% = 1"), (20, "RUN")], name="run"
    )
    il = dotnet_backend.emit_il(program)
    # RUN clears variables via a generated __reset that zeroes the globals.
    assert ".method static void __reset() cil managed" in il
    assert "stsfld int32 i_n" in il          # n% zeroed in __reset
    assert "call void __reset()" in il        # RUN calls it


@requires_dotnet_toolchain
def test_run_clears_variables_and_restarts(compile_and_run):
    # n% is set to 42, then RUN restarts: on the next pass n% must read back as
    # 0 (cleared), never 42. INPUT terminates the otherwise-endless restart.
    lines = [
        (10, "PRINT n%"), (20, "n% = 42"), (30, "INPUT cmd$"),
        (40, 'IF cmd$ = "q" THEN END'), (50, "RUN"),
    ]
    program = analyse_numbered_lines(lines, name="rc")
    stdout = compile_and_run(program, stdin="x\nq\n")
    assert "42" not in stdout          # the variable was cleared by RUN
    assert stdout.count("0") == 2      # n% read 0 on both passes


@requires_dotnet_toolchain
def test_on_goto_compiles_and_runs(compile_and_run):
    # ON X% GOTO 40,50,60 with X%=2 jumps to the second target (1-based).
    lines = [
        (10, "X% = 2"), (20, "ON X% GOTO 40, 50, 60"), (30, "END"),
        (40, 'PRINT "one"'), (45, "END"), (50, 'PRINT "two"'), (55, "END"),
        (60, 'PRINT "three"'), (65, "END"),
    ]
    program = analyse_numbered_lines(lines, name="og")
    assert compile_and_run(program).strip() == "two"


def test_emit_il_lowers_repeat_until(dotnet_backend):
    il = dotnet_backend.emit_il(analyse_fixture("repeat_until.bbctxt"))
    # UNTIL branches back to the REPEAT block while the condition is false.
    assert "brfalse BB_" in il


def test_emit_il_lowers_for_next(dotnet_backend):
    il = dotnet_backend.emit_il(analyse_fixture("for_next.bbctxt"))
    # NEXT increments, checks the step's sign, and branches back to the body top.
    assert "FOR_body_" in il
    assert "bgt FOR_pos_" in il
    assert "brtrue FOR_body_" in il


@requires_dotnet_toolchain
def test_six_times_seven_compiles_and_runs(compile_and_run):
    # The computed value reaches stdout (BBC BASIC: PRINT "..." 6*7).
    assert "Six times seven is 42" in compile_and_run(
        analyse_fixture("six_times_seven.bbctxt")
    )


@requires_dotnet_toolchain
def test_scalar_variables_compile_and_run(compile_and_run):
    # A% = 6 : B% = 7 : PRINT "Product is " A% * B%
    assert "Product is 42" in compile_and_run(
        analyse_fixture("scalar_variables.bbctxt")
    )


@requires_dotnet_toolchain
def test_string_and_float_variables_compile_and_run(compile_and_run):
    # S$="Answer is " : N=3.5 : PRINT S$ N -> "Answer is 3.5"; C=6 : PRINT C -> "6"
    stdout = compile_and_run(analyse_fixture("string_float_variables.bbctxt"))
    assert "Answer is 3.5" in stdout
    assert "\n6" in stdout


@requires_dotnet_toolchain
def test_if_empty_then_compiles_and_runs(compile_and_run):
    # IF n%=0 THEN ELSE PRINT "nonzero" : the empty THEN branch is the true path.
    stdout = compile_and_run(analyse_fixture("if_empty_then.bbctxt"))
    assert stdout.split() == ["nonzero", "done"]


@requires_dotnet_toolchain
def test_conditional_compiles_and_runs(compile_and_run):
    # A%=8 : IF A%>5 THEN PRINT "big" ELSE PRINT "small" : PRINT "done"
    stdout = compile_and_run(analyse_fixture("conditional.bbctxt"))
    assert "big" in stdout
    assert "small" not in stdout
    assert "done" in stdout


@requires_dotnet_toolchain
def test_procedure_compiles_and_runs(compile_and_run):
    # PROCgreet : PRINT "after" : END : DEFPROCgreet PRINT "Hi from PROC" ENDPROC
    stdout = compile_and_run(analyse_fixture("procedure.bbctxt"))
    assert "Hi from PROC" in stdout
    assert "after" in stdout
    # The PROC body runs before control returns to print "after".
    assert stdout.index("Hi from PROC") < stdout.index("after")


@requires_dotnet_toolchain
def test_procedure_with_parameter_compiles_and_runs(compile_and_run):
    # PROCsquare(5) : ... DEFPROCsquare(n%) PRINT n%*n% ENDPROC -> 25
    assert "25" in compile_and_run(analyse_fixture("procedure_param.bbctxt"))


@requires_dotnet_toolchain
def test_procedure_with_mixed_parameters_compiles_and_runs(compile_and_run):
    # PROCshow("Value: ", 42) with formals (label$, n%) -> "Value: 42"
    assert "Value: 42" in compile_and_run(
        analyse_fixture("procedure_params2.bbctxt")
    )


@requires_dotnet_toolchain
def test_global_variable_shared_across_procedure_compiles_and_runs(compile_and_run):
    # score%=10 : PROCbonus (adds 5 to the global) : PRINT score% -> 15
    # A per-method local would wrongly print 10.
    assert "15" in compile_and_run(analyse_fixture("global_var.bbctxt"))


@requires_dotnet_toolchain
def test_local_variable_shadows_global_compiles_and_runs(compile_and_run):
    # X%=100 : PROCchange (LOCAL X% : X%=7) : PRINT X% -> 100
    # LOCAL must make PROCchange's X% a method local, leaving the global intact.
    assert "100" in compile_and_run(analyse_fixture("local_var.bbctxt"))


@requires_dotnet_toolchain
def test_dynamic_scoping_local_and_parameter_visible_to_called_routine(compile_and_run):
    # In BBC BASIC a LOCAL and a formal parameter are dynamically scoped: each is
    # the global of that name, saved on entry and restored on exit, so a routine
    # called in between (PROCinner) sees the caller's parameter Z$ ("hello") and
    # LOCAL I% (7) through those globals. Sphinx's word-wrap printer relies on it.
    assert "hello7" in compile_and_run(analyse_fixture("dynamic_scope.bbctxt"))


@requires_dotnet_toolchain
def test_byte_indirection_compiles_and_runs(compile_and_run):
    # ptr%?10=65 (dyadic write), ?20=66 (unary write), read back via dyadic.
    stdout = compile_and_run(analyse_fixture("byte_indirection.bbctxt"))
    assert "65" in stdout
    assert "66" in stdout


@requires_dotnet_toolchain
def test_repeat_until_compiles_and_runs(compile_and_run):
    # n%=0 : REPEAT n%=n%+1 : PRINT n% : UNTIL n%>=3  -> 1, 2, 3
    stdout = compile_and_run(analyse_fixture("repeat_until.bbctxt"))
    assert stdout.split() == ["1", "2", "3"]


def test_emit_il_lowers_while_endwhile(dotnet_backend):
    # WHILE is pre-tested: its condition branches past the loop when false, and
    # ENDWHILE is an unconditional back-edge to the WHILE test.
    il = dotnet_backend.emit_il(
        analyse("X=0\nWHILE X<3\nX=X+1\nENDWHILE\nPRINT99\n", name="t"))
    assert "brfalse BB_" in il    # pre-test exits past the loop
    assert "\n        br BB_" in il    # ENDWHILE back-edge to the WHILE test


@requires_dotnet_toolchain
def test_while_endwhile_compiles_and_runs(compile_and_run):
    # X=0 : WHILE X<3 : X=X+1 : PRINT X : ENDWHILE  -> 1, 2, 3
    stdout = compile_and_run(
        analyse("X=0\nWHILE X<3\nX=X+1\nPRINTX\nENDWHILE\n", name="t"))
    assert stdout.split() == ["1", "2", "3"]


@requires_dotnet_toolchain
def test_while_with_initially_false_condition_skips_body(compile_and_run):
    # Pre-tested: the body must not run when the condition is false on entry.
    stdout = compile_and_run(
        analyse("X=5\nWHILE X<3\nPRINTX\nENDWHILE\nPRINT99\n", name="t"))
    assert stdout.split() == ["99"]


@requires_dotnet_toolchain
def test_for_next_ascending_compiles_and_runs(compile_and_run):
    # FOR i% = 1 TO 3 : PRINT i% : NEXT  -> 1, 2, 3
    stdout = compile_and_run(analyse_fixture("for_next.bbctxt"))
    assert stdout.split() == ["1", "2", "3"]


@requires_dotnet_toolchain
def test_for_next_negative_step_compiles_and_runs(compile_and_run):
    # FOR x = 10 TO 6 STEP -2 : PRINT x : NEXT  -> 10, 8, 6
    stdout = compile_and_run(analyse_fixture("for_next_step.bbctxt"))
    assert stdout.split() == ["10", "8", "6"]
