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
