"""Resident integers (@%, A%-Z%) are preserved across RUN/CHAIN and seeded from
the environment at process start.

BBC BASIC keeps @% and A%-Z% alive through NEW/OLD/CLEAR/RUN/CHAIN -- the
documented channel for passing data into a CHAINed program (see the BASIC II
program-lifecycle analysis). OWL models this by seeding them once at startup from
OWL_BASIC_RESIDENT_<name> (A..Z, and AT for @%), defaulting to 0 / the existing
format when unset, and excluding them from the RUN clear (__reset). This is the
foundation CHAIN hands values across; here it is exercised directly through the
environment, with no CHAIN involved.
"""
import os
import shutil
import subprocess

from conftest import requires_dotnet_toolchain
from helpers import find_owlruntime_dll

from owl_basic.analysis import analyse


def _run(dotnet_backend, tmp_path, source, **env_overrides):
    program = analyse(source, name="res")
    dll_filepath = dotnet_backend.generate(program, tmp_path)
    shutil.copy(find_owlruntime_dll(), tmp_path)
    env = dict(os.environ)
    env.update(env_overrides)
    result = subprocess.run(
        ["dotnet", str(dll_filepath)],
        capture_output=True, text=True, timeout=30, env=env,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


@requires_dotnet_toolchain
def test_resident_integer_seeded_from_environment(dotnet_backend, tmp_path):
    # A% picks up OWL_BASIC_RESIDENT_A. Compared by value to dodge @% formatting.
    out = _run(dotnet_backend, tmp_path,
               'IF A%=42 THEN PRINT "ok" ELSE PRINT "no"\nEND\n',
               OWL_BASIC_RESIDENT_A="42")
    assert out.splitlines() == ["ok"]


@requires_dotnet_toolchain
def test_resident_integer_defaults_to_zero_when_unset(dotnet_backend, tmp_path):
    # No environment variable -> the BBC default of 0 (residents start zeroed).
    out = _run(dotnet_backend, tmp_path,
               'IF A%=0 THEN PRINT "zero" ELSE PRINT "no"\nEND\n',
               OWL_BASIC_RESIDENT_A="")
    assert out.splitlines() == ["zero"]


@requires_dotnet_toolchain
def test_several_residents_seeded_independently(dotnet_backend, tmp_path):
    out = _run(dotnet_backend, tmp_path,
               'PRINT A%+B%+Z%\nEND\n',
               OWL_BASIC_RESIDENT_A="1", OWL_BASIC_RESIDENT_B="2",
               OWL_BASIC_RESIDENT_Z="100")
    assert out.strip() == "103"


@requires_dotnet_toolchain
def test_at_percent_seeded_from_environment(dotnet_backend, tmp_path):
    # @% is resident too, carried on OWL_BASIC_RESIDENT_AT. Read its value back.
    out = _run(dotnet_backend, tmp_path,
               'IF @%=10 THEN PRINT "atok" ELSE PRINT "no"\nEND\n',
               OWL_BASIC_RESIDENT_AT="10")
    assert out.splitlines() == ["atok"]


@requires_dotnet_toolchain
def test_at_percent_unset_keeps_its_default_format(dotnet_backend, tmp_path):
    # An absent OWL_BASIC_RESIDENT_AT must not zero @% -- its default format is
    # non-zero, so a plain integer still prints without a thousands separator etc.
    out = _run(dotnet_backend, tmp_path, 'PRINT 42\nEND\n', OWL_BASIC_RESIDENT_AT="")
    assert out.strip() == "42"


def _method_body(il, name):
    """The IL text of the named method, from its `.method` line to its closing
    brace, so an assertion targets that method rather than a prologue call."""
    start = il.index(".method static void %s()" % name)
    end = il.index("\n}", start)
    return il[start:end]


def test_reset_does_not_clear_resident_integers(dotnet_backend):
    # __reset is the RUN clear; residents must survive it, so it must not store a
    # default into i_A. __seed_residents seeds it instead. Pins the exclusion
    # without needing to actually RUN (which would loop).
    # A% is a resident (single letter); total% is an ordinary global. (Every
    # single-letter %-variable A%-Z% is resident, so the contrast needs a
    # multi-character name.)
    program = analyse('A%=A%+1\ntotal%=5\nPRINT A%\nEND\n', name="resil")
    il = dotnet_backend.emit_il(program)
    reset = _method_body(il, "__reset")
    assert "stsfld int32 i_A" not in reset        # A% is a resident: not reset
    assert "stsfld int32 i_total" in reset         # total% is ordinary: reset
    # ...and a dedicated method seeds the resident from the environment.
    seed = _method_body(il, "__seed_residents")
    assert 'ldstr "A"' in seed
    assert "SeedResident" in seed
    assert "stsfld int32 i_A" in seed
    assert "SeedAtPercent" in seed
