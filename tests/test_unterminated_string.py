"""An unterminated string literal must not hang the lexer.

The string-literal rule was `"((?:[^"]+|"")*)"` -- a `[^"]+` nested inside a `*`,
the classic catastrophic-backtracking shape. On an unterminated string (no closing
quote, as produced by a corrupted/garbage line) the regex tried exponentially many
ways to find a closing quote that was not there, hanging the lexer. The fix makes
the inner alternation single-character so matching stays linear.
"""
import threading

import pytest

from owl_basic.analysis import analyse
from owl_basic.syntax import parser


class _Options:
    debug_lex = False
    verbose = False
    use_clr = False


@pytest.fixture(autouse=True)
def _warm_parser():
    # The first parse builds the LALR tables (seconds); do that outside the
    # per-test timeout so it measures only the unterminated-string parse.
    parser.parse("PRINT 1\n", _Options())


def _with_timeout(seconds, fn):
    # Run fn on a worker thread and wait at most `seconds`. A thread (not
    # signal.alarm, which is Unix-only) keeps this cross-platform: catastrophic
    # backtracking makes the worker miss the deadline, so the join returns while
    # it is still alive and we fail. The daemon worker dies with the process.
    result = {}

    def _run():
        try:
            result["value"] = fn()
        except BaseException as exc:  # marshalled to the caller and re-raised
            result["error"] = exc

    worker = threading.Thread(target=_run, daemon=True)
    worker.start()
    worker.join(seconds)
    if worker.is_alive():
        raise TimeoutError("took too long -- likely catastrophic backtracking")
    if "error" in result:
        raise result["error"]
    return result.get("value")


def test_long_unterminated_string_lexes_quickly():
    # 400 non-quote chars after an opening quote, never closed.
    source = 'PRINT "' + "A FOR EOR " * 40 + "\n"
    _with_timeout(5, lambda: parser.parse(source, _Options()))


def test_unterminated_string_analyses_without_hanging():
    source = 'PRINT "' + "x y z " * 60 + "\n"
    _with_timeout(5, lambda: analyse(source, name="t"))


def test_normal_and_escaped_strings_still_work():
    from helpers import walk
    from owl_basic.syntax.ast import LiteralString
    tree = parser.parse('A$="hi":B$="a""b"\n', _Options())
    values = [n.value for n in walk(tree) if isinstance(n, LiteralString)]
    assert "hi" in values
    assert 'a"b' in values  # "" is an escaped quote
