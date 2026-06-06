"""De-protect Acornsoft Sphinx Adventure's SPHINX2 BASIC program.

Sphinx ships with anti-listing protection of two kinds:

* Logical line 173 is placed *last* in the file (out of monotonic order) and
  stuffed with control bytes and fake 0x8D line-number tokens, which
  deliberately breaks LIST/RENUMBER and detokenisers.

* A byte poke on line 363: the ``(`` (0x28) in ``PROCR(6)`` is overwritten with
  the PROC token (0xF2). No source text tokenises to those bytes (typing
  ``PROCRPROC6)`` yields a *name* "RPROC6", not a token), so it can only have
  been poked directly; LIST then shows the garbage ``PROCRPROC6)``. A PROC token
  immediately followed by a digit is never valid (procedure names cannot start
  with a digit), which unambiguously marks the poke; we restore it to ``(``.

This tool reverses both, restoring logical line-number order and yielding a
clean, listable/compilable copy we can drive the compiler against.

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
_PROC = 0xF2
_OPEN_PAREN = 0x28
_QUOTE = 0x22


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


def _restore_paren_pokes(content: bytes):
    """Restore ``(``-poked-to-PROC bytes in one line's content.

    A PROC token (0xF2) immediately followed by a digit, outside a string
    literal, is an overwritten ``(``; restore it. Returns (content, count).
    """
    out = bytearray(content)
    in_string = False
    count = 0
    for i in range(len(out) - 1):
        if out[i] == _QUOTE:
            in_string = not in_string
        elif not in_string and out[i] == _PROC and 0x30 <= out[i + 1] <= 0x39:
            out[i] = _OPEN_PAREN
            count += 1
    return bytes(out), count


def deprotect(data: bytes):
    """Return (deprotected_bytes, dropped, poked).

    Drops the out-of-order duplicate anti-listing line(s) (the genuine line of
    that number sits in its proper place), and restores ``(``-poked-to-PROC
    bytes. Everything else is kept untouched and already in order.
    """
    cleaned = []
    dropped = []
    poked = 0
    highest = -1
    for number, content in split_records(data):
        if number <= highest:
            dropped.append(number)  # out-of-order duplicate: the anti-listing line
            continue
        content, fixed = _restore_paren_pokes(content)
        poked += fixed
        cleaned.append((number, content))
        highest = number
    return build(cleaned), dropped, poked


def main(argv=None):
    argv = argv or sys.argv[1:]
    if len(argv) != 3:
        raise SystemExit(__doc__)
    tokenised = Path(argv[0]).read_bytes()
    deprotected, dropped, poked = deprotect(tokenised)
    Path(argv[1]).write_bytes(deprotected)
    Path(argv[2]).write_text(detokenize(deprotected), encoding="utf-8")
    print("dropped %d anti-listing line(s) %s" % (len(dropped), dropped))
    print("restored %d ( -> PROC byte poke(s)" % poked)
    print("wrote %s (%d bytes) and %s" % (argv[1], len(deprotected), argv[2]))


if __name__ == "__main__":
    main()
