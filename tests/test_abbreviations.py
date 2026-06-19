"""OWL expands BBC BASIC keyword abbreviations (via oaknut-basic) so abbreviated
listings -- as common in the BBC Micro Bot one-liners -- parse and analyse.

A trailing dot abbreviates a keyword (``P.``=PRINT, ``MO.``=MODE, ``F.``/``N.``=
FOR/NEXT). OWL's lexer reads full keywords only, so the front end normalises
abbreviations first; see :mod:`owl_basic.abbreviations`.
"""
from owl_basic.abbreviations import expand_numbered_lines, expand_unnumbered
from owl_basic.analysis import analyse


def test_expands_common_abbreviations():
    assert expand_unnumbered('P."HI"\n') == 'PRINT"HI"\n'
    assert expand_unnumbered('MO.7:CLS\n') == 'MODE7:CLS\n'
    assert expand_unnumbered('F.I=1TO9:P.I:N.\n') == 'FORI=1TO9:PRINTI:NEXT\n'


def test_full_keywords_pass_through_unchanged():
    assert expand_unnumbered('PRINT"HI"\n') == 'PRINT"HI"\n'


def test_numbered_lines_keep_their_numbers():
    # GOTO/GOSUB depend on the real line numbers, so only bodies are normalised.
    assert expand_numbered_lines([(10, ' P."HI"'), (20, ' G.10')]) == [
        (10, ' PRINT"HI"'),
        (20, ' GOTO10'),
    ]


def test_expansion_falls_back_rather_than_raising():
    # A line past BBC BASIC's length limit cannot be tokenised; expansion must
    # return the source unchanged, never raise.
    long_line = 'PRINT "' + "X" * 300 + '"\n'
    assert expand_unnumbered(long_line) == long_line


def test_analyse_accepts_abbreviated_source():
    program = analyse('MO.7\nP."HELLO"\n', name="abbr")
    assert program is not None
