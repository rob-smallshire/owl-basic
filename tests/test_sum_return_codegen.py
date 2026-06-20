"""Runtime boxing of union (sum) DEF FN return types in the .NET backend.

A function that returns different kinds on different paths (e.g. Integer on one,
String on another) has no single CIL primitive, so it lowers to a method that
returns ``object``: each value-typed arm is boxed at the return site, and the use
site tag-dispatches on the boxed runtime type. PRINT does this via Print(object).

These compile and run real programs, asserting the boxed value round-trips: the
same function prints as a number when it took the numeric arm and as text when it
took the string arm.
"""
from conftest import requires_dotnet_toolchain
from owl_basic.analysis import analyse


# --- IL-shape checks (pure Python, run even without the .NET toolchain) -----

def test_sum_function_returns_object_and_boxes(dotnet_backend):
    il = dotnet_backend.emit_il(analyse(
        'PRINT FNlabel(7)\nEND\n'
        'DEF FNlabel(n)\nIF n<10 THEN =n\n="many"\n', name="t"))
    # The function erases to an object-returning method...
    assert ".method static object FNlabel" in il
    # ...the numeric arm is boxed (n is a real, so a Double)...
    assert "box [System.Runtime]System.Double" in il
    # ...and the use site tag-dispatches via Print(object).
    assert "[OwlRuntime]OwlRuntime.BasicCommands::Print(object)" in il


# FNlabel(n) returns the number n itself for n<10, otherwise the string "many".
_LABEL = ('DEF FNlabel(n)\n'
          'IF n<10 THEN =n\n'
          '="many"\n')


@requires_dotnet_toolchain
def test_int_or_string_prints_numeric_arm(compile_and_run):
    out = compile_and_run(analyse('PRINT FNlabel(7)\nEND\n' + _LABEL, name="t"))
    assert out.splitlines() == ["7"]


@requires_dotnet_toolchain
def test_int_or_string_prints_string_arm(compile_and_run):
    out = compile_and_run(analyse('PRINT FNlabel(42)\nEND\n' + _LABEL, name="t"))
    assert out.splitlines() == ["many"]


@requires_dotnet_toolchain
def test_both_arms_in_one_run(compile_and_run):
    # Same function, both paths exercised in one program: number then text.
    src = 'PRINT FNlabel(3)\nPRINT FNlabel(99)\nEND\n' + _LABEL
    out = compile_and_run(analyse(src, name="t"))
    assert out.splitlines() == ["3", "many"]


@requires_dotnet_toolchain
def test_float_or_string_boxes_the_float_arm(compile_and_run):
    # The numeric arm is a float here, so the box carries a Double.
    src = ('PRINT FNg(1)\nPRINT FNg(0)\nEND\n'
           'DEF FNg(n)\nIF n>0 THEN =2.5\n="zero"\n')
    out = compile_and_run(analyse(src, name="t"))
    assert out.splitlines() == ["2.5", "zero"]


# FNt returns an integer, a float, or a string on three different paths; the
# numerics collapse to Float, so the static type is Float|String.
_THREE_WAY = ('DEF FNt(n)\n'
              'IF n=0 THEN =42\n'
              'IF n=1 THEN =2.5\n'
              '="text"\n')


@requires_dotnet_toolchain
def test_three_way_sum_each_arm_prints(compile_and_run):
    src = 'PRINT FNt(0)\nPRINT FNt(1)\nPRINT FNt(2)\nEND\n' + _THREE_WAY
    out = compile_and_run(analyse(src, name="t"))
    assert out.splitlines() == ["42", "2.5", "text"]


@requires_dotnet_toolchain
def test_pass_through_sum_flows_the_boxed_value(compile_and_run):
    # FNouter just returns FNlabel(n): the boxed object flows straight through a
    # second object-returning method without re-boxing or unboxing.
    src = ('PRINT FNouter(5)\nPRINT FNouter(50)\nEND\n'
           'DEF FNouter(n)=FNlabel(n)\n' + _LABEL)
    out = compile_and_run(analyse(src, name="t"))
    assert out.splitlines() == ["5", "many"]


@requires_dotnet_toolchain
def test_long_integer_or_string_boxes_int64(compile_and_run):
    # n%*2 is int32*int32, evaluated in 64 bits -> LongInteger, so this is a
    # LongInteger|String sum whose numeric arm boxes an Int64.
    src = ('PRINT FNw(5)\nPRINT FNw(-1)\nEND\n'
           'DEF FNw(n%)\nIF n%>0 THEN =n%*2\n="neg"\n')
    out = compile_and_run(analyse(src, name="t"))
    assert out.splitlines() == ["10", "neg"]


@requires_dotnet_toolchain
def test_computed_numeric_arm_is_boxed(compile_and_run):
    # The numeric arm is an expression (n*n), not a literal -- the computed
    # value is boxed before return.
    src = ('PRINT FNsq(4)\nPRINT FNsq(-1)\nEND\n'
           'DEF FNsq(n)\nIF n>=0 THEN =n*n\n="negative"\n')
    out = compile_and_run(analyse(src, name="t"))
    assert out.splitlines() == ["16", "negative"]
