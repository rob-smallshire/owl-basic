import sys

def warning(level, message):
    sys.stderr.write("Warning: ")
    sys.stderr.write(message)
    sys.stderr.write('\n')
    
