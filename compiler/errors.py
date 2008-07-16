import sys

def warning(message):
    sys.stderr.write("Warning: ")
    sys.stderr.write(message)
    sys.stderr.write('\n')
    
def error(message):
    sys.stderr.write("Error: ")
    sys.stderr.write(message)
    sys.stderr.write('\n')
    
def internal(message):
    sys.stderr.write("Internal Compiler Error: ")
    sys.stderr.write(message)
    sys.stderr.write('\n')