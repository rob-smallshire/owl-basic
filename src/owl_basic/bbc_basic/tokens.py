"""Token tables and the dialect model for the BBC BASIC (de)tokeniser.

A :class:`Dialect` is the single source of truth for a BASIC variant: an ordered
table of :class:`TokenSpec` rows (byte value, keyword name, behaviour flags).
The byte<->keyword values are facts of the BBC BASIC ROMs; the behaviour-flag
model is our own.

Currently only BBC BASIC II (BBC Micro) is populated. BBC BASIC IV (Master), V
(Archimedes/RISC OS, with the 0xC6-0xC8 escape-token mechanism) and BB4W are
planned as further dialects.
"""

from dataclasses import dataclass, field
from enum import Flag as _Flag, auto
from typing import Dict, FrozenSet, Tuple

# The line-record framing bytes, common to every dialect.
LINE_RECORD_MARKER = 0x0D     # each program line begins <0x0D> hi lo len ...
END_OF_PROGRAM = 0xFF         # the record after the last line is <0x0D> 0xFF
LINE_NUMBER_TOKEN = 0x8D      # GOTO/GOSUB etc. line refs: 0x8D + 3 encoded bytes
PSEUDO_VAR_OFFSET = 0x40      # statement form of a pseudo-variable = byte + 0x40


class Flag(_Flag):
    """Per-keyword behaviour, driving both tokenising and detokenising."""

    NONE = 0
    CONDITIONAL = auto()         # only a keyword if not followed by an identifier char
    LINE_LITERAL = auto()        # the rest of the line is literal text (REM, DATA)
    EXPECT_LINE_NUMBER = auto()  # a following digit run encodes a line reference
    PSEUDO_VAR = auto()          # also has a statement form at byte + 0x40
    START_OF_STATEMENT = auto()  # resets the tokeniser to start-of-statement (THEN/ELSE)
    FN_PROC = auto()             # the following identifier is an opaque user name
    COMMON_ABBREV = auto()       # ROM-preferred winner for a shared abbreviation


@dataclass(frozen=True)
class TokenSpec:
    byte: int
    name: str
    flags: Flag = Flag.NONE


@dataclass(frozen=True)
class Dialect:
    """A BASIC variant: its token table plus derived lookup maps."""

    name: str
    tokens: Tuple[TokenSpec, ...]
    byte_to_name: Dict[int, str] = field(default_factory=dict)
    line_literal_bytes: FrozenSet[int] = field(default_factory=frozenset)

    @classmethod
    def build(cls, name: str, tokens: Tuple[TokenSpec, ...]) -> "Dialect":
        byte_to_name: Dict[int, str] = {}
        line_literal = set()
        for spec in tokens:
            byte_to_name[spec.byte] = spec.name
            if Flag.PSEUDO_VAR in spec.flags:
                # The statement form (byte + 0x40) detokenises to the same name.
                byte_to_name[spec.byte + PSEUDO_VAR_OFFSET] = spec.name
            if Flag.LINE_LITERAL in spec.flags:
                line_literal.add(spec.byte)
        return cls(name, tokens, byte_to_name, frozenset(line_literal))


def _t(byte, name, flags=Flag.NONE):
    return TokenSpec(byte, name, flags)


