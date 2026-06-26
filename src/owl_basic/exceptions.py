"""Exception hierarchy for OWL BASIC.

A single base, :class:`OwlBasicError`, roots every error the package raises so
that callers can catch the whole family with one ``except``.
"""


class OwlBasicError(Exception):
    """Base class for all OWL BASIC errors."""


class ExtensionError(OwlBasicError):
    """Raised when a plug-in extension cannot be found or loaded."""


class CompileError(OwlBasicError):
    """Raised when a program cannot be compiled (e.g. unparseable source).

    By default the compiler is strict: an unparseable line is a CompileError.
    A lenient option recovers per line instead.
    """


class InternalError(OwlBasicError):
    """Raised when the compiler hits a state it cannot handle.

    Covers both genuine internal-invariant violations and not-yet-supported
    constructs that the back end bails out on. It is an ``OwlBasicError`` so the
    CLI reports it cleanly and callers (tests, the corpus harness) can catch it
    -- a library must never ``sys.exit()`` out from under its caller.
    """
