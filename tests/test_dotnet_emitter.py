"""The dotnet backend's textual-CIL emitter.

The CIL-text generation runs everywhere (pure Python). The compile-and-run
tests are skipped unless the full .NET toolchain is present (see conftest:
``dotnet``, a CoreCLR ``ilasm`` and a freshly built net10 ``OwlRuntime.dll``).
"""

from conftest import requires_dotnet_toolchain
from helpers import analyse_fixture

from owl_basic.analysis import analyse_numbered_lines


def test_emit_il_lowers_print_and_arithmetic(dotnet_backend):
    il = dotnet_backend.emit_il(analyse_fixture("six_times_seven.bbctxt"))
    assert 'ldstr "Bah!"' in il
    assert "[OwlRuntime]OwlRuntime.BasicCommands::Print(string)" in il
    assert "ldc.i4 6" in il
    assert "ldc.i4 7" in il
    assert "\n        mul" in il
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


def test_emit_il_lowers_data_read_restore(dotnet_backend):
    il = dotnet_backend.emit_il(analyse_fixture("data_read.bbctxt"))
    # DATA becomes a static string array, READ reads/parses it, RESTORE rewinds.
    assert ".field static string[] __data" in il
    assert "newarr [System.Runtime]System.String" in il
    assert "ldelem.ref" in il
    assert "System.Int32::Parse(string)" in il
    assert "stsfld int32 __dataIndex" in il


@requires_dotnet_toolchain
def test_data_read_restore_compiles_and_runs(compile_and_run):
    # DATA 10,20,hello : READ a% (10), c$ ("20") : RESTORE : READ d% (10)
    stdout = compile_and_run(analyse_fixture("data_read.bbctxt"))
    assert stdout.split() == ["10", "20", "10"]


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
