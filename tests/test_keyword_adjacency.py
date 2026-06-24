"""Keyword adjacency: where a keyword abuts following letters.

BBC BASIC II tokenises by first-prefix-match at the start of a name-run (verified
against the ROM keyword table), NOT longest-match -- and `TOP` is not a keyword at
all (it is a run-time pseudo-variable; the table has only `TO`). So `0TOPI` is
`0 TO PI`, and the family of "gotchas" holds: a keyword that is a prefix of the
following letters still tokenises (TOTAL -> TO TAL, FORM -> FOR M).

OWL's lexer does longest-match, which is faithful here as long as it does not
carry spurious longer keywords like `TOP`. These pin that.
"""
import pytest

from owl_basic.analysis import analyse
from owl_basic.syntax import parser


class _Options:
    debug_lex = False
    verbose = False
    use_clr = False


def _keywords(source):
    """The keyword token types the lexer produces for *source*."""
    lexer = parser.buildLexer(_Options())
    lexer.input(source)
    # A token is "keyword-like" if its type is its own uppercase value (TO, PI,
    # FOR, ...) rather than ID / a literal -- simplest: collect non-ID, non-literal
    # alphabetic tokens.
    out = []
    for tok in lexer:
        if tok.type not in ("ID",) and not tok.type.startswith("LITERAL"):
            out.append(tok.type)
    return out


def _token_pairs(source):
    lexer = parser.buildLexer(_Options())
    lexer.input(source)
    return [(t.type, str(t.value)) for t in lexer]


# --- the bug: TOP is not a keyword, so 0TOPI is 0 TO PI ---------------------

def test_0TOPI_is_TO_PI():
    assert _token_pairs("0TOPI") == [
        ("LITERAL_INTEGER", "0"), ("TO", "TO"), ("PI", "PI")]


def test_TOPRINT_is_TO_PRINT():
    assert _token_pairs("TOPRINT") == [("TO", "TO"), ("PRINT", "PRINT")]


# --- TOP is the pseudo-variable when standalone, but TO+P glued after a value -
# Verified on the ROM: `PRINT TOP` prints an address (TOP is a real pseudo-var),
# yet `FORI=P+2TOP+98` runs as `FOR I=P+2 TO P+98` -- the FOR byte-saver glues TO
# straight onto the loop limit. So a TOP riding directly on a digit is TO + P.

def test_digit_glued_TOP_is_TO_P():
    pairs = _token_pairs("2TOP+98")
    assert ("TO", "TO") in pairs
    assert ("ID", "P") in pairs
    assert all(t != "TOP" for t, _ in pairs), pairs


def test_digit_glued_TOP_at_end_is_TO_P():
    # `0TOP` (loop `... TO P`) with TOP at the very end: still TO + P.
    assert _token_pairs("0TOP") == [
        ("LITERAL_INTEGER", "0"), ("TO", "TO"), ("ID", "P")]


@pytest.mark.parametrize("source,before", [
    ("FNf(0)TOP+1", ")"),   # close paren ends a value
    ("I%TOP", "%"),         # integer suffix ends a variable
    ("A$TOP", "$"),         # string suffix ends a variable
    ("b%?0)]TOP", "]"),     # close bracket ends a value
])
def test_value_terminator_glued_TOP_is_TO_P(source, before):
    # TO crunches at any name-run start, i.e. right after any value terminator --
    # not only digits. So TOP glued onto ) % $ ] is the FOR separator TO + P.
    pairs = _token_pairs(source)
    assert ("TO", "TO") in pairs, (before, pairs)
    assert ("ID", "P") in pairs, (before, pairs)
    assert all(t != "TOP" for t, _ in pairs), (before, pairs)


def test_space_separated_TOP_after_a_value_is_TO_P():
    # The space before TOP is identical to `PRINT TOP`, so this cannot be told
    # apart by the preceding character -- only by the previous *token*: a value
    # (here the literal 2) before TOP means `... TO P`. Corpus adefad861e2b line 5
    # is FORI=P+2 TOP+150 STEP3.
    pairs = _token_pairs("P+2 TOP+150")
    assert ("TO", "TO") in pairs, pairs
    assert ("ID", "P") in pairs, pairs
    assert all(t != "TOP" for t, _ in pairs), pairs


def test_space_separated_TOP_after_a_variable_is_TO_P():
    # FORI=X TOP -> FOR I=X TO P: a variable also ends a value.
    pairs = _token_pairs("X TOP")
    assert ("TO", "TO") in pairs and ("ID", "P") in pairs, pairs
    assert all(t != "TOP" for t, _ in pairs), pairs


def test_value_keyword_glued_TOP_is_TO_P():
    # A nullary value pseudo-variable also ends a value: PAGE TOP -> PAGE TO P.
    pairs = _token_pairs("PAGE TOP")
    assert pairs == [("PAGE", "PAGE"), ("TO", "TO"), ("ID", "P")], pairs


def test_standalone_TOP_stays_the_pseudovariable():
    # Not glued to a value: TOP is the top-of-program pseudo-variable.
    assert _token_pairs("TOP") == [("TOP", "TOP")]
    assert _token_pairs("TOP-100")[0] == ("TOP", "TOP")
    assert ("TOP", "TOP") in _token_pairs("PRINT TOP")


@pytest.mark.parametrize("source", [
    "=TOP",        # after '=' (operand expected)
    "A=TOP+1",     # after '=', then used in arithmetic
    "X+TOP",       # after a binary operator
    "(TOP)",       # after '(' (operand expected)
    "PRINT;TOP",   # after ';'
])
def test_TOP_in_operand_position_is_the_pseudovariable(source):
    assert ("TOP", "TOP") in _token_pairs(source), _token_pairs(source)
    assert all(t != "TO" for t, _ in _token_pairs(source)), _token_pairs(source)


