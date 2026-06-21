"""USR calls native machine code, which cannot run on .NET.

`USR addr` enters a 6502 machine-code routine at an address and returns the CPU
registers -- inherently machine-specific, like an inline assembler block or a
CALL. OWL targets .NET CIL with no 6502 to run, so a program using USR is
rejected with a clear message naming machine code -- rather than the opaque
"Syntax error at 'USR'" it produced before (USR is a token but has no grammar
production, so it fell through to a parse error).
"""
import pytest

from owl_basic.analysis import analyse
from owl_basic.exceptions import CompileError


def test_usr_is_rejected_with_a_clear_message():
    with pytest.raises(CompileError) as excinfo:
        analyse("A=USR&FFF4\nEND\n", name="t")
    message = str(excinfo.value).lower()
    assert "usr" in message
    assert "machine code" in message


def test_usr_in_a_larger_expression_is_rejected_not_a_parse_error():
    # The corpus shape: =((USR&FFF4 AND &FF00)DIV &100<>79) inside a DEF FN.
    # The diagnostic must name USR/machine code, not be a bare syntax error.
    with pytest.raises(CompileError) as excinfo:
        analyse("DEF FNk=((USR&FFF4 AND &FF00)DIV &100<>79)\n", name="t")
    message = str(excinfo.value).lower()
    assert "usr" in message
    assert "syntax error" not in message


def test_usrfle_variable_is_not_a_false_positive():
    # USR is non-conditional in the ROM, so USRFLE tokenises as USR + FLE -- you
    # cannot name a variable USRFLE in BBC BASIC. The reverse, a variable that
    # merely contains "usr" lower-case or after a name char, must not trip the
    # rejection. `MUSR` is one identifier (USR only matches at a name-run start).
    program = analyse("MUSR=1\nPRINT MUSR\n", name="t")
    assert program is not None
