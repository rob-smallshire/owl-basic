"""The dotnet backend's textual-CIL emitter.

The CIL-text generation runs everywhere (pure Python). The compile-and-run
tests are skipped unless the full .NET toolchain is present (see conftest:
``dotnet``, a CoreCLR ``ilasm`` and a freshly built net10 ``OwlRuntime.dll``).
"""

from conftest import requires_dotnet_toolchain
from helpers import analyse_fixture


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
    # Two integer locals are declared and assigned, then read back.
    assert ".locals init" in il
    assert "int32 V_0" in il
    assert "int32 V_1" in il
    assert "stloc V_0" in il
    assert "stloc V_1" in il
    assert "ldloc V_0" in il
    assert "ldloc V_1" in il


def test_emit_il_lowers_string_and_float_variables(dotnet_backend):
    il = dotnet_backend.emit_il(analyse_fixture("string_float_variables.bbctxt"))
    assert "string V_0" in il      # S$
    assert "float64 V_1" in il     # N
    assert "float64 V_2" in il     # C (real), assigned from an integer literal
    assert "conv.r8" in il         # integer -> float cast for C = 6


def test_emit_il_lowers_if_with_relational_condition(dotnet_backend):
    il = dotnet_backend.emit_il(analyse_fixture("conditional.bbctxt"))
    assert "cgt" in il             # A% > 5
    assert "\n        neg" in il   # converted to a BBC boolean (0 / -1)
    # The clauses live in their own labelled blocks, reached by a branch.
    assert "BB_0:" in il
    assert ("brtrue " in il) or ("brfalse " in il)


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
