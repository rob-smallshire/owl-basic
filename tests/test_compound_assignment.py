"""+= and -= (compound assignment), WAIT, and the remaining deferred nodes.

`A += B` / `A -= B` are simple: they desugar to `A = A + B` / `A = A - B`,
reusing the assignment and binary-operator machinery (so string `+=` is
concatenation and numeric casts are inserted as usual). WAIT is a no-op on the
headless console (it waits for vertical sync, which has no meaning here). The
graphics/sound statements that remain unimplemented (LINE, POINT, ORIGIN, ...)
lower to a loud runtime stub like the other deferred features.
"""
import shutil
import subprocess

import pytest

from conftest import requires_dotnet_toolchain
from helpers import find_owlruntime_dll

from owl_basic.analysis import analyse


@requires_dotnet_toolchain
def test_increment_integer(compile_and_run):
    out = compile_and_run(analyse("n%=5\nn%+=3\nPRINT n%\n", name="t"))
    assert out.strip() == "8"


@requires_dotnet_toolchain
def test_decrement_float(compile_and_run):
    out = compile_and_run(analyse("n=10\nn-=4\nPRINT n\n", name="t"))
    assert out.strip() == "6"


@requires_dotnet_toolchain
def test_increment_string_concatenates(compile_and_run):
    out = compile_and_run(analyse('s$="foo"\ns$+="bar"\nPRINT s$\n', name="t"))
    assert out.strip() == "foobar"


@requires_dotnet_toolchain
def test_wait_is_a_noop(compile_and_run):
    out = compile_and_run(analyse('PRINT "before"\nWAIT\nPRINT "after"\n', name="t"))
    assert out.split() == ["before", "after"]


@requires_dotnet_toolchain
def test_line_compiles_and_fails_only_when_reached(compile_and_run):
    out = compile_and_run(analyse(
        'PRINT "ok"\nIF FALSE THEN LINE 0,0,100,100\n', name="t"))
    assert out.strip() == "ok"


@requires_dotnet_toolchain
def test_line_reached_fails_noisily(dotnet_backend, tmp_path):
    dll = dotnet_backend.generate(analyse("LINE 0,0,100,100\nEND\n", name="t"), tmp_path)
    shutil.copy(find_owlruntime_dll(), tmp_path)
    result = subprocess.run(["dotnet", str(dll)], capture_output=True, text=True,
                            timeout=30, cwd=tmp_path)
    assert result.returncode != 0
    assert "not yet implemented" in (result.stderr + result.stdout).lower()
