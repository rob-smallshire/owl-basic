"""BASIC V keywords used as variable names in older (BASIC II) listings.

SUM, WAIT and SWAP are BASIC V additions -- they did not exist in BASIC II, so
BBC Micro listings of that era freely used them (and POINT) as ordinary variable
names. The ROM-faithful tokeniser (oaknut) confirms it: in BASIC II `WAIT$`,
`SUMX`, `SUM%`, `POINTER$` are all plain text, not keywords.

OWL supports the BASIC V superset, so it keeps these as keywords -- but, like the
ROM's conditional-flag keywords (TIME/PAGE/VPOS...), the keyword must be
suppressed when it abuts a name character or a $/% sigil, so a variable that
merely starts with (or is spelt the same as, plus a sigil) one of these words is
lexed as an identifier. The bare keyword (a BASIC V statement/function) is
unchanged. Surfaced by the A & B Computing corpus (FORTUNE, MATHSTE, SHAPE, ...).

Tier 1 (this change): the prefix and sigil forms. Bare-scalar use of the word
itself (WAIT=INKEY, SUM=1, SWAP=0) remains the keyword -- that collision is a
separate, grammar-level decision.
"""
import pytest

from owl_basic.analysis import analyse
from owl_basic.syntax import parser


class _Options:
    debug_lex = False
    verbose = False
    use_clr = False


def _token_pairs(source):
    lexer = parser.buildLexer(_Options())
    lexer.input(source)
    return [(t.type, str(t.value)) for t in lexer]


# --- prefix forms: the keyword is the start of a longer name -> identifier -----

@pytest.mark.parametrize("word", ["SUMX", "SUMTOTAL", "WAITING", "SWAPPED", "POINTER"])
def test_keyword_prefix_of_a_name_is_an_identifier(word):
    assert _token_pairs(word) == [("ID", word)]


# --- sigil forms: keyword + $ or % is a (string/integer) variable -------------

@pytest.mark.parametrize("name", ["WAIT$", "WAIT%", "SUM$", "SUM%", "SWAP$", "POINTER$"])
def test_keyword_with_sigil_is_an_identifier(name):
    assert _token_pairs(name) == [("ID", name)]


def test_sigil_array_is_an_array_identifier():
    # SUM%(...) is a subscripted integer array, not the SUM keyword.
    assert _token_pairs("SUM%(3)")[0] == ("ARRAYID_LPAREN", "SUM%(")


# --- the bare keyword is unchanged (still the BASIC V statement/function) ------

@pytest.mark.parametrize("word", ["WAIT", "SUM", "SWAP", "POINT"])
def test_bare_keyword_still_tokenises(word):
    assert _token_pairs(word) == [(word, word)]


def test_swap_statement_unaffected():
    # SWAP a,b (a space after) stays the keyword form.
    assert _token_pairs("SWAP A,B")[0] == ("SWAP", "SWAP")


# --- end to end: such programs now parse and compile --------------------------

@pytest.mark.parametrize("source", [
    'WAIT$="hi":PRINT WAIT$\n',
    "SUM%=5:PRINT SUM%\n",
    "SUMX=3:SUMX=SUMX+1:PRINT SUMX\n",
    'POINTER$="x":PRINT POINTER$\n',
    "DIM SUM%(3)\nSUM%(1)=7\nPRINT SUM%(1)\n",
])
def test_program_analyses(source):
    analyse(source, name="t")


def test_keyword_named_variable_emits_il(dotnet_backend):
    assert dotnet_backend.emit_il(analyse("SUMX=3:PRINT SUMX\n", name="t"))
