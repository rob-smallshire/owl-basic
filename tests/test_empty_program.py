"""A source with no BBC BASIC statements is rejected gracefully.

A toot that is prose (a blog link, say) rather than a program, or an empty file,
parses to no statements. Locating the program entry point then indexed the first
statement of an empty list and crashed with IndexError; it must instead report
that there is nothing to compile.
"""
import pytest

from owl_basic.analysis import analyse
from owl_basic.exceptions import CompileError


def test_empty_source_is_rejected():
    with pytest.raises(CompileError):
        analyse("\n", name="t")


def test_blank_lines_only_is_rejected():
    with pytest.raises(CompileError):
        analyse("\n\n\n", name="t")


def test_message_mentions_no_statements():
    with pytest.raises(CompileError) as excinfo:
        analyse("", name="t")
    assert "statement" in str(excinfo.value).lower()
