"""Shared pytest fixtures and markers for OWL BASIC tests.

Pure helper functions live in the ``helpers`` package; this module wires the
.NET toolchain dependency and a compile-and-run fixture used by the backend
tests.
"""

import os
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


def pytest_addoption(parser):
    parser.addoption(
        "--runslow", action="store_true", default=False,
        help="run slow tests (e.g. the full Sphinx Adventure playthroughs)",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "slow: a long-running test (minutes), skipped unless --runslow is given",
    )


def pytest_collection_modifyitems(config, items):
    # The Sphinx playthroughs drive the whole game interactively and take a
    # couple of minutes between them, dwarfing the rest of the suite. Skip
    # anything marked `slow` unless the run opts in with --runslow (CI does).
    if config.getoption("--runslow"):
        return
    skip_slow = pytest.mark.skip(reason="slow; pass --runslow to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


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

    def run(program, stdin=None, timeout=None):
        dll_filepath = dotnet_backend.generate(program, tmp_path)
        shutil.copy(find_owlruntime_dll(), tmp_path)
        result = subprocess.run(
            ["dotnet", str(dll_filepath)],
            input=stdin, capture_output=True, text=True, timeout=timeout
        )
        assert result.returncode == 0, result.stderr
        return result.stdout

    return run


@pytest.fixture
def compile_and_capture_screen(dotnet_backend, tmp_path):
    """Like ``compile_and_run``, but runs with the grid-capturing screen mode
    (OWL_CAPTURE_SCREEN), so the returned string is the laid-out 80x25 text
    screen -- TAB(x,y) positioning and scrolling honoured -- rather than the
    streamed output. Useful for checking text formatting/layout.
    """

    def run(program, stdin=None, timeout=None):
        dll_filepath = dotnet_backend.generate(program, tmp_path)
        shutil.copy(find_owlruntime_dll(), tmp_path)
        env = dict(os.environ)
        env["OWL_CAPTURE_SCREEN"] = "1"
        result = subprocess.run(
            ["dotnet", str(dll_filepath)],
            input=stdin, capture_output=True, text=True, timeout=timeout, env=env
        )
        assert result.returncode == 0, result.stderr
        return result.stdout

    return run


@pytest.fixture
def compile_expecting_error(dotnet_backend, tmp_path):
    """Compile and run a program that is expected to fail at runtime.

    Asserts a non-zero exit and returns the combined stdout+stderr, so a test
    can check the program errored cleanly (rather than corrupting state) and,
    where relevant, name the error.
    """

    def run(program, stdin=None):
        dll_filepath = dotnet_backend.generate(program, tmp_path)
        shutil.copy(find_owlruntime_dll(), tmp_path)
        result = subprocess.run(
            ["dotnet", str(dll_filepath)],
            input=stdin, capture_output=True, text=True
        )
        assert result.returncode != 0, (
            "expected a runtime error but the program exited cleanly:\n"
            + result.stdout
        )
        return result.stdout + result.stderr

    return run
