import logging

from owl_basic.exceptions import InternalError

error_log = set()
_reported_errors = []  # the error (not warning) messages this compilation

def reset():
    """Clear the per-compilation diagnostic state.

    warning()/error() log each distinct message only once via error_log. That
    set is process-global, so without resetting it between compilations a
    diagnostic emitted by one program would be silently suppressed in the next
    (and tests compiling several programs in one process pollute each other).
    The error list, which the driver checks to refuse code generation for a
    program that did not type-check, is reset alongside it. Call at the start of
    every compilation.
    """
    error_log.clear()
    _reported_errors.clear()

def reported_errors():
    """The error messages reported during the current compilation (no warnings).

    A non-empty result means the program did not type-check, so a backend must
    not lower it -- recovery is only to collect every diagnostic, not to license
    generating code for a broken program.
    """
    return list(_reported_errors)

def warning(message):
    if message not in error_log:
        logging.warning(message)
        error_log.add(message)

def error(message):
    if message not in error_log:
        logging.error(message)
        error_log.add(message)
        _reported_errors.append(message)

def fatalError(message):
    logging.critical(message)
    raise InternalError(message)

def internal(message):
    logging.critical(message)
    raise InternalError(message)