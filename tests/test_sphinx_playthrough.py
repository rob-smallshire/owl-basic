"""End-to-end: play the compiled Sphinx Adventure to completion under program
control.

This compiles the whole de-protected adventure and drives it with the published
solution, reacting to the game's pseudo-random events the walkthrough omits --
the dwarf that follows you (kill it with the sword, re-collecting it after each
throw; with the axe once the sword has melted on the ogre) and the lamp running
low (rub it). It exercises the full stack interactively: movement, the
comma-delimited DATA tables, dynamic RESTORE of room descriptions, dynamically
scoped LOCALs and parameters, combat, a GOTO out of a PROC for the winning
screen, and the faithful BBC RND.

RND is seeded (as the game's own RND(-n) would) so the random encounters fall
where this route can handle them, giving a deterministic full solve. The
unseeded BBC cold seed plays just as faithfully but its late-game dwarf luck is
fatal, so that run is checked separately for robust progress rather than a win.
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
# The authoritative Paul Sanderson / Impact Games Club route (transcribed from
# sphinx_solution.jpeg); the most complete one, scoring the full 800. See
# tests/data/SPHINX_ADVENTURE.md.
_SOLUTION = os.path.join(FIXTURES_DIRPATH, "data", "sphinx_solution4.txt")

# A seed for which this driver solves the whole game (the random encounters fall
# where the sword/axe and lamp handling can deal with them).
_WINNING_SEED = 1

requires_posix = pytest.mark.skipif(
    sys.platform == "win32",
    reason="the player uses select() on a pipe (POSIX only)")


def _compile_sphinx(dotnet_backend, tmp_path):
    program = analyse_numbered_lines(
        detokenize_lines(open(_SPHINX, "rb").read()), name="sphinx")
    dll_filepath = dotnet_backend.generate(program, tmp_path)
    shutil.copy(find_owlruntime_dll(), tmp_path)
    return dll_filepath


@pytest.mark.slow
@requires_dotnet_toolchain
@requires_posix
def test_solves_the_whole_game(dotnet_backend, tmp_path):
    dll_filepath = _compile_sphinx(dotnet_backend, tmp_path)
    result = play(dll_filepath, load_walkthrough(_SOLUTION), seed=_WINNING_SEED, idle_seconds=0.18)

    assert not result["crashed"], result["stderr"]
    assert result["won"], (
        "did not reach the winning screen; "
        "last score %s at command %s" % (result["max_score"],
                                         result["commands_used"]))
    assert result["max_score"] == 800        # every treasure delivered
    assert result["dwarf_kills"] >= 1        # at least one dwarf fought off
    assert "You've solved the puzzle" in result["transcript"]


@pytest.mark.slow
@requires_dotnet_toolchain
@requires_posix
def test_cold_seed_plays_robustly(dotnet_backend, tmp_path):
    # The faithful power-on (cold) seed: the game is deterministic and never
    # crashes; the run gets deep and scores well before late dwarf luck ends it.
    dll_filepath = _compile_sphinx(dotnet_backend, tmp_path)
    result = play(dll_filepath, load_walkthrough(_SOLUTION), seed=None, idle_seconds=0.18)

    assert not result["crashed"], result["stderr"]
    assert result["rooms_seen"] >= 40
    assert result["dwarf_kills"] >= 1
    assert result["max_score"] >= 400
    assert "You are on the top of a mountain" in result["transcript"]
