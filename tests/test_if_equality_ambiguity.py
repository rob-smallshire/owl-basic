"""A single-line IF whose condition is an equality must parse the '=' as the
relational test, not as a '=expr' function return. The colon form `IF a=b:stmt`
(no THEN) was mis-parsed as `IF a` + `=b` (a return) -- the overloaded-'=' LALR
ambiguity -- which then produced invalid IL.
"""
from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse_numbered_lines


def _first_if(program):
    found = []

    def walk(node):
        if type(node).__name__ == "If":
            found.append(node)
        if hasattr(node, "forEachChild"):
            node.forEachChild(walk)

    for blocks in program.ordered_basic_blocks.values():
        for block in blocks:
            for statement in block.statements:
                walk(statement)
    return found[0]


def test_colon_if_condition_is_an_equality_not_a_return():
    program = analyse_numbered_lines([(10, 'IF 1=1:PRINT"x"'), (20, "END")], name="t")
    iff = _first_if(program)
    assert type(iff.condition).__name__ == "Equal"
    # The true clause is the PRINT, with no spurious ReturnFromFunction.
    kinds = []
    iff.forEachChild(lambda n: kinds.append(type(n).__name__))
    assert "ReturnFromFunction" not in kinds


@requires_dotnet_toolchain
def test_colon_if_with_equality_runs(compile_and_run):
    out = compile_and_run(analyse_numbered_lines(
        [(10, 'IF 1=1:PRINT"yes"'), (20, 'IF 1=2:PRINT"no"'), (30, "END")], name="t"))
    assert out == "yes\n"


@requires_dotnet_toolchain
def test_colon_if_with_equality_in_a_function_returns_correctly(compile_and_run):
    # The Beebium-confirmed shape: a colon-IF whose body is a =return, inside FN.
    out = compile_and_run(analyse_numbered_lines(
        [(10, "PRINT FNt(5)"), (20, "PRINT FNt(-1)"), (30, "END"),
         (40, "DEF FNt(n)"), (50, "IF n>0:=n*2"), (60, "=999")], name="t"))
    assert out.splitlines() == ["10", "999"]


@requires_dotnet_toolchain
def test_equality_condition_and_return_on_one_line(compile_and_run):
    # The case that was broken: an EQUALITY condition (n=0) AND a =return (=99)
    # on the same line -- exactly CLKSP3's FNAck `IF M%=0:=N%+1`.
    out = compile_and_run(analyse_numbered_lines(
        [(10, "PRINT FNz(0)"), (20, "PRINT FNz(3)"), (30, "END"),
         (40, "DEF FNz(n)"), (50, "IF n=0:=99"), (60, "=n*2")], name="z"))
    assert out.splitlines() == ["99", "6"]   # n=0 -> 99 ; else n*2 = 6


@requires_dotnet_toolchain
def test_plain_equality_return_still_works(compile_and_run):
    out = compile_and_run(analyse_numbered_lines(
        [(10, "PRINT FNd(4)"), (20, "END"), (30, "DEF FNd(n)"), (40, "=n*n")], name="d"))
    assert out.splitlines() == ["16"]
