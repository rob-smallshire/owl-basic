"""Typed file records: PRINT# / INPUT# (and string BPUT, PTR#).

PRINT# does not write text -- it writes BASIC's private type-tagged, byte-reversed
record format: an integer is &40 + 4 bytes MSB-first, a real is &FF + 5 reversed
float5 bytes (exponent last), a string is &00 + a length byte + the characters
reversed. INPUT# is the exact mirror: it validates the tag (Type mismatch on the
wrong one -- it does NOT coerce) and undoes the reversal.

These exercise the whole path end to end: that values round-trip PRINT#->INPUT#,
and -- the real point of "the format is private to BASIC" -- that the bytes OWL
writes are read back identically by oaknut-basic's BbcBasicDataReader (and vice
versa), so OWL data files interoperate with real BBC files and the oaknut CLI.
"""
import shutil
import struct
import subprocess

import oaknut.basic.datafile as datafile
import pytest
from conftest import requires_dotnet_toolchain
from helpers import find_owlruntime_dll

from owl_basic.analysis import analyse


def _run(dotnet_backend, tmp_path, source):
    # cwd=tmp_path so the program's data file lands in the isolated test directory.
    dll_filepath = dotnet_backend.generate(analyse(source, name="pif"), tmp_path)
    shutil.copy(find_owlruntime_dll(), tmp_path)
    result = subprocess.run(
        ["dotnet", str(dll_filepath)],
        capture_output=True, text=True, timeout=30, cwd=tmp_path)
    return result


def _run_ok(dotnet_backend, tmp_path, source):
    result = _run(dotnet_backend, tmp_path, source)
    assert result.returncode == 0, result.stderr
    return result.stdout


# -- round trips through OWL's own PRINT# / INPUT# --------------------------

@requires_dotnet_toolchain
def test_integer_record_round_trips(dotnet_backend, tmp_path):
    out = _run_ok(dotnet_backend, tmp_path,
                  'f%=OPENOUT("i.dat")\nPRINT#f%,&12345678\nCLOSE#f%\n'
                  'g%=OPENIN("i.dat")\nn%=0\nINPUT#g%,n%\nPRINT ~n%\nCLOSE#g%\nEND\n')
    assert out.strip() == "12345678"


@requires_dotnet_toolchain
def test_string_record_round_trips(dotnet_backend, tmp_path):
    out = _run_ok(dotnet_backend, tmp_path,
                  'f%=OPENOUT("s.dat")\nPRINT#f%,"HELLO WORLD"\nCLOSE#f%\n'
                  'g%=OPENIN("s.dat")\na$=""\nINPUT#g%,a$\nPRINT a$\nCLOSE#g%\nEND\n')
    assert out.strip() == "HELLO WORLD"


@requires_dotnet_toolchain
def test_real_record_round_trips(dotnet_backend, tmp_path):
    out = _run_ok(dotnet_backend, tmp_path,
                  'f%=OPENOUT("r.dat")\nPRINT#f%,3.5\nCLOSE#f%\n'
                  'g%=OPENIN("r.dat")\nr=0\nINPUT#g%,r\nPRINT r\nCLOSE#g%\nEND\n')
    assert out.strip() == "3.5"


@requires_dotnet_toolchain
def test_mixed_record_list_round_trips(dotnet_backend, tmp_path):
    # PRINT# walks a comma-separated list; INPUT# reads them back in order, each
    # tag matching its target's type.
    out = _run_ok(dotnet_backend, tmp_path,
                  'f%=OPENOUT("m.dat")\nPRINT#f%,42,"two",3.25\nCLOSE#f%\n'
                  'g%=OPENIN("m.dat")\nn%=0\nb$=""\nc=0\n'
                  'INPUT#g%,n%,b$,c\nPRINT n%\nPRINT b$\nPRINT c\nCLOSE#g%\nEND\n')
    assert out.split("\n")[:3] == ["42", "two", "3.25"]


# -- interop with oaknut-basic's data-file codec ---------------------------

