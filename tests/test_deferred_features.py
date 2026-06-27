"""Backend features: the simple ones implemented, the complex ones deferred.

Several BBC BASIC constructs analyse and type-check but had no backend lowering,
so a program using any of them could not be compiled at all. The simple ones
(GET$, INKEY$, STOP) are now lowered properly; the complex ones (SOUND,
ENVELOPE, ...) lower to a loud runtime failure, so the program compiles and runs
until -- if ever -- it reaches the unimplemented operation. A compiler gap
("cannot lower node X") becomes a visible runtime library gap.
"""
import pytest

from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse


# -- implemented: GET$ / INKEY$ -------------------------------------------

@requires_dotnet_toolchain
def test_get_str_reads_a_character(compile_and_run):
    # GET$ returns the keypress as a one-character string; feed it on stdin.
    out = compile_and_run(analyse('a$=GET$\nPRINT a$\n', name="t"), stdin="Q")
    assert out.strip() == "Q"


@requires_dotnet_toolchain
def test_inkey_str_times_out_to_empty(compile_and_run):
    # INKEY$(0) with no key waiting returns "" (the stdin is empty).
    out = compile_and_run(analyse('a$=INKEY$(0)\nPRINT "["+a$+"]"\n', name="t"))
    assert out.strip() == "[]"


# -- deferred: compiles, but fails loudly when the op runs -----------------

@requires_dotnet_toolchain
def test_sound_compiles_and_fails_only_when_reached(compile_and_run):
    # The program compiles; SOUND is never reached, so it runs to completion.
    out = compile_and_run(analyse(
        'PRINT "before"\nIF FALSE THEN SOUND 1,-15,100,10\nPRINT "after"\n', name="t"))
    assert out.split() == ["before", "after"]


@requires_dotnet_toolchain
def test_sound_reached_fails_noisily(dotnet_backend, tmp_path):
    # When SOUND actually runs, it raises a clear NotImplemented runtime error
    # rather than having refused to compile.
    import shutil, subprocess
    from helpers import find_owlruntime_dll
    dll = dotnet_backend.generate(analyse('SOUND 1,-15,100,10\nEND\n', name="t"), tmp_path)
    shutil.copy(find_owlruntime_dll(), tmp_path)
    result = subprocess.run(["dotnet", str(dll)], capture_output=True, text=True,
                            timeout=30, cwd=tmp_path)
    assert result.returncode != 0
    combined = (result.stderr + result.stdout).lower()
    assert "sound" in combined and "not yet implemented" in combined


@requires_dotnet_toolchain
def test_envelope_compiles(compile_and_run):
    out = compile_and_run(analyse(
        'PRINT "ok"\nIF FALSE THEN ENVELOPE 1,1,0,0,0,0,0,0,0,0,0,0,126,126\n',
        name="t"))
    assert out.strip() == "ok"
