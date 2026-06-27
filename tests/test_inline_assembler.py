"""Inline assembler `[ ... ]` is a backend-agnostic opaque block.

The frontend captures the block verbatim into a generic ``InlineAssembler``
statement and never rejects it; the ``dotnet`` backend, having no assembler
dialect, rejects it cleanly at code generation. See docs/inline-assembler.md.
"""
import pytest

from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse_numbered_lines
from owl_basic.exceptions import OwlBasicError
from owl_basic.syntax.ast import InlineAssembler


def _analyse(lines):
    return analyse_numbered_lines(lines, name="asm")


def _statements(program):
    """Every statement node across the analysed program's basic blocks."""
    return [statement
            for blocks in program.ordered_basic_blocks.values()
            for block in blocks
            for statement in block.statements]


def _only_assembler(program):
    nodes = [n for n in _statements(program) if isinstance(n, InlineAssembler)]
    assert len(nodes) == 1, f"expected one InlineAssembler, got {len(nodes)}"
    return nodes[0]


def test_single_line_block_parses_to_inline_assembler():
    node = _only_assembler(_analyse([
        (10, " [OPT2:LDA #65:JSR &FFEE:]"),
        (20, " END"),
    ]))
    # The block text is captured from '[' up to (not including) the terminating
    # ']', which is a separate statement-separator token so a statement may
    # follow it on the same line (e.g. ']NEXT'). The content is verbatim.
    assert node.code.startswith("[")
    assert "LDA #65" in node.code and "JSR &FFEE" in node.code


def test_multi_line_block_parses_and_keeps_text_verbatim():
    # The classic two-pass idiom: '[' and ']' on different lines. The per-line
    # gate must not flag the body lines; the block is captured whole.
    node = _only_assembler(_analyse([
        (10, " FOR pass%=0 TO 2 STEP 2"),
        (20, " P%=code%"),
        (30, " [OPT pass%"),
        (40, " LDA #65"),
        (50, " JSR &FFEE"),
        (60, " ]"),
        (70, " NEXT"),
        (80, " END"),
    ]))
    assert "LDA #65" in node.code and "JSR &FFEE" in node.code


def test_bracket_in_a_string_is_not_assembler():
    # A '[' inside a string literal must not open an assembler block.
    program = _analyse([(10, ' PRINT "[not asm]"'), (20, " END")])
    assert not any(isinstance(n, InlineAssembler) for n in _statements(program))


def test_close_bracket_inside_a_string_does_not_terminate_the_block():
    # EQUS "Contains]" -- per the BBC ROM, ']' only terminates at the start of a
    # statement, and a quoted string is read as one operand, so the ']' inside
    # the quotes is string data, not the block terminator. The block runs to the
    # real ']' after RTS.
    node = _only_assembler(_analyse([
        (10, ' [OPT0:EQUS "Contains]":RTS:]'),
        (20, " END"),
    ]))
    # The ']' inside the quotes is captured as block content (the block did not
    # end there), and the block runs on past it to RTS; the real terminator ']'
    # after RTS is a separate token, so it is not part of the captured code.
    assert 'EQUS "Contains]"' in node.code
    assert "RTS" in node.code


@requires_dotnet_toolchain
def test_dotnet_backend_rejects_inline_assembler_cleanly(dotnet_backend):
    program = _analyse([(10, " [OPT2:LDA #65:]"), (20, " END")])
    with pytest.raises(OwlBasicError, match="does not support inline assembler"):
        dotnet_backend.emit_il(program)
