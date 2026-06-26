"""Detokenise BBC BASIC: the interpreter's internal byte form -> source text.

Delegated entirely to oaknut-basic, the canonical ROM-faithful (de)tokeniser
(OWL no longer maintains its own token tables). We default to the BASIC V
dialect: it is a superset that renders BASIC II programs identically -- the bytes
it reassigns (the command-mode keywords AUTO/DELETE/LIST/LOAD/NEW/OLD/RENUMBER/
SAVE, which never appear in a saved program body) -- while also decoding BASIC V's
0xC6/0xC7/0xC8 two-byte escape tokens (ORIGIN, MOUSE, CASE, WHEN, ...). So a
single dialect detokenises both BBC Micro and Archimedes programs correctly.
"""

from typing import List, Tuple

from oaknut.basic import (
    BASIC_V,
    Dialect,
    decode_line_number,
    detokenise as _oaknut_detokenise,
    scan_program,
)
from oaknut.basic.exceptions import DetokeniseError


def decode_line_reference(b0: int, b1: int, b2: int) -> int:
    """Decode the three bytes following 0x8D (a GOTO/GOSUB line reference) into a
    line number, via oaknut's ROM-faithful decoder."""
    return decode_line_number(bytes((b0, b1, b2)))


def detokenize_lines(data, dialect: Dialect = BASIC_V) -> List[Tuple[int, str]]:
    """Detokenise *data*, returning a list of ``(line_number, source_text)``.

    A truncated or malformed image (common in cover-disc rips) keeps its valid
    prefix -- the lines decoded before the bad byte -- rather than failing the
    whole program, as OWL's former hand-written detokeniser did."""
    lines: List[Tuple[int, str]] = []
    try:
        for record in scan_program(bytes(data), dialect=dialect):
            lines.append(
                (record.line_number, "".join(token.value for token in record.tokens)))
    except DetokeniseError:
        pass
    return lines


def detokenize(data, dialect: Dialect = BASIC_V) -> str:
    """Detokenise *data* to LISTed source text (``<n><text>`` per line)."""
    return _oaknut_detokenise(bytes(data), dialect=dialect)
