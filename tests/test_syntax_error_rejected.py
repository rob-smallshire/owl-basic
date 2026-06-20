"""A source that does not parse is rejected gracefully, not limped through.

When the parser hits a syntax error it logs it and recovers a partial tree so it
can report further errors. That recovered tree must not then be analysed as if it
were a real program (a corrupted/garbage toot -- keyword soup, stray operators --
would be mis-compiled). A source with any syntax error is rejected with a clear
CompileError naming the first one.
"""
import pytest

from owl_basic.analysis import analyse
from owl_basic.exceptions import CompileError


def test_keyword_soup_is_rejected():
    with pytest.raises(CompileError) as excinfo:
        analyse("AND\n", name="t")
    assert "parse" in str(excinfo.value).lower()


def test_stray_operator_is_rejected():
    with pytest.raises(CompileError):
        analyse("PAGE |PRINT PLOT\n", name="t")


def test_well_formed_program_still_compiles():
    analyse('PRINT "ok"\nEND\n', name="t")  # no exception
