"""Differential audit: OWL's lexer vs the oaknut-basic ROM-faithful tokeniser.

For every alphabetic BBC BASIC II keyword, drive it through both tokenisers --
alone, and abutting a trailing letter/digit (the adjacency cases where the ROM's
first-prefix-match + conditional flag matter) -- and require the same sequence of
keyword tokens. This guards the TOP and conditional-flag fixes against regression
and would catch any new keyword-adjacency drift.

A small set of divergences is expected and documented in DIVERGENCES below.
"""
import re

import pytest

import oaknut.basic as _ob
from oaknut.basic import tokenise
from owl_basic.syntax import parser


class _Options:
    debug_lex = False
    verbose = False
    use_clr = False


# OWL token types that are not keywords (punctuation, literals, identifiers, and
# OWL's bundled forms: FN_ID/PROC_ID for FN/PROC names, COMMENT for REM).
_NON_KEYWORD = {
    "EOL", "ID", "PROC_ID", "FN_ID", "ARRAYID_LPAREN", "COMMENT", "STAR_COMMAND",
    "ASSEMBLER", "LITERAL_STRING", "LITERAL_FLOAT", "LITERAL_INTEGER", "QUERY",
    "PLING", "PIPE", "HASH", "DOLLAR", "APOSTROPHE", "COLON", "COMMA", "SEMICOLON",
    "PLUS", "MINUS", "TIMES", "DIVIDE", "EQ", "NE", "LTE", "GTE", "LT", "GT",
    "PLUS_ASSIGN", "MINUS_ASSIGN", "TIMES_ASSIGN", "DIVIDE_ASSIGN", "AND_ASSIGN",
    "DIV_ASSIGN", "EOR_ASSIGN", "MOD_ASSIGN", "OR_ASSIGN", "SHIFT_LEFT",
    "SHIFT_RIGHT", "SHIFT_RIGHT_UNSIGNED", "AMPERSAND", "LPAREN", "RPAREN",
    "LBRAC", "RBRAC", "CARET", "TILDE", "DOT",
}

# Keywords where OWL is expected to differ from the ROM tokeniser, by design:
#  * editor/immediate-mode commands a compiler does not run as statements;
#  * REM/DATA captured as a single line-literal token (content folded into value),
#    and FN/PROC names bundled into FN_ID/PROC_ID -- both faithful to the ROM's
#    own name-skipping, just a different token shape.
# (RETURN was here as an unresolved ROM-table conflict; the BASIC II disassembly
# settled it -- RETURN's keyword-table flag byte is &01, CONDITIONAL -- so OWL's
# lexer and tokens.py now both agree with the ROM and it is no longer divergent.)
DIVERGENCES = {
    "AUTO", "DELETE", "LIST", "LOAD", "NEW", "OLD", "RENUMBER", "SAVE",
    "FN", "PROC", "REM", "DATA",
}


def _norm(value):
    return re.sub(r"[^A-Z]+$", "", str(value).upper())


def _oaknut_keywords(source):
    record = list(_ob.scan_program(tokenise(source, start=10, step=10)))[0]
    return [_norm(t.value) for t in record.tokens
            if str(t.kind).endswith("KEYWORD")]


def _owl_keywords(source):
    lexer = parser.buildLexer(_Options())
    lexer.input(source)
    return [_norm(t.value) for t in lexer if t.type not in _NON_KEYWORD]


_ALPHABETIC_KEYWORDS = sorted(
    k for k in set(_ob.TOKEN_TO_KEYWORD.values())
    if k.isalpha() and k not in DIVERGENCES
)


@pytest.mark.parametrize("keyword", _ALPHABETIC_KEYWORDS)
def test_owl_matches_rom_tokeniser(keyword):
    for suffix in ("", "X", "1", "Z"):
        probe = keyword + suffix
        assert _owl_keywords(probe) == _oaknut_keywords(probe), probe


def _oaknut_conditional_keywords():
    """The keywords oaknut flags CONDITIONAL (ROM keyword-table bit 0)."""
    for value in vars(_ob.tokens).values():
        if (isinstance(value, (list, tuple)) and value
                and isinstance(value[0], tuple) and len(value[0]) == 3
                and isinstance(value[0][0], str)):
            return {name for (name, _byte, flags) in value
                    if flags & _ob.FLAG_CONDITIONAL}
    raise AssertionError("could not locate oaknut's keyword table")


def _owl_conditional_keywords():
    """The keywords OWL's tokens.py table flags CONDITIONAL."""
    from owl_basic.bbc_basic import tokens as owl_tokens
    return {spec.name for spec in owl_tokens.BBC_BASIC_II.tokens
            if owl_tokens.Flag.CONDITIONAL in spec.flags}


def test_conditional_flag_column_matches_rom():
    # tokens.py's CONDITIONAL column must equal the ROM's (oaknut is ROM-faithful).
    # This caught 13 stragglers (RETURN, END, ENDPROC, STOP, RUN, CLS, ...) whose
    # bit-0 flag was missing; it guards the whole column against future drift.
    assert _owl_conditional_keywords() == _oaknut_conditional_keywords()


def test_divergence_set_is_still_divergent():
    # If a "known divergence" silently starts agreeing, drop it from DIVERGENCES.
    still = [k for k in sorted(DIVERGENCES)
            if k.isalpha()
            and _owl_keywords(k + "X") == _oaknut_keywords(k + "X")
            and _owl_keywords(k) == _oaknut_keywords(k)]
    # FN/PROC/REM/DATA differ in token *shape* not keyword list, so they may agree
    # on this coarse comparison; only flag the command keywords + RETURN.
    unexpected = [k for k in still
                  if k in {"AUTO", "DELETE", "LIST", "LOAD", "NEW", "OLD",
                           "RENUMBER", "SAVE"}]
    assert not unexpected, f"no longer divergent (remove from DIVERGENCES): {unexpected}"
