"""Expand BBC BASIC keyword abbreviations using oaknut-basic.

BBC BASIC lets keywords be abbreviated with a trailing dot -- ``P.`` for
``PRINT``, ``MO.`` for ``MODE``, ``REP.`` for ``REPEAT`` -- as a shorthand when
typing them in. OWL's lexer reads full keywords only, so abbreviated listings
(common in the BBC Micro Bot one-liners) fail to parse, e.g. the lexer reads
``MO.0`` as the float ``0.0``.

oaknut-basic's tokeniser resolves each abbreviation to its keyword token and its
detokeniser re-emits the full keyword, so a tokenise -> detokenise round-trip
expands abbreviations to canonical source while leaving everything else (spacing,
string and REM contents) intact. Anything oaknut cannot tokenise as BBC BASIC II
-- e.g. an OWL extension keyword -- is returned unchanged, so this never
regresses input the round-trip does not understand.
"""

import re

from oaknut.basic import detokenise, tokenise
from oaknut.basic.exceptions import BASICError

# Split an optional leading line number off a line: oaknut emits numbered source,
# but OWL tracks the line-number column separately from the body.
_LINE_BODY_RE = re.compile(r"\s*(\d+)?\s?(.*)")


def expand_unnumbered(source):
    """Return un-numbered *source* with keyword abbreviations expanded.

    oaknut needs line numbers to tokenise, so we auto-number, round-trip, then
    strip the numbers back off (``analyse`` supplies its own logical numbers).
    The physical line count is preserved.
    """
    try:
        numbered = detokenise(tokenise(source, start=10, step=10))
    except BASICError:
        return source
    bodies = [_LINE_BODY_RE.match(line).group(2) for line in numbered.splitlines()]
    return "\n".join(bodies) + ("\n" if source.endswith("\n") else "")


def expand_numbered_lines(numbered_lines):
    """Return ``(line_number, body)`` pairs with abbreviations expanded.

    The real line numbers are preserved (GOTO/GOSUB resolve against them); only
    the bodies are normalised. *body* values keep the leading-space convention
    OWL's front end uses.
    """
    numbered_lines = list(numbered_lines)
    source = "\n".join("%d%s" % (number, body) for number, body in numbered_lines)
    try:
        expanded = detokenise(tokenise(source + "\n"))
    except BASICError:
        return numbered_lines
    pairs = []
    for line in expanded.splitlines():
        match = _LINE_BODY_RE.match(line)
        number, body = match.group(1), match.group(2)
        pairs.append((int(number) if number else 0, " " + body if body else body))
    return pairs
