#!ipy

# .NET Framework
import clr
clr.AddReference('System.Xml')
from System.Xml import XmlTextWriter, Formatting

# Python Standard Library
import sys
from optparse import OptionParser



import ply.lex as lex
import ply.yacc as yacc

import bbc_lexer
import bbc_grammar

def tokenize(data):
    # Give the lexer some input
    lex.input(data)

    # Tokenize
    while 1:
        tok = lex.token()
        if not tok: break      # No more input
        print tok

if __name__ == '__main__':
    
    parser = OptionParser()
    parser.add_option("-l", "--lex", action='store_true', dest='lex', default=False)
    
    (options, args) = parser.parse_args();
        
    filename = args[0]
    
    # Read the file
    f = open(filename, 'r')
    data = f.read()
    f.close()
    
    # Build the lexer and parser
    lex.lex(bbc_lexer)
    
    if options.lex:
        tokenize(data)
        
    yacc.yacc(module=bbc_grammar, debug = 1)
    
    parse_tree = yacc.parse(data)
        
    output_filename = filename + ".xml"
    
    writer = XmlTextWriter(output_filename, None)
    writer.Formatting = Formatting.Indented
    writer.WriteComment("XML Parse Tree")
    parse_tree.xml(writer)
    writer.Flush()
    writer.Close()