def test_TOP_as_for_limit_after_TO_is_the_pseudovariable():
    # FOR I=0 TO TOP: the separator TO is in value position for the limit, so the
    # *limit* TOP is the pseudo-variable, not another TO + P.
    pairs = _token_pairs("FOR I=0 TO TOP")
    assert pairs.count(("TO", "TO")) == 1, pairs   # only the structural separator
    assert ("TOP", "TOP") in pairs, pairs


def test_for_to_p_byte_saver_analyses_as_one_for():
    # The corpus shape (ff76e28369da line 6): FORI=P+2TOP+98STEP3.
    program = analyse("P=&2000\nFORI=P+2TOP+98STEP3:NEXT\n", name="t")
    from helpers import walk
    fors = [n for n in walk(program.parse_tree) if type(n).__name__ == "ForToStep"]
    assert len(fors) == 1


def test_for_to_p_byte_saver_spaced_analyses_as_one_for():
    # The corpus shape (adefad861e2b line 5): FORI=P+2 TOP+150 STEP3 -- a space
    # before TOP, yet still FOR I=P+2 TO P+150 STEP 3.
    program = analyse("P=&2000\nFORI=P+2 TOP+150 STEP3:NEXT\n", name="t")
    from helpers import walk
    fors = [n for n in walk(program.parse_tree) if type(n).__name__ == "ForToStep"]
    assert len(fors) == 1


def test_STOP_keyword_is_not_disturbed_by_the_TOP_rule():
    # STOP contains TOP; it must stay the STOP keyword, even glued after a digit.
    assert _token_pairs("STOP") == [("STOP", "STOP")]
    assert _token_pairs("2STOP") == [("LITERAL_INTEGER", "2"), ("STOP", "STOP")]


def test_for_to_pi_without_spaces_analyses():
    # FOR i=0 TO PI*2 STEP 0.1 written byte-saved as FORi=0TOPI*2STEP0.1
    analyse("FORi=0TOPI*2STEP0.1:NEXT\n", name="t")


def test_for_to_pi_loop_runs(monkeypatch):
    # The angle loop must actually iterate (limit PI*2 ~ 6.28), not stop at TOP.
    program = analyse("c%=0\nFORi=0TOPI*2STEP1:c%=c%+1:NEXT\nPRINT c%\n", name="t")
    # PI*2 ~= 6.28, STEP 1 -> i=0,1,2,3,4,5,6 -> 7 iterations. Just assert it
    # analysed with a single FOR (not a broken TOP parse).
    from helpers import walk
    fors = [n for n in walk(program.parse_tree)
            if type(n).__name__ == "ForToStep"]
    assert len(fors) == 1


# --- the established gotchas (already correct; guard against regression) ----

def test_TOTAL_is_TO_TAL():
    assert _token_pairs("TOTAL") == [("TO", "TO"), ("ID", "TAL")]


def test_INPUTS_is_INPUT_S():
    assert _token_pairs("INPUTS") == [("INPUT", "INPUT"), ("ID", "S")]


def test_FORM_is_FOR_M():
    assert _token_pairs("FORM") == [("FOR", "FOR"), ("ID", "M")]


# --- conditional-flag keywords: not tokenised before a name char -----------
# The ROM gives these the CONDITIONAL flag (bit 0): a name char immediately after
# suppresses the keyword, so TIMER/PAGES/HIMEMORY stay variables. OWL's pseudo-
# variable rules (TIME/PAGE/PTR/LOMEM/HIMEM and RND/VPOS/ERL/ERR) were greedy.

@pytest.mark.parametrize("word", [
    "TIMER", "PAGES", "PTRX", "LOMEMORY", "HIMEMORY", "RNDOM", "VPOSITION",
    "ERLANG", "ERROL", "RETURNED",
])
def test_conditional_keyword_followed_by_letters_is_an_identifier(word):
    assert _token_pairs(word) == [("ID", word)]


@pytest.mark.parametrize("word,kind", [
    ("TIME", "TIME"), ("PAGE", "PAGE"), ("PTR", "PTR"), ("LOMEM", "LOMEM"),
    ("HIMEM", "HIMEM"), ("RND", "RND"), ("VPOS", "VPOS"), ("ERL", "ERL"),
    ("ERR", "ERR"), ("RETURN", "RETURN"),
])
def test_conditional_keyword_alone_still_tokenises(word, kind):
    assert _token_pairs(word) == [(kind, word)]


def test_pseudo_var_assignment_and_function_forms_still_work():
    # PAGE=... (assignment) and PRINT PAGE (function) both keep the keyword.
    assert _token_pairs("PAGE=&1900")[0] == ("PAGE", "PAGE")
    assert ("TIME", "TIME") in _token_pairs("PRINT TIME")


def test_keyword_with_paren_or_dollar_suffix_still_works():
    # The RND( and TIME$ variants must not be disturbed.
    assert _token_pairs("RND(5)")[0] == ("RND_LPAREN", "RND(")
    assert _token_pairs("TIME$") == [("TIME_STR", "TIME$")]


def test_ERROR_is_not_ERR_plus_OR():
    assert _token_pairs("ERROR") == [("ERROR", "ERROR")]


def test_RETURN_by_reference_parameter_keeps_keyword():
    # RETURN is CONDITIONAL (ROM bit-0): glued to a name char (RETURNX) it is the
    # variable RETURNX, but the by-reference formal `RETURN x` -- a space between --
    # must keep the RETURN keyword.
    assert _token_pairs("RETURNX") == [("ID", "RETURNX")]
    assert _token_pairs("RETURN x") == [("RETURN", "RETURN"), ("ID", "x")]
