"""Shared test helpers for OWL BASIC.

Pure functions only (no pytest dependency); pytest fixtures live in
``tests/conftest.py``. Importable as ``helpers`` because ``tests`` is on the
pytest ``pythonpath`` (see ``pyproject.toml``).
"""

import glob
import os

from owl_basic.analysis import analyse
from owl_basic.syntax import parser as _parser
from owl_basic.syntax.ast import DefineFunction, ReturnFromFunction

# tests/helpers/ -> tests/ (where the .bbctxt fixtures live) -> repo root.
_HELPERS_DIRPATH = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIRPATH = os.path.dirname(_HELPERS_DIRPATH)
_REPO_DIRPATH = os.path.dirname(FIXTURES_DIRPATH)


class Options:
    """Minimal options object accepted by the parser and analysis pipeline."""

    debug_lex = False
    verbose = False
    use_clr = False


def parse(source):
    """Parse BASIC *source* (a trailing newline is added if missing)."""
    if not source.endswith("\n"):
        source += "\n"
    return _parser.parse(source, Options())


def analyse_fixture(filename, name=None):
    """Analyse a ``.bbctxt`` fixture from the tests directory."""
    with open(os.path.join(FIXTURES_DIRPATH, filename), encoding="latin-1") as f:
        source = f.read()
    if name is None:
        name = os.path.splitext(os.path.basename(filename))[0]
    return analyse(source, name=name)


def define_functions(source):
    """Return the top-level ``DEF FN`` nodes parsed from *source*."""
    tree = parse(source)
    return [s for s in tree.statements.statements if isinstance(s, DefineFunction)]


def walk(node):
    """Yield *node* and every descendant AST node (depth-first)."""
    yield node
    for child in node.children.values():
        for sub in (child if isinstance(child, list) else [child]):
            if sub is not None and hasattr(sub, "children"):
                yield from walk(sub)


def returns_by_function(source):
    """Map each ``DEF FN`` name to the list of expressions it returns.

    Attributes every ``= expr`` (including those nested in IF clauses) to the
    function whose linear span it falls in -- enough for focused inference tests.
    """
    tree = parse(source)
    by_function = {}
    current = None
    seen = set()
    for statement in tree.statements.statements:
        if isinstance(statement, DefineFunction):
            current = statement.name
            by_function.setdefault(current, [])
        if current is None:
            continue
        for node in walk(statement):
            if isinstance(node, ReturnFromFunction) and id(node) not in seen:
                seen.add(id(node))
                by_function[current].append(node.returnValue)
    return by_function


def function_return_types(program):
    """Map each ``FN`` entry-point name in an analysed *program* to its type."""
    return {
        name: getattr(entry, "returnType", None)
        for name, entry in program.entry_points.items()
        if name.startswith("FN")
    }


def find_owlruntime_dll():
    """Locate a built net10 ``OwlRuntime.dll``, or ``None`` if absent."""
    pattern = os.path.join(
        _REPO_DIRPATH, "OwlRuntime", "OwlRuntime", "bin", "**", "net10.0",
        "OwlRuntime.dll",
    )
    matches = glob.glob(pattern, recursive=True)
    return matches[0] if matches else None
