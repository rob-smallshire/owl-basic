"""Differential test: our detokeniser vs the real BBC BASIC ROM (basictool).

basictool (https://github.com/ZornsLemma/basictool) runs an original BBC BASIC
ROM under 6502 emulation and detokenises via the ROM's own LIST — the ground
truth. This asserts our clean-room detokeniser produces identical output for the
de-protected Sphinx program. Skipped unless the basictool binary is available
(set OWL_BASICTOOL, or have it at ../basictool/basictool).
"""

import os
import re
import shutil
import subprocess

import pytest

from owl_basic.bbc_basic import detokenize

HERE = os.path.dirname(os.path.abspath(__file__))
_SPHINX = os.path.join(HERE, "data", "sphinx2-deprotected.bbc")


def _find_basictool():
    return (
        os.environ.get("OWL_BASICTOOL")
        or shutil.which("basictool")
        or next(
            (
                p
                for p in [os.path.join(HERE, "..", "..", "basictool", "basictool")]
                if os.path.isfile(p)
            ),
            None,
        )
    )


def _strip_line_numbers(text):
    """Map line number -> body, ignoring the (differently formatted) numbers."""
    result = {}
    for line in text.splitlines():
        m = re.match(r"\s*(\d+)(.*)", line)
        if m:
            result[int(m.group(1))] = m.group(2)
    return result


_basictool = _find_basictool()


@pytest.mark.skipif(
    _basictool is None or not os.path.isfile(_SPHINX),
    reason="needs the basictool binary and the de-protected Sphinx fixture",
)
def test_detokeniser_matches_real_rom_on_sphinx():
    ours = _strip_line_numbers(detokenize(open(_SPHINX, "rb").read()))
    rom_text = subprocess.run(
        [_basictool, "-2", "--input-tokenised", _SPHINX, "-"],
        capture_output=True, text=True, check=True,
    ).stdout
    rom = _strip_line_numbers(rom_text)
    assert set(ours) == set(rom)
    mismatches = {n: (ours[n], rom[n]) for n in ours if ours[n] != rom[n]}
    assert not mismatches, "lines differ from the real ROM: %r" % list(mismatches)[:5]
