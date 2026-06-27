"""USR calls native machine code -- a backend decision, like CALL and assembler.

`USR addr` enters a machine-code routine at an address and returns a value. That
is target-specific: a bbc-micro-6502 backend would compile it, the dotnet backend
cannot (no 6502 to run). So the frontend parses USR into a neutral node and never
rejects it; the dotnet backend rejects it at code generation with a clear,
self-naming message. See docs/backend-specific-constructs.md.
"""
import pytest

from owl_basic.analysis import analyse
from owl_basic.exceptions import OwlBasicError


def _emit(source, dotnet_backend):
    return dotnet_backend.emit_il(analyse(source, name="t"))


def test_usr_parses_then_rejected_at_codegen(dotnet_backend):
    # No frontend rejection (that was the layering bug); the dotnet backend
    # rejects it clearly at code generation.
    assert analyse("A=USR&FFF4\nEND\n", name="t") is not None
    with pytest.raises(OwlBasicError) as excinfo:
        _emit("A=USR&FFF4\nEND\n", dotnet_backend)
    message = str(excinfo.value).lower()
    assert "usr" in message and "dotnet backend" in message


def test_usr_in_a_larger_expression_is_not_a_parse_error(dotnet_backend):
    # The corpus shape: =((USR&FFF4 AND &FF00)DIV &100<>79) inside a DEF FN. It
    # must parse (USR is a real expression now), then be rejected by the backend
    # -- not a bare syntax error.
    source = "DEF FNk=((USR&FFF4 AND &FF00)DIV &100<>79)\n"
    assert analyse(source, name="t") is not None
    with pytest.raises(OwlBasicError) as excinfo:
        _emit(source, dotnet_backend)
    assert "syntax error" not in str(excinfo.value).lower()


def test_usrfle_variable_is_not_a_false_positive():
    # USR is non-conditional in the ROM, so USRFLE tokenises as USR + FLE -- you
    # cannot name a variable USRFLE in BBC BASIC. The reverse, a variable that
    # merely contains "usr" after a name char, must not trip USR. `MUSR` is one
    # identifier (USR only matches at a name-run start).
    program = analyse("MUSR=1\nPRINT MUSR\n", name="t")
    assert program is not None
