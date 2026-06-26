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
def test_cross_method_constant_string_eval_runs(compile_and_run):
    # The ImageP shape: the formula constant f$ is set up in one PROC and EVAL'd
    # in another. Inter-procedural propagation makes EVAL(f$) -> EVAL("user1+area"),
    # which reads user1/area at run time.
    out = compile_and_run(analyse(
        'PROCsetup\nPROCuse\nEND\n'
        'DEFPROCsetup\nuser1=10\narea=5\nf$="user1+area"\nENDPROC\n'
        'DEFPROCuse\nPRINT EVAL(f$)\nENDPROC\n', name="ev"))
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
