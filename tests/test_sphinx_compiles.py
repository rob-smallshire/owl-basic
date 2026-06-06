"""End-to-end: the whole Sphinx Adventure compiles to a .NET assembly.

This drives the full front-end and the dotnet backend over the de-protected
Sphinx program and asserts it assembles. (Running it is an interactive
adventure loop, so this test stops at assembly.)
"""

import os

from conftest import requires_dotnet_toolchain
from helpers import FIXTURES_DIRPATH

from owl_basic.analysis import analyse_numbered_lines
from owl_basic.bbc_basic.detokenizer import detokenize_lines

_SPHINX = os.path.join(FIXTURES_DIRPATH, "data", "sphinx2-deprotected.bbc")


def test_sphinx_analyses_with_every_line_parsing():
    # No lenient recovery needed: all lines parse (anti-listing poke, lone-dot
    # and chained-ELSE quirks all handled), so every PROC/FN is defined.
    data = open(_SPHINX, "rb").read()
    program = analyse_numbered_lines(detokenize_lines(data), name="sphinx")
    assert "PROCC" in program.entry_points     # the chained-ELSE DEFPROCC
    assert "PROCE" in program.entry_points     # the de-protected DEFPROCE


@requires_dotnet_toolchain
def test_sphinx_adventure_assembles(dotnet_backend, tmp_path):
    data = open(_SPHINX, "rb").read()
    program = analyse_numbered_lines(detokenize_lines(data), name="sphinx")
    dll_filepath = dotnet_backend.generate(program, tmp_path)
    assert dll_filepath.exists() and dll_filepath.stat().st_size > 0
