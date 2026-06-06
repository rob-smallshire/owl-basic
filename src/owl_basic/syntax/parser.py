import sys
import logging

import ply.lex as lex
import ply.yacc as yacc

from . import grammar
from . import lexer

__author__ = 'rjs'

def buildLexer(options):
    logging.debug("buildLexer")
    if options.verbose:
        sys.stderr.write("Building lexer...")
    # Build the lexer and parser

    lx = lex.lex(lexer)
    if options.verbose:
        sys.stderr.write("done\n")

    return lx

def tokenize(data, lexer):
    '''Lex the data and exit.

    Args:
        data: The data to be lexed.
        lexer: The lexer instance to do the lexing.
    '''
    # Give the lexer some input
    lexer.input(data)

    # Tokenize
    while 1:
        tok = lexer.token()
        if not tok: break      # No more input
        print(tok)
    # Running the lexer twice on the same input screws up the line numbers, so stop here.
    sys.exit(0) 

# The LALR tables are expensive to build but identical for every parse, so the
# parser is constructed once and cached. write_tables=False keeps construction
# entirely in memory: when owl_basic is installed as a wheel the grammar module
# lives in a possibly read-only site-packages, where writing parsetab/parser.out
# would either fail or litter the install.
_basic_parser = None

def buildParser(options):
    logging.debug("buildParser")
    global _basic_parser
    if _basic_parser is None:
        if options.verbose:
            sys.stderr.write("Building parser... ")
        _basic_parser = yacc.yacc(
            module=grammar,
            write_tables=False,
            debug=False,
            errorlog=yacc.NullLogger(),  # silence "unused token" grammar warnings
        )
        if options.verbose:
            sys.stderr.write("done\n")

    return _basic_parser

def parse(data, options):
    logging.debug("parse")
    if options.verbose:
        sys.stderr.write("Parsing...")

    lexer = buildLexer(options)

    if options.debug_lex:
        tokenize(data, lexer)

    parser = buildParser(options)

    del grammar.syntax_errors[:]  # reset; p_error appends, callers read after
    parse_tree = parser.parse(data, lexer=lexer, tracking=True)
    if options.verbose:
        sys.stderr.write("done\n")

    return parse_tree