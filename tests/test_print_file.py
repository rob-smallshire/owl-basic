"""PRINT to a file channel: ``PRINT#channel, expr, expr`` (the output analogue
of INPUT#/BPUT#).

This form reduces through ``print_stmt``'s third alternative,
``PRINT channel COMMA actual_arg_list``. That branch was guarded by the wrong
RHS length (``len(p) == 4`` for a 4-symbol production, whose ``len(p)`` is 5),
so it never ran: ``p[0]`` stayed ``None`` and every ``PRINT#`` crashed the
parser with ``AttributeError: 'NoneType' has no attribute 'lineNum'``. Surfaced
across ~74 Acorn User type-ins (e.g. Tau85-a/DEC84.FRYER, ``PRINT#f,e%,f%``).
"""
from helpers import parse, walk

from owl_basic.syntax.ast import PrintFile


def _only_print_file(source):
    tree = parse(source)
    nodes = [n for n in walk(tree) if isinstance(n, PrintFile)]
    assert len(nodes) == 1, f"expected one PrintFile, got {len(nodes)}"
    return nodes[0]


def test_print_file_single_item_parses():
    node = _only_print_file("PRINT#f, A\n")
    assert node.channel is not None
    assert node.items is not None


def test_print_file_multiple_items_parses():
    # The items are an actual_arg_list, so several comma-separated values land
    # in one PrintFile rather than the COMMA being mistaken for the items.
    node = _only_print_file("PRINT#f, e%, f%, kw%, nc%\n")
    assert len(node.items.arguments) == 4


def test_print_to_screen_is_unaffected():
    # The plain PRINT forms must still parse and not become PrintFile.
    tree = parse('PRINT "hi"; x\n')
    assert not any(isinstance(n, PrintFile) for n in walk(tree))
