"""Constant propagation feeds EVAL lowering: a constant string in a variable
makes EVAL(f$) compile, and a constant argument unblocks the function-by-name
dispatch -- neither is an EVAL special case, both fall out of propagation
running before EVAL lowering. See docs/constant-propagation.md.
"""
from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse
from owl_basic.syntax.ast import EvalFunc


def _has_eval(program):
    found = []

    def walk(node):
        if node is None:
            return
        if isinstance(node, EvalFunc):
            found.append(node)
        if hasattr(node, "forEachChild"):
            node.forEachChild(walk)

    walk(program.parse_tree)
    return bool(found)


def test_eval_of_a_constant_string_variable_analyses():
    # f$ is a constant expression string; propagation makes EVAL(f$) -> EVAL of a
    # literal, which the existing lowering re-parses. No EVAL node survives.
    program = analyse(
        'user1=10\narea=5\nf$="user1+area"\nA=EVAL(f$)\nPRINT A\nEND\n', name="ev")
    assert not _has_eval(program)


@requires_dotnet_toolchain
def test_eval_of_a_constant_string_variable_runs(compile_and_run):
    out = compile_and_run(analyse(
        'user1=10\narea=5\nf$="user1+area"\nPRINT EVAL(f$)\nEND\n', name="ev"))
    assert out.strip() == "15"


@requires_dotnet_toolchain
def test_dispatch_with_a_constant_argument_runs(compile_and_run):
    # The runtime name (c$) dispatches over the DEF FNs; the argument p$ is a
    # constant, so EVAL("FN"+c$+"("+p$+")") becomes the literal-argument dispatch
    # the lowering already compiles.
    out = compile_and_run(analyse(
        'READ c$\np$="7"\nPRINT EVAL("FN"+c$+"("+p$+")")\nEND\n'
        'DATA g\nDEFFNg(a)=a*2\n', name="ev"))
    assert out.strip() == "14"
