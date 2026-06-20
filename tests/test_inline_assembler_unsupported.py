"""Inline 6502 assembler ([ ... ]) cannot be compiled to .NET.

BBC BASIC embeds 6502 machine code between `[` and `]`. OWL targets .NET CIL and
has no 6502 to run, so an assembler block is rejected with a clear message naming
inline assembly -- rather than a bare "Syntax error at '['".
"""
import pytest

from owl_basic.analysis import analyse
from owl_basic.exceptions import CompileError


def test_inline_assembler_block_is_rejected():
    with pytest.raises(CompileError) as excinfo:
        analyse("P%=0\n[OPT0:LDA#42:RTS:]\n", name="t")
    message = str(excinfo.value).lower()
    assert "assembl" in message


def test_assembler_on_one_line_with_other_statements_is_rejected():
    with pytest.raises(CompileError):
        analyse('S$="x":P%=0:[OPT0:RTS:]\n', name="t")
