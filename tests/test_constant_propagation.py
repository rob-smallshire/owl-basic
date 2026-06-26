"""General constant propagation: a scalar whose every assignment is the same
constant is substituted by that literal wherever it is definitely assigned.

This is a general pass, not an EVAL feature. The soundness guard is
definite-assignment over the per-method CFG: a read that can run before the
assignment (the RUN idiom) is never propagated. See docs/constant-propagation.md.
"""
from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse, analyse_numbered_lines
from owl_basic.syntax.ast import Variable


def _reads_of(program, name):
    """Variable read nodes for *name* remaining after propagation."""
    found = []

    def walk(node):
        if (isinstance(node, Variable) and node.identifier == name
                and not getattr(node, "isLValue", False)):
            found.append(node)
        if hasattr(node, "forEachChild"):
            node.forEachChild(walk)

    for blocks in program.ordered_basic_blocks.values():
        for block in blocks:
            for statement in block.statements:
                walk(statement)
    return found


# --- propagation happens -------------------------------------------------

def test_constant_scalar_read_is_replaced():
    program = analyse('N%=5\nM%=N%\nPRINT M%\nEND\n', name="cp")
    assert _reads_of(program, "N%") == []          # the read of N% became 5


def test_chained_constants_resolve():
    program = analyse('A%=7\nB%=A%\nC%=B%\nPRINT C%\nEND\n', name="cp")
    assert _reads_of(program, "A%") == [] and _reads_of(program, "B%") == []


def test_string_constant_is_replaced():
    program = analyse('F$="hi"\nG$=F$\nPRINT G$\nEND\n', name="cp")
    assert _reads_of(program, "F$") == []


# --- soundness: not propagated when it could be wrong --------------------

def test_use_before_assignment_is_not_propagated():
    # The RUN idiom: line 10 reads n% before line 20 assigns it, so n% is 0 there,
    # not 42. Definite-assignment must leave the line-10 read alone.
    program = analyse_numbered_lines(
        [(10, "PRINT n%"), (20, "n% = 42"), (30, "END")], name="cp")
    assert _reads_of(program, "n%")                # the read survives


def test_assignment_in_one_if_branch_is_not_propagated():
    # V% assigned only on the THEN path; a use after the join is not definitely
    # assigned.
    program = analyse_numbered_lines(
        [(10, "IF A% THEN V% = 5"), (20, "M% = V%"), (30, "PRINT M%"), (40, "END")],
        name="cp")
    assert _reads_of(program, "V%")


def test_reassigned_variable_is_not_propagated():
    program = analyse('Z%=1\nZ%=2\nM%=Z%\nPRINT M%\nEND\n', name="cp")
    assert _reads_of(program, "Z%")


def test_input_variable_is_not_propagated():
    program = analyse('INPUT X%\nM%=X%\nPRINT M%\nEND\n', name="cp")
    assert _reads_of(program, "X%")


def test_for_variable_is_not_propagated():
    program = analyse('FOR I%=1 TO 3\nPRINT I%\nNEXT\nEND\n', name="cp")
    assert _reads_of(program, "I%")


def test_int64_scalar_is_left_alone():
    # %% (int64) operands are deliberately not propagated (shift-width semantics).
    program = analyse('W%%=1\nM%=W%%\nPRINT M%\nEND\n', name="cp")
    assert _reads_of(program, "W%%")


# --- end-to-end ----------------------------------------------------------

@requires_dotnet_toolchain
def test_propagation_into_for_limit_runs(compile_and_run):
    out = compile_and_run(analyse(
        'L%=3\nFOR I%=1 TO L%\nPRINT I%\nNEXT\nEND\n', name="cp"))
    assert out.splitlines() == ["1", "2", "3"]


@requires_dotnet_toolchain
def test_chained_constant_runs(compile_and_run):
    out = compile_and_run(analyse('A%=7\nB%=A%\nPRINT B%\nEND\n', name="cp"))
    assert out.strip() == "7"
