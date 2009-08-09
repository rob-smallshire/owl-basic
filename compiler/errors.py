import sys

error_log = set()

def warning(message):
    if message not in error_log:
        sys.stderr.write("Warning: ")
        sys.stderr.write(message)
        sys.stderr.write('\n')
        error_log.add(message)
    
def error(message):
    if message not in error_log:
        sys.stderr.write("Error: ")
        sys.stderr.write(message)
        sys.stderr.write('\n')
        error_log.add(message)

def fatalError(message):
    error(message)
    sys.exit(1)
    
def internal(message):
    sys.stderr.write("Internal Compiler Error: ")
    sys.stderr.write(message)
    sys.stderr.write('\n')
    sys.exit(1)