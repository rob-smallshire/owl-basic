"""The bare ON / OFF cursor-control statements: compile, but deferred at runtime.

In BBC BASIC V a bare OFF turns the text cursor off and a bare ON turns it back
on -- programs typically OFF the cursor while drawing and ON it again at the end
(Acorn User Tau92-a/FEB92.Verhul does exactly this: OFF at line 60, ON at line
360). ON had no backend lowering at all, so the program could not be compiled.
Neither is implemented on the headless renderer, so both lower to a loud runtime
stub (NotImplemented): the program compiles and runs until -- if ever -- it
reaches the cursor statement. ON ERROR OFF is a separate construct, unaffected.
"""
import shutil
import subprocess

import pytest

from conftest import requires_dotnet_toolchain
from helpers import find_owlruntime_dll

from owl_basic.analysis import analyse


def test_cursor_on_off_compile_to_a_deferred_stub(dotnet_backend):
    # The Verhul shape compiles; the cursor statements lower to a deferred
    # (throwing) runtime call rather than being dropped or refusing to compile.
    il = dotnet_backend.emit_il(analyse(
        'OFF\nPRINT "drawing"\nON\nEND\n', name="t"))
    assert il
    assert "NotImplemented" in il


def test_on_error_off_still_compiles(dotnet_backend):
    # ON ERROR OFF disables the handler -- it must not be confused with bare ON/OFF.
    il = dotnet_backend.emit_il(analyse(
        'ON ERROR OFF\nPRINT "ok"\nEND\n', name="t"))
    assert il


@requires_dotnet_toolchain
def test_cursor_statement_compiles_and_fails_only_when_reached(compile_and_run):
    # Guarded behind IF FALSE: never reached, so the program runs to completion.
    out = compile_and_run(analyse(
        'PRINT "ok"\nIF FALSE THEN OFF\n', name="t"))
    assert out.strip() == "ok"


@requires_dotnet_toolchain
def test_cursor_statement_reached_fails_noisily(dotnet_backend, tmp_path):
    dll = dotnet_backend.generate(analyse("OFF\nEND\n", name="t"), tmp_path)
    shutil.copy(find_owlruntime_dll(), tmp_path)
    result = subprocess.run(["dotnet", str(dll)], capture_output=True, text=True,
                            timeout=30, cwd=tmp_path)
    assert result.returncode != 0
