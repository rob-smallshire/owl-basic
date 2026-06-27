"""The two-pass assembler idiom, where `]` is followed by a statement.

The standard BBC assembler harness is `FOR pass%=0 TO 3 STEP 3 [ ... ] NEXT`,
and the closing `]` is very often on the same line as the loop close: `]NEXT`.
In BBC BASIC `]` is itself a statement terminator, so a statement may follow it
with no `:` separator. The lexer used to swallow the `]` into the assembler
token, leaving `ASSEMBLER NEXT` with nothing between them -- a "Syntax error at
NEXT" that the diagnostic then blamed on assembler. Now `]` is a separator
token, so `]NEXT` (and `]PRINT`, etc.) parse, and the whole block reaches the
backend like any other assembler (rejected there on dotnet).

Surfaced across the Acorn User corpus (e.g. Tau85-a/MAY85.TIMER).
"""
import pytest

from conftest import requires_dotnet_toolchain
from owl_basic.analysis import analyse_numbered_lines
from owl_basic.exceptions import OwlBasicError


def _two_pass(closer):
    return [(10, "DIM code% 100"), (20, "FOR pass%=0 TO 3 STEP 3"),
            (30, "P%=code%"), (40, "[OPT pass%"), (50, ".start LDA #0"),
            (60, "RTS"), (70, closer), (80, "ENDPROC")]


def test_close_bracket_then_next_same_line_parses():
    # ]NEXT -- the closing bracket and NEXT on one line, no separator.
    program = analyse_numbered_lines(_two_pass("]NEXT"), name="t")
    assert program is not None


def test_close_bracket_colon_next_still_parses():
    program = analyse_numbered_lines(_two_pass("]:NEXT"), name="t")
    assert program is not None


def test_close_bracket_alone_then_next_line_still_parses():
    program = analyse_numbered_lines(
        [(10, "FOR I%=0 TO 3 STEP 3"), (20, "[OPT I%"), (30, "RTS"),
         (40, "]"), (50, "NEXT"), (60, "END")], name="t")
    assert program is not None


def test_statement_after_close_bracket_parses():
    # Any statement may follow ] on the same line, not just NEXT.
    program = analyse_numbered_lines(
        [(10, "[OPT 0"), (20, "RTS"), (30, ']PRINT "done"'), (40, "END")],
        name="t")
    assert program is not None


def test_two_pass_with_close_bracket_next_rejected_at_backend(dotnet_backend):
    # It parses, then the dotnet backend rejects the assembler block at codegen.
    program = analyse_numbered_lines(_two_pass("]NEXT"), name="t")
    with pytest.raises(OwlBasicError) as excinfo:
        dotnet_backend.emit_il(program)
    assert "assembl" in str(excinfo.value).lower()
