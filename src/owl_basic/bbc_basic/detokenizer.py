"""Detokenise BBC BASIC: the interpreter's internal byte form -> source text.

Original implementation. The line-record framing and the XOR-0x54 line-number
encoding are documented behaviours of the BBC BASIC ROMs.
"""

from typing import List, Tuple

from owl_basic.bbc_basic.tokens import (
    BBC_BASIC_II,
    END_OF_PROGRAM,
    LINE_NUMBER_TOKEN,
    LINE_RECORD_MARKER,
    Dialect,
)

_QUOTE = 0x22


def decode_line_reference(b0: int, b1: int, b2: int) -> int:
    """Decode the three bytes following 0x8D into a line number.

    Inverse of the ROM's encoding: the top two bits of each of the low and high
    bytes are packed (XOR 0x54) into the first byte; the remaining six bits live
    in the other two.
    """
    x = b0 ^ 0x54
    lo = (b1 & 0x3F) | ((x & 0x30) << 2)
    hi = (b2 & 0x3F) | ((x & 0x0C) << 4)
    return hi * 256 + lo


def detokenize_lines(data, dialect: Dialect = BBC_BASIC_II) -> List[Tuple[int, str]]:
    """Detokenise *data*, returning a list of ``(line_number, source_text)``."""
    data = bytes(data)
    lines: List[Tuple[int, str]] = []
    pos = 0
    end = len(data)
    while pos + 3 < end:
        if data[pos] != LINE_RECORD_MARKER or data[pos + 1] == END_OF_PROGRAM:
            break
        line_number = data[pos + 1] * 256 + data[pos + 2]
        length = data[pos + 3]
        if length < 4:
            break  # malformed: a line is at least its 4-byte header
        content = data[pos + 4: pos + length]
        lines.append((line_number, _detokenize_content(content, dialect)))
        pos += length
    return lines


def detokenize(data, dialect: Dialect = BBC_BASIC_II) -> str:
    """Detokenise *data* to LISTed source text (``<n> <text>`` per line)."""
    return "".join(
        "%d%s\n" % (number, text) for number, text in detokenize_lines(data, dialect)
    )


def _detokenize_content(content: bytes, dialect: Dialect) -> str:
    out: List[str] = []
    i = 0
    n = len(content)
    literal = False  # set by REM/DATA: the rest of the line is literal text
    while i < n:
        b = content[i]
        if literal:
            out.append(chr(b))
            i += 1
            continue
        if b == _QUOTE:  # copy the quoted string verbatim, including both quotes
            out.append('"')
            i += 1
            while i < n:
                c = content[i]
                out.append(chr(c))
                i += 1
                if c == _QUOTE:
                    break
            continue
        if b == LINE_NUMBER_TOKEN and i + 3 < n:
            out.append(str(decode_line_reference(
                content[i + 1], content[i + 2], content[i + 3])))
            i += 4
            continue
        name = dialect.byte_to_name.get(b)
        if name is not None:
            out.append(name)
            if b in dialect.line_literal_bytes:
                literal = True
            i += 1
            continue
        out.append(chr(b))  # an ordinary character (or an unknown byte)
        i += 1
    return "".join(out)
