"""Byte-level file I/O: OPENOUT/OPENIN/OPENUP, BPUT, BGET, CLOSE, EOF.

Until now the Channel operand (`#ch`) was never typed (so every file statement
failed type-checking), the emitter had no lowering for any of these, and the
runtime's Bput/Bget/Close had an inverted channel check. These exercise the whole
path end to end, and -- the point -- that data written with BPUT reads back with
BGET (a genuine round-trip through a file).
"""
import shutil
import subprocess

from conftest import requires_dotnet_toolchain
from helpers import find_owlruntime_dll

from owl_basic.analysis import analyse


def _run(dotnet_backend, tmp_path, source):
    # cwd=tmp_path so the program's file lands in the isolated test directory.
    dll_filepath = dotnet_backend.generate(analyse(source, name="fio"), tmp_path)
    shutil.copy(find_owlruntime_dll(), tmp_path)
    result = subprocess.run(
        ["dotnet", str(dll_filepath)],
        capture_output=True, text=True, timeout=30, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    return result.stdout


@requires_dotnet_toolchain
def test_bput_bget_byte_round_trip(dotnet_backend, tmp_path):
    out = _run(dotnet_backend, tmp_path,
               'f%=OPENOUT("rt.dat")\nBPUT#f%,65\nBPUT#f%,66\nBPUT#f%,67\nCLOSE#f%\n'
               'g%=OPENIN("rt.dat")\nPRINT BGET#g%\nPRINT BGET#g%\nPRINT BGET#g%\n'
               'CLOSE#g%\nEND\n')
    assert out.split() == ["65", "66", "67"]


@requires_dotnet_toolchain
def test_bput_wraps_to_a_byte(dotnet_backend, tmp_path):
    # BPUT writes the low byte: 321 AND 255 = 65.
    out = _run(dotnet_backend, tmp_path,
               'f%=OPENOUT("w.dat")\nBPUT#f%,321\nCLOSE#f%\n'
               'g%=OPENIN("w.dat")\nPRINT BGET#g%\nCLOSE#g%\nEND\n')
    assert out.strip() == "65"


@requires_dotnet_toolchain
def test_eof_terminates_a_read_loop(dotnet_backend, tmp_path):
    # Write 3 bytes, read until EOF -- the canonical copy idiom. EOF#ch is TRUE
    # (-1) at end of file.
    out = _run(dotnet_backend, tmp_path,
               'f%=OPENOUT("e.dat")\nFOR I%=1 TO 3\nBPUT#f%,I%*10\nNEXT\nCLOSE#f%\n'
               'g%=OPENIN("e.dat")\n'
               'REPEAT\nb%=BGET#g%\nPRINT b%\nUNTIL EOF#g%\nCLOSE#g%\nEND\n')
    assert out.split() == ["10", "20", "30"]


@requires_dotnet_toolchain
def test_openup_reads_and_writes(dotnet_backend, tmp_path):
    # OPENUP opens an existing file for update (read+write).
    out = _run(dotnet_backend, tmp_path,
               'f%=OPENOUT("u.dat")\nBPUT#f%,99\nCLOSE#f%\n'
               'g%=OPENUP("u.dat")\nPRINT BGET#g%\nCLOSE#g%\nEND\n')
    assert out.strip() == "99"
