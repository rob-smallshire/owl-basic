"""POINT(x, y) compiles to a runtime stub that raises -- it does not block the
compile.

Reading the screen back (the logical colour at a graphics coordinate) is not yet
implemented. Rather than fail to lower the whole program (which stopped graphics
programs such as the db825 IFS fractal from compiling at all), POINT lowers to a
call to an OwlRuntime stub that raises at run time. So the program compiles, but
raises if it actually evaluates a POINT.
"""
import shutil
import subprocess

import pytest

from conftest import requires_dotnet_toolchain
from owl_basic.analysis import analyse
from helpers import find_owlruntime_dll


def test_point_lowers_to_a_runtime_call(dotnet_backend):
    il = dotnet_backend.emit_il(analyse("A%=POINT(10,20)\nPRINT A%\n", name="t"))
    assert "BasicCommands::Point(int32, int32)" in il


@requires_dotnet_toolchain
def test_point_program_compiles_but_raises_at_runtime(dotnet_backend, tmp_path):
    # It must assemble and run -- and the run must fail (the stub raises), not
    # exit cleanly, and not fail to compile.
    dll_filepath = dotnet_backend.generate(
        analyse("A%=POINT(10,20)\nPRINT A%\n", name="t"), tmp_path
    )
    shutil.copy(find_owlruntime_dll(), tmp_path)
    result = subprocess.run(
        ["dotnet", str(dll_filepath)], capture_output=True, text=True, timeout=30
    )
    assert result.returncode != 0
    assert "not yet implemented" in result.stderr
