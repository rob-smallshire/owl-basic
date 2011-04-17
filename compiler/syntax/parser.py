import sys
import logging

import ply.lex as lex
import ply.yacc as yacc

import grammar
import lexer

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
        print tok
    # Running the lexer twice on the same input screws up the line numbers, so stop here.
    sys.exit(0) 

def buildParser(options):
    logging.debug("buildParser")
    if options.verbose:
        sys.stderr.write("Building parser... ")

    basic_parser = yacc.yacc(module=grammar, picklefile="parsetab.pickle", debug=1)
    if options.verbose:
        sys.stderr.write("done\n")
    
    return basic_parser

def parse(data, options):
    logging.debug("parse")
    if options.verbose:
        sys.stderr.write("Parsing...")

    lexer = buildLexer(options)

    if options.debug_lex:
        tokenize(data, lexer)

    parser = buildParser(options)

    parse_tree = parser.parse(data, lexer=lexer, tracking=True)
    if options.verbose:
        sys.stderr.write("done\n")

    return parse_tree