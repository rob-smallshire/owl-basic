"""CHAIN loads and runs another program, handing over the resident integers.

CHAIN "B" replaces the running program with B and continues there; only the
resident integers @% and A%-Z% carry across (named variables do not), exactly
as on the BBC -- see the BASIC II program-lifecycle analysis. On the .NET target
this is a fresh `dotnet B.dll` process: the chaining program stages its residents
into the environment (over the inherited ones, so residents it never touched pass
through too), the runtime resolves the BBC name to <name>.dll beside the chaining
assembly, launches it, and exits with its status. CHAIN never returns.

The end-to-end tests compile two programs A and B side by side in one directory
and run A, expecting B's output.
"""
import os
import shutil
import subprocess

import pytest

from conftest import requires_dotnet_toolchain
from helpers import find_owlruntime_dll

from owl_basic.analysis import analyse, analyse_numbered_lines
from owl_basic.syntax.ast import Chain


def test_chain_parses_to_a_chain_node():
    program = analyse_numbered_lines([(10, ' CHAIN "B"'), (20, " END")], name="a")
    nodes = [s for blocks in program.ordered_basic_blocks.values()
             for b in blocks for s in b.statements if isinstance(s, Chain)]
    assert len(nodes) == 1


def _compile_two_and_run_first(dotnet_backend, tmp_path, source_a, source_b,
                               **env_overrides):
    """Compile A and B into one directory and run A; return A-then-B's stdout."""
    a_dll = dotnet_backend.generate(analyse(source_a, name="A"), tmp_path)
    dotnet_backend.generate(analyse(source_b, name="B"), tmp_path)
    shutil.copy(find_owlruntime_dll(), tmp_path)
    env = dict(os.environ)
    env.update(env_overrides)
    result = subprocess.run(
        ["dotnet", str(a_dll)],
        capture_output=True, text=True, timeout=60, env=env,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


@requires_dotnet_toolchain
def test_chain_runs_the_other_program(dotnet_backend, tmp_path):
    out = _compile_two_and_run_first(
        dotnet_backend, tmp_path,
        'PRINT "in A"\nCHAIN "B"\nEND\n',
        'PRINT "in B"\nEND\n',
    )
    assert out.splitlines() == ["in A", "in B"]


@requires_dotnet_toolchain
def test_chain_hands_over_a_resident_integer(dotnet_backend, tmp_path):
    # A sets A%; the CHAINed B reads it back -- the resident crosses the boundary.
    out = _compile_two_and_run_first(
        dotnet_backend, tmp_path,
        'A%=42\nCHAIN "B"\nEND\n',
        'IF A%=42 THEN PRINT "got 42" ELSE PRINT "lost it"\nEND\n',
    )
    assert out.splitlines() == ["got 42"]


@requires_dotnet_toolchain
def test_chain_does_not_pass_ordinary_variables(dotnet_backend, tmp_path):
    # name$ is an ordinary variable, not a resident: it must NOT cross. B sees the
    # empty default, not A's value.
    out = _compile_two_and_run_first(
        dotnet_backend, tmp_path,
        'name$="alice"\nCHAIN "B"\nEND\n',
        'IF name$="" THEN PRINT "fresh" ELSE PRINT "leaked"\nEND\n',
    )
    assert out.splitlines() == ["fresh"]


@requires_dotnet_toolchain
def test_chain_passes_through_residents_it_never_touched(dotnet_backend, tmp_path):
    # B% is set in A's environment but A never names it; it still reaches the
    # chained program, because the child inherits A's environment.
    out = _compile_two_and_run_first(
        dotnet_backend, tmp_path,
        'A%=1\nCHAIN "B"\nEND\n',
        'PRINT B%\nEND\n',
        OWL_BASIC_RESIDENT_B="7",
    )
    assert out.strip() == "7"


@requires_dotnet_toolchain
def test_chain_hands_over_at_percent(dotnet_backend, tmp_path):
    # @% is resident too: a format set in A is in effect in B.
    out = _compile_two_and_run_first(
        dotnet_backend, tmp_path,
        '@%=10\nCHAIN "B"\nEND\n',
        'IF @%=10 THEN PRINT "at carried" ELSE PRINT "at lost"\nEND\n',
    )
    assert out.splitlines() == ["at carried"]


@requires_dotnet_toolchain
def test_chain_propagates_the_chained_programs_exit(dotnet_backend, tmp_path):
    # B errors (unhandled SQR of a negative); A must exit non-zero, because CHAIN
    # exits with the chained program's status rather than swallowing it.
    a_dll = dotnet_backend.generate(analyse('CHAIN "B"\nEND\n', name="A"), tmp_path)
    dotnet_backend.generate(analyse('B=SQR(-1)\nEND\n', name="B"), tmp_path)
    shutil.copy(find_owlruntime_dll(), tmp_path)
    result = subprocess.run(["dotnet", str(a_dll)], capture_output=True, text=True,
                            timeout=60)
    assert result.returncode != 0
