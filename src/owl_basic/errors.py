import sys
import logging

error_log = set()

def reset():
    """Clear the per-compilation diagnostic dedup set.

    warning()/error() log each distinct message only once via error_log. That
    set is process-global, so without resetting it between compilations a
    diagnostic emitted by one program would be silently suppressed in the next
    (and tests compiling several programs in one process pollute each other).
    Call at the start of every compilation.
    """
    error_log.clear()

def warning(message):
    if message not in error_log:
        logging.warning(message)
        error_log.add(message)
    
def error(message):
    if message not in error_log:
        logging.error(message)
        error_log.add(message)

def fatalError(message):
    logging.critical(message)
    sys.exit(1)
    
def internal(message):
    logging.critical(message)
    sys.exit(1)