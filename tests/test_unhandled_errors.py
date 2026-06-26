"""Unhandled runtime errors propagate as .NET exceptions -- not suppressed.

OWL deliberately does NOT catch a BBC runtime error at the program boundary to
print a message and exit cleanly. With no ON ERROR handler installed, the error
surfaces as the underlying .NET exception -- a non-zero process exit with a
stack trace -- so OWL-compiled code stays usable as a library from other .NET
languages, which can catch the exception themselves. A program that wants to
recover uses ON ERROR (see test_on_error.py).

This pins that intent: do not add a boundary catch-all that swallows unhandled
errors.
"""
import shutil
import subprocess

from conftest import requires_dotnet_toolchain
from helpers import find_owlruntime_dll

from owl_basic.analysis import analyse


@requires_dotnet_toolchain
def test_runtime_error_without_on_error_propagates_unhandled(dotnet_backend, tmp_path):
    # SQR(-1) raises NegativeRootException; with no ON ERROR it must reach the
    # process boundary as an unhandled .NET exception, not be turned into a
    # clean print-and-exit-0.
    program = analyse('A = SQR(-1)\nPRINT "after"\nEND\n', name="unh")
    dll_filepath = dotnet_backend.generate(program, tmp_path)
    shutil.copy(find_owlruntime_dll(), tmp_path)
    result = subprocess.run(
        ["dotnet", str(dll_filepath)], capture_output=True, text=True, timeout=30)
    assert result.returncode != 0                    # not a clean exit
    assert "NegativeRootException" in result.stderr  # the real .NET exception
    assert "after" not in result.stdout              # execution stopped at the error
