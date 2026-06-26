"""The multi-line (block) IF -- a BASIC V form.

  IF <cond> THEN
    <statements>
  [ELSE
    <statements>]
  ENDIF

distinguished from the single-line IF by THEN sitting at end-of-line. OWL parses
the whole program at once, so the block spans logical lines; this pins that it
lowers and runs (both branches, nesting, multi-statement bodies). Surfaced across
many Acorn User Archimedes type-ins.
"""
from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse


@requires_dotnet_toolchain
def test_block_if_true_branch_runs(compile_and_run):
    out = compile_and_run(analyse(
        'A%=1\nIF A%=1 THEN\nPRINT "yes"\nENDIF\nPRINT "after"\nEND\n', name="bif"))
    assert out.splitlines() == ["yes", "after"]


@requires_dotnet_toolchain
def test_block_if_false_skips_the_body(compile_and_run):
    out = compile_and_run(analyse(
        'A%=0\nIF A%=1 THEN\nPRINT "yes"\nENDIF\nPRINT "after"\nEND\n', name="bif"))
    assert out.splitlines() == ["after"]


@requires_dotnet_toolchain
def test_block_if_else_true_branch(compile_and_run):
    out = compile_and_run(analyse(
        'A%=1\nIF A%=1 THEN\nPRINT "yes"\nELSE\nPRINT "no"\nENDIF\nEND\n', name="bif"))
    assert out.splitlines() == ["yes"]


@requires_dotnet_toolchain
def test_block_if_else_false_branch(compile_and_run):
    out = compile_and_run(analyse(
        'A%=0\nIF A%=1 THEN\nPRINT "yes"\nELSE\nPRINT "no"\nENDIF\nEND\n', name="bif"))
    assert out.splitlines() == ["no"]


@requires_dotnet_toolchain
def test_block_if_multi_statement_body(compile_and_run):
    out = compile_and_run(analyse(
        'A%=1\nIF A%=1 THEN\nPRINT "a"\nPRINT "b"\nENDIF\nEND\n', name="bif"))
    assert out.splitlines() == ["a", "b"]


@requires_dotnet_toolchain
def test_nested_block_if(compile_and_run):
    out = compile_and_run(analyse(
        'A%=1\nB%=1\nIF A%=1 THEN\nIF B%=1 THEN\nPRINT "both"\nENDIF\nENDIF\nEND\n',
        name="bif"))
    assert out.splitlines() == ["both"]
