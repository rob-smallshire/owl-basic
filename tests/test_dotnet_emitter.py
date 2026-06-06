"""The dotnet backend's textual-CIL emitter.

The CIL-text generation runs everywhere (pure Python). The compile-and-run test
is skipped unless the full .NET toolchain is present: ``dotnet``, a CoreCLR
``ilasm`` (the runtime.<rid>.Microsoft.NETCore.ILAsm NuGet package), and a
freshly built net10 ``OwlRuntime.dll``.
"""

import glob
import os
import shutil
import subprocess

import pytest

from owl_basic.analysis import analyse
from owl_basic.ext.backends.dotnet.backend import Backend as DotnetBackend
from owl_basic.extension import create_extension

HERE = os.path.dirname(os.path.abspath(__file__))


def _analyse(filename):
    with open(os.path.join(HERE, filename), encoding="latin-1") as f:
        source = f.read()
    name = os.path.splitext(os.path.basename(filename))[0]
    return analyse(source, name=name)


def _backend():
    return create_extension("backend", "owl_basic.backend", "dotnet")


def _find_owlruntime_dll():
    pattern = os.path.join(
        HERE, "..", "OwlRuntime", "OwlRuntime", "bin", "**", "net10.0", "OwlRuntime.dll"
    )
    matches = glob.glob(pattern, recursive=True)
    return matches[0] if matches else None


def test_emit_il_lowers_print_and_arithmetic():
    il = _backend().emit_il(_analyse("six_times_seven.bbctxt"))
    assert 'ldstr "Bah!"' in il
    assert "[OwlRuntime]OwlRuntime.BasicCommands::Print(string)" in il
    assert "ldc.i4 6" in il
    assert "ldc.i4 7" in il
    assert "\n        mul" in il
    assert "[OwlRuntime]OwlRuntime.BasicCommands::Print(int32)" in il
    assert ".entrypoint" in il


_toolchain_ready = (
    shutil.which("dotnet") is not None
    and DotnetBackend.find_ilasm() is not None
    and _find_owlruntime_dll() is not None
)


@pytest.mark.skipif(
    not _toolchain_ready,
    reason="needs dotnet, a CoreCLR ilasm, and a built net10 OwlRuntime.dll",
)
def test_six_times_seven_compiles_and_runs(tmp_path):
    dll_filepath = _backend().generate(_analyse("six_times_seven.bbctxt"), tmp_path)
    shutil.copy(_find_owlruntime_dll(), tmp_path)  # runtime alongside the program
    result = subprocess.run(
        ["dotnet", str(dll_filepath)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    # The computed value reaches stdout (BBC BASIC: PRINT "..." 6*7).
    assert "Six times seven is 42" in result.stdout
