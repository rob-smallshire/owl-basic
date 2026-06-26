"""errors.internal()/fatalError() must raise, not sys.exit().

The compiler is a library: a bail-out from deep in a pass (an unsupported
construct, a violated invariant) used to call ``sys.exit(1)``, which is
uncatchable by callers and killed the corpus harness mid-run (e.g.
Tau93-b/JUL93.Advent, whose type check reaches errors.internal). They now raise
``InternalError`` (an ``OwlBasicError``), so the CLI reports it and tests/tools
can catch it.
"""
import pytest

from owl_basic import errors
from owl_basic.exceptions import InternalError, OwlBasicError


def test_internal_raises_internal_error():
    with pytest.raises(InternalError, match="boom"):
        errors.internal("boom")


def test_fatal_error_raises_internal_error():
    with pytest.raises(InternalError, match="kaboom"):
        errors.fatalError("kaboom")


def test_internal_error_is_an_owl_basic_error():
    # The CLI catches OwlBasicError, so InternalError must be in that family.
    assert issubclass(InternalError, OwlBasicError)
