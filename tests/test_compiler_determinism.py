"""The compiler must be deterministic: the same source yields the same output.

CFG edges are held in sets of vertex objects, whose iteration order follows
object identity and so varies between processes. Loop correlation and basic-block
ordering used to walk those sets directly, so the verdict (compile vs reject) and
the emitted block layout could differ run to run -- a program would compile in
one process and be rejected in another, or assemble to a different (sometimes
broken) layout. Every such walk now goes in stable creation-id order.

The non-determinism is *between* processes, so the meaningful check runs the
front end in separate subprocesses and compares.
"""
import hashlib
import subprocess
import sys
import textwrap

import pytest


def _run_in_subprocess(expr):
    """Evaluate *expr* in a fresh interpreter, returning its stdout (stripped)."""
    code = textwrap.dedent(
        """
        import hashlib
        from owl_basic.analysis import analyse
        from owl_basic.ext.backends.dotnet.emitter import emit_program
        from owl_basic.exceptions import OwlBasicError
        %s
        """
    ) % expr
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=120
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


# A program with a conditional branch and a loop: several vertices have more than
# one out-edge, so traversal order (if set-dependent) would change the layout.
_PROGRAM = (
    "C%=0\\n"
    "REPEAT\\n"
    "C%=C%+1\\n"
    "IF C%<5 UNTIL FALSE\\n"
    "UNTIL TRUE\\n"
    "PRINT C%\\n"
)


@pytest.mark.slow
def test_emitted_il_is_identical_across_processes():
    expr = (
        "il = emit_program(analyse('%s', name='t'), 't')\n"
        "print(hashlib.md5(il.encode()).hexdigest())"
    ) % _PROGRAM
    digests = {_run_in_subprocess(expr) for _ in range(3)}
    assert len(digests) == 1, "IL differs between processes: %r" % digests


@pytest.mark.slow
def test_correlation_verdict_is_identical_across_processes():
    # A conditional NEXT closing a FOR -- the dynamic-stack shape whose verdict
    # used to flip with traversal order. It must reject the same way every run.
    program = (
        "FOR Y=0 TO 2\\n"
        "FOR X=0 TO 2\\n"
        "IF X=0 NEXT\\n"
        "PRINT X\\n"
        "NEXT,\\n"
    )
    expr = (
        "import sys\n"
        "try:\n"
        "    analyse('%s', name='t'); print('compiles')\n"
        "except OwlBasicError: print('rejected')\n"
    ) % program
    verdicts = {_run_in_subprocess(expr) for _ in range(3)}
    assert len(verdicts) == 1, "verdict differs between processes: %r" % verdicts


def test_in_id_order_sorts_by_vertex_id():
    from owl_basic.correlation_visitor import _in_id_order

    class V:
        def __init__(self, i):
            self.id = i

    a, b, c = V(3), V(1), V(2)
    assert [v.id for v in _in_id_order({a, b, c})] == [1, 2, 3]
