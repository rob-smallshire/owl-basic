"""Phase 0 regression net: can the front-end still turn each corpus file into an AST?

This is deliberately minimal. It drives the parser the same way main.py does for
the text path (skipping detokenization, since the .bbctxt files are already plain
BASIC text), and asserts only that a parse tree comes back. As the Python 2->3 port
proceeds in Phase 1, the number of passing files is our progress metric.
"""
import glob
import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = sorted(glob.glob(os.path.join(HERE, "*.bbctxt")))

# IDs are just the bare feature name (e.g. "for_next_test") for readable output.
CORPUS_IDS = [os.path.splitext(os.path.basename(p))[0] for p in CORPUS]


class _Options:
    """Stand-in for the optparse options object main.py threads through parse()."""
    debug_lex = False
    verbose = False
    use_clr = False


# Known grammar-coverage gaps surfaced by the corpus (pre-existing, not Py2->3
# regressions). Keyed by corpus id -> reason. These are xfail rather than deleted
# so the gap stays visible and flips to a failure (xpass) the moment it's fixed.
KNOWN_GAPS = {
    "function_inference": "grammar: 'IF <cond> THEN =<expr>' (function return in "
                          "single-branch IF, no ELSE) not accepted; tied to DEF FN "
                          "type-inference work",
    "if_then_else_test": "grammar: 'IF <cond> THEN =<expr>' (function return in "
                         "single-branch IF, no ELSE) not accepted",
}


@pytest.mark.parametrize("source_filepath", CORPUS, ids=CORPUS_IDS)
def test_parses_to_ast(source_filepath, request):
    gap = KNOWN_GAPS.get(request.node.callspec.id)
    if gap is not None:
        request.node.add_marker(pytest.mark.xfail(reason=gap, strict=True))
    # Imported lazily so that a hard import failure (e.g. Py2 syntax) is reported
    # per-test rather than aborting collection of the whole module.
    import syntax.parser

    # BBC BASIC source is byte-oriented (effectively Latin-1 / CP1252), never
    # UTF-8 — e.g. 0x92 is a curly apostrophe. Latin-1 maps every byte 1:1 and
    # never raises, which matches how the byte-level lexer treats the input.
    with open(source_filepath, "r", encoding="latin-1") as f:
        data = f.read()
    if not data.endswith("\n"):
        data += "\n"

    parse_tree = syntax.parser.parse(data, _Options())
    assert parse_tree is not None
