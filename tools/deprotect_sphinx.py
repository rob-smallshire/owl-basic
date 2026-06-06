"""De-protect Acornsoft Sphinx Adventure's SPHINX2 BASIC program.

Sphinx ships with one anti-listing line: logical line 173 is placed *last* in
the file (out of monotonic order) and stuffed with control bytes and fake
0x8D line-number tokens, which deliberately breaks LIST/RENUMBER and
detokenisers. This tool rewrites that one line as a benign REM and restores
logical line-number order, yielding a clean, listable/compilable copy we can
drive the compiler against.

Extract the tokenised input from the disc image first, e.g.::

    disc cat tests/data/SphinxAdventureFIN.ssd:$.SPHINX2 > sphinx2.tok

then::

    python tools/deprotect_sphinx.py sphinx2.tok tests/data/sphinx2-deprotected.bbc tests/data/sphinx2.bas
"""

import sys
from pathlib import Path

from owl_basic.bbc_basic.detokenizer import detokenize

PROTECTED_LINE = 173
_REM = 0xF4


def split_records(data: bytes):
    """Yield (line_number, content_bytes) for each tokenised line record."""
    records = []
    pos = 0
    while pos + 3 < len(data) and data[pos] == 0x0D and data[pos + 1] != 0xFF:
        length = data[pos + 3]
        number = data[pos + 1] * 256 + data[pos + 2]
        records.append((number, data[pos + 4: pos + length]))
        pos += length
    return records


def build(records) -> bytes:
    out = bytearray()
    for number, content in records:
        out += bytes([0x0D, (number >> 8) & 0xFF, number & 0xFF, 4 + len(content)])
        out += content
    out += bytes([0x0D, 0xFF])  # end-of-program marker
    return bytes(out)


def deprotect(data: bytes):
    """Return (deprotected_bytes, dropped_count).

    The anti-listing line is a *duplicate* line number placed out of monotonic
    order at the end of the file (the genuine line of that number sits in its
    proper place). Drop the out-of-order duplicate(s); keep everything else,
    including the real line, untouched and already in order.
    """
    cleaned = []
    dropped = []
    highest = -1
    for number, content in split_records(data):
        if number <= highest:
            dropped.append(number)  # out-of-order duplicate: the anti-listing line
            continue
        cleaned.append((number, content))
        highest = number
    return build(cleaned), dropped


def main(argv=None):
    argv = argv or sys.argv[1:]
    if len(argv) != 3:
        raise SystemExit(__doc__)
    tokenised = Path(argv[0]).read_bytes()
    deprotected, dropped = deprotect(tokenised)
    Path(argv[1]).write_bytes(deprotected)
    Path(argv[2]).write_text(detokenize(deprotected), encoding="utf-8")
    print("dropped %d anti-listing line(s) %s" % (len(dropped), dropped))
    print("wrote %s (%d bytes) and %s" % (argv[1], len(deprotected), argv[2]))


if __name__ == "__main__":
    main()
