"""An IF with no THEN/ELSE evaluates its condition for side effects.

`IF GET` is the idiomatic "press any key to continue": the condition (a blocking
keypress) is evaluated for its effect and the result discarded -- there is no
clause. OWL used to fail codegen with "IF with no clauses"; now it lowers the
condition, pops the value and continues.
"""
from owl_basic.analysis import analyse
from owl_basic.ext.backends.dotnet.emitter import emit_program
from conftest import requires_dotnet_toolchain


def test_if_get_in_the_middle_lowers():
    emit_program(analyse("PRINT 1\nIF GET\nPRINT 2\n", name="t"), "t")


def test_if_get_at_end_lowers():
    # Terminal IF GET (the shape in the recursive-fractal corpus program).
    emit_program(analyse("PRINT 1\nIF GET\n", name="t"), "t")


def test_clauseless_if_on_a_plain_condition_lowers():
    emit_program(analyse("X=1\nIF X\nPRINT 2\n", name="t"), "t")


@requires_dotnet_toolchain
def test_if_get_waits_then_continues(compile_and_run):
    # GET consumes one input character; control then continues to PRINT 2.
    out = compile_and_run(
        analyse("PRINT 1\nIF GET\nPRINT 2\n", name="t"), stdin="x", timeout=30)
    assert out == "1\n2\n"
