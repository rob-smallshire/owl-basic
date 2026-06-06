"""Symbol-table construction must not recurse per control-flow-graph node.

The symbol-table visitor walks the CFG depth-first; doing that with the call
stack overflows on large programs (real Sphinx triggers a RecursionError). A
long linear program reproduces it without needing the whole adventure.
"""

from owl_basic.analysis import analyse


def test_long_linear_program_builds_symbol_tables_without_stack_overflow():
    source = "\n".join("X%%=%d" % i for i in range(3000)) + "\n"
    # Must complete (no RecursionError) and produce a usable program.
    program = analyse(source, "long")
    assert program is not None
