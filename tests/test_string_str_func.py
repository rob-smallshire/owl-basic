"""STRING$(count, source) -- a standard BBC BASIC function that repeats a string.

The lexer already recognised ``STRING$(`` but the grammar production was a TODO,
so it failed to parse; this covers the implemented form.
"""
from helpers import parse, walk
from owl_basic.syntax.ast import StringStrFunc


def _first_string_str(source):
    return next(
        (n for n in walk(parse(source)) if isinstance(n, StringStrFunc)), None
    )


def test_string_str_parses():
    assert _first_string_str('A$=STRING$(5,"x")\n') is not None


def test_string_str_has_count_and_source():
    node = _first_string_str('A$=STRING$(3,"ab")\n')
    assert node.count is not None and node.source is not None


def test_string_str_in_expression():
    assert _first_string_str('PRINT STRING$(N,CHR$(32))+"!"\n') is not None