@requires_dotnet_toolchain
def test_owl_print_is_read_by_oaknut(dotnet_backend, tmp_path):
    # The bytes OWL writes must be exactly BASIC's format: read them back with
    # oaknut's reader and check the values (and the raw byte framing).
    _run_ok(dotnet_backend, tmp_path,
            'f%=OPENOUT("o.dat")\nPRINT#f%,42,"AB",1.0\nCLOSE#f%\nEND\n')
    raw = (tmp_path / "o.dat").read_bytes()
    assert raw[:5] == bytes([0x40, 0x00, 0x00, 0x00, 0x2A])      # 42
    assert raw[5:9] == bytes([0x00, 0x02, ord("B"), ord("A")])   # "AB" reversed
    assert raw[9:15] == bytes([0xFF, 0x00, 0x00, 0x00, 0x00, 0x81])  # 1.0
    with datafile.open(str(tmp_path / "o.dat"), "r") as f:
        assert f.read_int() == 42
        assert f.read_str() == "AB"
        assert f.read_float() == 1.0


@requires_dotnet_toolchain
def test_negative_real_packs_the_sign_bit(dotnet_backend, tmp_path):
    # The float5 sign bit lands in the 4th data byte on the wire (exponent last):
    # -1.0 -> FF 00 00 00 80 81 (cf. the BBC BASIC II disassembly worked example).
    _run_ok(dotnet_backend, tmp_path,
            'f%=OPENOUT("n.dat")\nPRINT#f%,-1.0\nCLOSE#f%\nEND\n')
    assert (tmp_path / "n.dat").read_bytes() == bytes([0xFF, 0x00, 0x00, 0x00, 0x80, 0x81])
    with datafile.open(str(tmp_path / "n.dat"), "r") as f:
        assert f.read_float() == -1.0


@requires_dotnet_toolchain
def test_oaknut_write_is_read_by_owl_input(dotnet_backend, tmp_path):
    # The mirror: a file written by oaknut is read back correctly by INPUT#.
    with datafile.open(str(tmp_path / "k.dat"), "w") as f:
        f.write_int(1234)
        f.write_str("oaknut")
        f.write_float(2.718281828)
    out = _run_ok(dotnet_backend, tmp_path,
                  'g%=OPENIN("k.dat")\nn%=0\ns$=""\nr=0\n'
                  'INPUT#g%,n%,s$,r\nPRINT n%\nPRINT s$\nPRINT r\nCLOSE#g%\nEND\n')
    lines = out.split("\n")
    assert lines[0] == "1234"
    assert lines[1] == "oaknut"
    assert abs(float(lines[2]) - 2.718281828) < 1e-6


# -- INPUT# validates the tag; it does not coerce --------------------------

@requires_dotnet_toolchain
def test_input_type_mismatch_is_an_error(dotnet_backend, tmp_path):
    # An integer record read into a string variable is a Type mismatch, not a
    # silent coercion: the program must fail rather than read garbage.
    result = _run(dotnet_backend, tmp_path,
                  'f%=OPENOUT("t.dat")\nPRINT#f%,42\nCLOSE#f%\n'
                  'g%=OPENIN("t.dat")\na$=""\nINPUT#g%,a$\nCLOSE#g%\nEND\n')
    assert result.returncode != 0
    assert "mismatch" in result.stderr.lower() or "mismatch" in result.stdout.lower()


# -- string BPUT and PTR# --------------------------------------------------

@requires_dotnet_toolchain
def test_string_bput_writes_the_bytes(dotnet_backend, tmp_path):
    # BPUT#ch, A$ writes the string's bytes (a trailing newline unless `;`).
    _run_ok(dotnet_backend, tmp_path,
            'f%=OPENOUT("b.dat")\nBPUT#f%,"AB";\nCLOSE#f%\nEND\n')
    assert (tmp_path / "b.dat").read_bytes() == b"AB"


@requires_dotnet_toolchain
def test_ptr_allows_random_access(dotnet_backend, tmp_path):
    # PTR#ch = n rewinds an OPENUP channel; the next BGET reads at that position.
    out = _run_ok(dotnet_backend, tmp_path,
                  'f%=OPENOUT("p.dat")\nBPUT#f%,10\nBPUT#f%,20\nBPUT#f%,30\nCLOSE#f%\n'
                  'g%=OPENUP("p.dat")\nPTR#g%=1\nPRINT BGET#g%\nPRINT PTR#g%\nCLOSE#g%\nEND\n')
    assert out.split()[:2] == ["20", "2"]
