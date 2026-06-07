"""End-to-end: play the compiled Sphinx Adventure under program control.

This compiles the whole de-protected adventure, then drives it with the
published solution while reacting to the game's pseudo-random events (the dwarf
that follows you, and the lamp running low). It exercises the full stack
interactively -- movement, the comma-delimited DATA tables, dynamic RESTORE of
room descriptions, dynamically-scoped LOCALs/parameters, combat, and the
faithful BBC RND -- and is reproducible because RND starts from the BBC cold
seed and Sphinx never re-seeds.
"""

import os
import shutil
import sys

import pytest

from conftest import requires_dotnet_toolchain
from helpers import FIXTURES_DIRPATH, find_owlruntime_dll
from helpers.sphinx_player import load_walkthrough, play

from owl_basic.analysis import analyse_numbered_lines
from owl_basic.bbc_basic.detokenizer import detokenize_lines

_SPHINX = os.path.join(FIXTURES_DIRPATH, "data", "sphinx2-deprotected.bbc")
_SOLUTION = os.path.join(FIXTURES_DIRPATH, "data", "sphinx_solution.txt")


@requires_dotnet_toolchain
@pytest.mark.skipif(sys.platform == "win32",
                    reason="the player uses select() on a pipe (POSIX only)")
def test_plays_through_collecting_treasure_and_fighting_the_dwarf(
        dotnet_backend, tmp_path):
    program = analyse_numbered_lines(
        detokenize_lines(open(_SPHINX, "rb").read()), name="sphinx")
    dll_filepath = dotnet_backend.generate(program, tmp_path)
    shutil.copy(find_owlruntime_dll(), tmp_path)

    # No seed -> the faithful BBC cold seed, so this run is deterministic.
    result = play(dll_filepath, load_walkthrough(_SOLUTION), seed=None)

    # The compiled game must never fall over: any in-game death is a clean
    # "reincarnate?" prompt, never an unhandled CLR exception.
    assert not result["crashed"], result["stderr"]

    # It navigates a large part of the map (movement, exit and description
    # tables, and dynamic RESTORE of room text all working) ...
    assert result["rooms_seen"] >= 20
    assert "You are on the top of a mountain" in result["transcript"]
    # ... collects treasure (scoring works) ...
    assert result["max_score"] >= 100
    # ... refuels the lamp when it runs low ...
    assert result["lamp_rubs"] >= 1
    # ... and meets and defeats the dwarf that starts following it.
    assert result["dwarf_kills"] >= 1
    assert "You killed a dwarf" in result["transcript"]
