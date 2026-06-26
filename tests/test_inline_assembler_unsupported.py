"""The dotnet backend cannot compile an inline assembler ([ ... ]) block.

BBC BASIC embeds machine code between `[` and `]`. Recognising the block is a
frontend job (it parses to an opaque InlineAssembler node); whether it can be
compiled is a backend decision. OWL targets .NET CIL with no machine code to
run, so the dotnet backend rejects the block at code generation with a clear
message -- see docs/inline-assembler.md and tests/test_inline_assembler.py.
"""
import pytest

from owl_basic.analysis import analyse
from owl_basic.exceptions import OwlBasicError


def _emit(source, dotnet_backend):
    return dotnet_backend.emit_il(analyse(source, name="t"))


def test_inline_assembler_block_is_rejected(dotnet_backend):
    with pytest.raises(OwlBasicError) as excinfo:
        _emit("P%=0\n[OPT0:LDA#42:RTS:]\n", dotnet_backend)
    assert "assembl" in str(excinfo.value).lower()


def test_assembler_on_one_line_with_other_statements_is_rejected(dotnet_backend):
    with pytest.raises(OwlBasicError):
        _emit('S$="x":P%=0:[OPT0:RTS:]\n', dotnet_backend)


def test_assembler_block_now_parses_in_the_frontend():
    # The frontend no longer rejects it -- that was the layering bug.
    program = analyse("P%=0\n[OPT0:LDA#42:RTS:]\n", name="t")
    assert program is not None
