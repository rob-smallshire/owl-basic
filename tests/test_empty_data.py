"""An empty DATA statement is valid and must not crash the lexer.

DATA captures the rest of its line as raw items. With no items (a bare `DATA`, as
some programs use as a list terminator) the lexer's rule called an undefined
`fatalError`, raising NameError. An empty DATA is legal -- its content is just the
empty string.
"""
from helpers import walk
from owl_basic.analysis import analyse
from owl_basic.syntax.ast import Data


def _data_nodes(source):
    return [n for n in walk(analyse(source, name="t").parse_tree)
            if isinstance(n, Data)]


def test_bare_data_analyses():
    # Was: NameError 'fatalError' is not defined.
    nodes = _data_nodes("DATA\nREAD a$\n")
    assert len(nodes) == 1
    assert nodes[0].data == ""


def test_data_with_items_still_works():
    nodes = _data_nodes("DATA 1,2,3\nREAD a,b,c\n")
    assert nodes[0].data == " 1,2,3"


def test_data_among_other_statements():
    analyse('PRINT "x":DATA\n', name="t")  # no crash
