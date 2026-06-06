"""Shared pytest fixtures and markers for OWL BASIC tests.

Pure helper functions live in the ``helpers`` package; this module wires the
.NET toolchain dependency and a compile-and-run fixture used by the backend
tests.
"""

import shutil
import subprocess

import pytest

from owl_basic.ext.backends.dotnet.backend import Backend as DotnetBackend
from owl_basic.extension import create_extension

from helpers import find_owlruntime_dll

TOOLCHAIN_READY = (
    shutil.which("dotnet") is not None
    and DotnetBackend.find_ilasm() is not None
    and find_owlruntime_dll() is not None
)

# Apply to tests that assemble and run a generated assembly.
requires_dotnet_toolchain = pytest.mark.skipif(
    not TOOLCHAIN_READY,
    reason="needs dotnet, a CoreCLR ilasm, and a built net10 OwlRuntime.dll",
)


@pytest.fixture
def dotnet_backend():
    """The discoverable ``dotnet`` backend extension."""
    return create_extension("backend", "owl_basic.backend", "dotnet")


@pytest.fixture
def compile_and_run(dotnet_backend, tmp_path):
    """Return a function that compiles an analysed Program and runs it.

    The function generates the assembly into a temp directory beside a copy of
    ``OwlRuntime.dll``, runs it with ``dotnet``, asserts a clean exit and
    returns the program's standard output.
    """

    def run(program, stdin=None):
        dll_filepath = dotnet_backend.generate(program, tmp_path)
        shutil.copy(find_owlruntime_dll(), tmp_path)
        result = subprocess.run(
            ["dotnet", str(dll_filepath)],
            input=stdin, capture_output=True, text=True
        )
        assert result.returncode == 0, result.stderr
        return result.stdout

    return run