# BBC BASIC II (BBC Micro). Bytes 0x80-0xFF; 0x8D is the line-number marker (not
# a keyword) and 0xCE is unused (BBC BASIC IV fills it with EDIT). The five
# pseudo-variables carry their function-form byte and PSEUDO_VAR; their statement
# forms (byte + 0x40, i.e. 0xCF-0xD3) are derived.
_BBC_BASIC_II_TOKENS: Tuple[TokenSpec, ...] = (
    _t(0x80, "AND", Flag.COMMON_ABBREV), _t(0x81, "DIV"), _t(0x82, "EOR"),
    _t(0x83, "MOD"), _t(0x84, "OR"), _t(0x85, "ERROR"), _t(0x86, "LINE"),
    _t(0x87, "OFF"), _t(0x88, "STEP"), _t(0x89, "SPC"), _t(0x8A, "TAB("),
    _t(0x8B, "ELSE", Flag.START_OF_STATEMENT | Flag.EXPECT_LINE_NUMBER),
    _t(0x8C, "THEN", Flag.START_OF_STATEMENT | Flag.EXPECT_LINE_NUMBER),
    _t(0x8E, "OPENIN"), _t(0x8F, "PTR", Flag.CONDITIONAL | Flag.PSEUDO_VAR),
    _t(0x90, "PAGE", Flag.CONDITIONAL | Flag.PSEUDO_VAR),
    _t(0x91, "TIME", Flag.CONDITIONAL | Flag.PSEUDO_VAR | Flag.COMMON_ABBREV),
    _t(0x92, "LOMEM", Flag.CONDITIONAL | Flag.PSEUDO_VAR),
    _t(0x93, "HIMEM", Flag.CONDITIONAL | Flag.PSEUDO_VAR),
    _t(0x94, "ABS"), _t(0x95, "ACS"), _t(0x96, "ADVAL"), _t(0x97, "ASC"),
    _t(0x98, "ASN"), _t(0x99, "ATN"), _t(0x9A, "BGET", Flag.CONDITIONAL),
    _t(0x9B, "COS"), _t(0x9C, "COUNT", Flag.CONDITIONAL), _t(0x9D, "DEG"),
    _t(0x9E, "ERL", Flag.CONDITIONAL), _t(0x9F, "ERR", Flag.CONDITIONAL),
    _t(0xA0, "EVAL"), _t(0xA1, "EXP"), _t(0xA2, "EXT", Flag.CONDITIONAL),
    _t(0xA3, "FALSE", Flag.CONDITIONAL), _t(0xA4, "FN", Flag.FN_PROC),
    _t(0xA5, "GET"), _t(0xA6, "INKEY"), _t(0xA7, "INSTR("), _t(0xA8, "INT"),
    _t(0xA9, "LEN"), _t(0xAA, "LN"), _t(0xAB, "LOG"), _t(0xAC, "NOT"),
    _t(0xAD, "OPENUP"), _t(0xAE, "OPENOUT"), _t(0xAF, "PI", Flag.CONDITIONAL),
    _t(0xB0, "POINT("), _t(0xB1, "POS", Flag.CONDITIONAL), _t(0xB2, "RAD"),
    _t(0xB3, "RND", Flag.CONDITIONAL), _t(0xB4, "SGN"), _t(0xB5, "SIN"),
    _t(0xB6, "SQR"), _t(0xB7, "TAN"), _t(0xB8, "TO"),
    _t(0xB9, "TRUE", Flag.CONDITIONAL), _t(0xBA, "USR"), _t(0xBB, "VAL"),
    _t(0xBC, "VPOS", Flag.CONDITIONAL), _t(0xBD, "CHR$"), _t(0xBE, "GET$"),
    _t(0xBF, "INKEY$"), _t(0xC0, "LEFT$("), _t(0xC1, "MID$("),
    _t(0xC2, "RIGHT$("), _t(0xC3, "STR$"), _t(0xC4, "STRING$("),
    _t(0xC5, "EOF", Flag.CONDITIONAL),
    _t(0xC6, "AUTO"), _t(0xC7, "DELETE"), _t(0xC8, "LOAD"), _t(0xC9, "LIST"),
    _t(0xCA, "NEW", Flag.CONDITIONAL), _t(0xCB, "OLD", Flag.CONDITIONAL),
    _t(0xCC, "RENUMBER"), _t(0xCD, "SAVE"),
    _t(0xD4, "SOUND"), _t(0xD5, "BPUT", Flag.CONDITIONAL), _t(0xD6, "CALL"),
    _t(0xD7, "CHAIN"),
    _t(0xD8, "CLEAR", Flag.CONDITIONAL), _t(0xD9, "CLOSE", Flag.CONDITIONAL),
    _t(0xDA, "CLG", Flag.CONDITIONAL), _t(0xDB, "CLS", Flag.CONDITIONAL),
    _t(0xDC, "DATA", Flag.LINE_LITERAL), _t(0xDD, "DEF"), _t(0xDE, "DIM"),
    _t(0xDF, "DRAW"), _t(0xE0, "END", Flag.CONDITIONAL),
    _t(0xE1, "ENDPROC", Flag.COMMON_ABBREV | Flag.CONDITIONAL),
    _t(0xE2, "ENVELOPE"), _t(0xE3, "FOR"),
    _t(0xE4, "GOSUB", Flag.EXPECT_LINE_NUMBER),
    _t(0xE5, "GOTO", Flag.EXPECT_LINE_NUMBER), _t(0xE6, "GCOL"), _t(0xE7, "IF"),
    _t(0xE8, "INPUT"), _t(0xE9, "LET"), _t(0xEA, "LOCAL"), _t(0xEB, "MODE"),
    _t(0xEC, "MOVE"), _t(0xED, "NEXT"), _t(0xEE, "ON"), _t(0xEF, "VDU"),
    _t(0xF0, "PLOT"), _t(0xF1, "PRINT", Flag.COMMON_ABBREV), _t(0xF2, "PROC", Flag.FN_PROC),
    _t(0xF3, "READ"), _t(0xF4, "REM", Flag.LINE_LITERAL),
    _t(0xF5, "REPEAT", Flag.COMMON_ABBREV), _t(0xF6, "REPORT", Flag.CONDITIONAL),
    _t(0xF7, "RESTORE", Flag.EXPECT_LINE_NUMBER),
    _t(0xF8, "RETURN", Flag.CONDITIONAL),
    _t(0xF9, "RUN", Flag.CONDITIONAL), _t(0xFA, "STOP", Flag.CONDITIONAL),
    _t(0xFB, "COLOUR"), _t(0xFC, "TRACE"),
    _t(0xFD, "UNTIL"), _t(0xFE, "WIDTH"), _t(0xFF, "OSCLI"),
)

BBC_BASIC_II = Dialect.build("BBC BASIC II", _BBC_BASIC_II_TOKENS)
