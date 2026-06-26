"""GOTO/GOSUB to a constant line that does not exist.

``LineMapper.logicalToPhysical`` resolved a target via ``list.index``, which
raised a bare ``ValueError: x not in list`` -- crashing the front end -- when
the target line was absent. The BBC interpreter reports "No such line"; the
compiler now rejects it as a CompileError. Surfaced by Tau89-b/NOV89.MODS.
"""
import pytest

from owl_basic.analysis import analyse_numbered_lines
from owl_basic.exceptions import CompileError


def _analyse(lines):
    return analyse_numbered_lines(lines, name="t", source_filepath="t")


@pytest.mark.parametrize("branch", ["GOTO 9999", "GOSUB 9999"])
def test_branch_to_missing_line_is_a_clean_compile_error(branch):
    with pytest.raises(CompileError, match="does not exist"):
        _analyse([(10, " " + branch), (20, " END")])


def test_branch_to_existing_line_still_works():
    program = _analyse([(10, " GOTO 30"), (20, " PRINT 1"), (30, " END")])
    assert program is not None
