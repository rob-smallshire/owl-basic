'''
Convert longjumps (GOTO out of a function or procedure)
to exceptions with appropriate handlers.
'''

import logging

from longjump_visitor import LongjumpVisitor

logger = logging.getLogger('flow.longjump_converter')

def convertLongjumpsToExceptions(parse_tree, line_mapper, options):
    logger.debug("convertLongjumpsToExceptions")
    # Insert longjumps where flow control jumps out of a procedure
    logging.info("Finding longjump locations")
    ljv = LongjumpVisitor(line_mapper)
    parse_tree.accept(ljv)
    logging.info("Creating long jumps")
        
    ljv.createLongjumps()
