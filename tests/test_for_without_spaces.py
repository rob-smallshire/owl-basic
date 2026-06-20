"""FOR with no spaces around TO/STEP (and FOR glued to its counter) is valid.

Tweet-sized programs save bytes by dropping spaces: `FORX=0TO3STEP1` and the
abbreviated `F.L%=0TO358:N.` (which expands to `FORL%=0TO358:NEXT`). The lexer
already separates `0TO3` into `0 TO 3`, so these parse and run like their spaced
forms; these guard that.
"""
from conftest import requires_dotnet_toolchain
from helpers import walk
from owl_basic.analysis import analyse
from owl_basic.syntax.ast import ForToStep


def _for_loops(source):
    return [n for n in walk(analyse(source, name="t").parse_tree)
            if isinstance(n, ForToStep)]


def test_for_no_space_before_to_analyses():
    assert len(_for_loops("FOR X=0TO3:NEXT\n")) == 1


def test_for_glued_to_counter_analyses():
    # FORL%=... (no space after FOR), the shape abbreviation expansion produces.
    assert len(_for_loops("FORL%=0TO3:NEXT\n")) == 1


def test_for_no_space_with_step_analyses():
    assert len(_for_loops("FORX=0TO10STEP2:NEXT\n")) == 1


def test_abbreviated_for_next_analyses():
    # F. -> FOR, N. -> NEXT via abbreviation expansion, then no spaces around TO.
    assert len(_for_loops("F.L%=0TO5:N.\n")) == 1


@requires_dotnet_toolchain
def test_for_no_space_runs(compile_and_run):
    out = compile_and_run(analyse("FORX=1TO3:PRINT X:NEXT\n", name="t"))
    assert out.split() == ["1", "2", "3"]
