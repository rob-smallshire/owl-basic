import sys
import logging

error_log = set()

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