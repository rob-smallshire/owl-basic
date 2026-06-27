"""CALL, USR and SYS are backend-specific (like inline assembler).

Whether these compile is a backend decision, not a frontend one: the frontend
parses each into a neutral AST node and never rejects it, and the dotnet backend
rejects it at code generation with a clear, self-naming message (it cannot run
6502/ARM machine code, and has no SWI mechanism). A bbc-micro-6502 backend would
compile all three. See docs/backend-specific-constructs.md.
"""
import pytest

from owl_basic.analysis import analyse
from owl_basic.exceptions import OwlBasicError


def _emit(source, dotnet_backend):
    return dotnet_backend.emit_il(analyse(source, name="t"))


# -- the frontend parses them (no frontend rejection) ----------------------

def test_usr_parses_in_the_frontend():
    program = analyse("X%=USR(&FFEE)\nEND\n", name="t")
    assert program is not None


def test_sys_parses_in_the_frontend():
    program = analyse('SYS "OS_Byte",19\nEND\n', name="t")
    assert program is not None


def test_call_parses_in_the_frontend():
    program = analyse("CALL &FFEE\nEND\n", name="t")
    assert program is not None


# -- the dotnet backend rejects them clearly at code generation ------------

def test_usr_rejected_by_dotnet_backend(dotnet_backend):
    with pytest.raises(OwlBasicError) as excinfo:
        _emit("X%=USR(&FFEE)\nEND\n", dotnet_backend)
    message = str(excinfo.value).lower()
    assert "usr" in message and "dotnet backend" in message


def test_sys_rejected_by_dotnet_backend(dotnet_backend):
    with pytest.raises(OwlBasicError) as excinfo:
        _emit('SYS "OS_Byte",19\nEND\n', dotnet_backend)
    message = str(excinfo.value).lower()
    assert "sys" in message and "dotnet backend" in message


def test_call_rejected_by_dotnet_backend(dotnet_backend):
    with pytest.raises(OwlBasicError) as excinfo:
        _emit("CALL &FFEE\nEND\n", dotnet_backend)
    message = str(excinfo.value).lower()
    assert "call" in message and "dotnet backend" in message
