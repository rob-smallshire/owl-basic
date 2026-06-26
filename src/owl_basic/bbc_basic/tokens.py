"""BBC BASIC dialect constants, re-exported from oaknut-basic.

OWL no longer maintains its own token tables: the canonical, ROM-faithful
dialects live in oaknut-basic and OWL delegates all (de)tokenisation to it (see
:mod:`owl_basic.bbc_basic.detokenizer`). This module keeps the program-framing
byte constants (facts of the saved-program format, not a token table) and
re-exports oaknut's :class:`Dialect` and the BBC BASIC II / V dialects under the
names OWL has historically used.
"""

from oaknut.basic import BASIC_II as BBC_BASIC_II
from oaknut.basic import BASIC_V as BBC_BASIC_V
from oaknut.basic import Dialect

# The line-record framing bytes, common to every dialect.
LINE_RECORD_MARKER = 0x0D     # each program line begins <0x0D> hi lo len ...
END_OF_PROGRAM = 0xFF         # the record after the last line is <0x0D> 0xFF
LINE_NUMBER_TOKEN = 0x8D      # GOTO/GOSUB etc. line refs: 0x8D + 3 encoded bytes
PSEUDO_VAR_OFFSET = 0x40      # statement form of a pseudo-variable = byte + 0x40

__all__ = [
    "BBC_BASIC_II", "BBC_BASIC_V", "Dialect",
    "LINE_RECORD_MARKER", "END_OF_PROGRAM", "LINE_NUMBER_TOKEN",
    "PSEUDO_VAR_OFFSET",
]
