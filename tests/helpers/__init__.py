"""Shared test helpers for OWL BASIC.

Pure functions only (no pytest dependency); pytest fixtures live in
``tests/conftest.py``. Importable as ``helpers`` because ``tests`` is on the
pytest ``pythonpath`` (see ``pyproject.toml``).
"""

import glob
import os
import shutil
import sys

from pathlib import Path

from owl_basic.analysis import analyse
from owl_basic.cli import _analyse_source
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
    """Analyse a ``.bbctxt`` fixture, dispatching on its form like the CLI.

    A numbered listing (e.g. ragged-num) is analysed by its real line numbers and
    an un-numbered snippet with synthesised ones -- the same dispatch
    ``_analyse_source`` does -- so a numbered fixture is not mis-parsed as if its
    line numbers were part of the first statement.
    """
    return _analyse_source(
        Path(os.path.join(FIXTURES_DIRPATH, filename)), "latin-1")


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
    """Locate a built net10 ``OwlRuntime.dll`` (newest), or ``None`` if absent.

    There may be both Debug and Release builds; pick the most recently built so
    tests run against the latest runtime.
    """
    pattern = os.path.join(
        _REPO_DIRPATH, "OwlRuntime", "OwlRuntime", "bin", "**", "net10.0",
        "OwlRuntime.dll",
    )
    matches = glob.glob(pattern, recursive=True)
    return max(matches, key=os.path.getmtime) if matches else None


def copy_skia_deps(dest_dirpath):
    """Copy SkiaSharp's managed assembly and this platform's native library
    (flat, beside the program) into *dest_dirpath*, so a graphics-capture
    program can load SkiaSharp. A no-op if the build output lacks them."""
    runtime_dirpath = os.path.dirname(find_owlruntime_dll())
    skia = os.path.join(runtime_dirpath, "SkiaSharp.dll")
    if os.path.exists(skia):
        shutil.copy(skia, dest_dirpath)
    if sys.platform == "darwin":
        native = "runtimes/osx*/native/libSkiaSharp.dylib"
    elif sys.platform.startswith("linux"):
        native = "runtimes/linux*/native/libSkiaSharp.so"
    else:
        native = "runtimes/win*/native/libSkiaSharp.dll"
    for path in glob.glob(os.path.join(runtime_dirpath, native)):
        shutil.copy(path, dest_dirpath)
        break
