#!ipy

# Python Standard Library
import sys
import re
import logging
from optparse import OptionParser

import ply.lex as lex
import ply.yacc as yacc

import bbc_lexer
import bbc_grammar
import xml_visitor
import parent_visitor
import simplify_visitor
import typecheck_visitor

#from errors import warning

logging._srcfile = None
logging.basicConfig(level=logging.DEBUG)

def tokenize(data):
    # Give the lexer some input
    lex.input(data)

    # Tokenize
    while 1:
        tok = lex.token()
        if not tok: break      # No more input
        print tok

def xml(tree, filename):
    xmlv = xml_visitor.XmlVisitor(filename)
    tree.accept(xmlv)
    xmlv.close()

if __name__ == '__main__':
    
    parser = OptionParser()
    parser.add_option("-x", "--debug-lex", action='store_true', dest='debug_lex', default=False)
    parser.add_option("-l", "--line-numbers", action='store_true', dest="line_numbers", default=False)
    parser.add_option("-c", "--debug-no-clr", action='store_false', dest='use_clr', default=True)
    parser.add_option("-s", "--debug-no-simplification", action='store_false', dest='use_simplification', default=True)
    parser.add_option("-t", "--debug-no-typecheck", action='store_false', dest='use_typecheck', default=True)
    
    (options, args) = parser.parse_args();

    if options.use_clr:
        # .NET Framework
        import clr
        clr.AddReference('System.Xml')
        from System.Xml import XmlTextWriter, Formatting

    if len(args) == 0:
        sys.stderr.write("No filename supplied.\n")
        sys.exit(1)
            
    filename = args[0]
    
    # Read the file - processing it for line numbers if necessary
    f = open(filename, 'r')
    if options.line_numbers:
        line_number_regex = re.compile(r'\s*(\d+)\s*(.*)')
        physical_line = 0
        logical_line = 0
        physical_to_logical_line = [0]
        line_bodies = []
        while True:
            line = f.readline()
            if not line:
                break
            physical_line += 1
            m = line_number_regex.match(line)
            if not m:
                logging.error("Missing line number at physical line %d (after logical line %d)", physical_line, logical_line)
                sys.exit(1)
            logical_line = int(m.group(1))
            physical_to_logical_line.append(logical_line)
            line_bodies.append(m.group(2))
        print physical_to_logical_line
        data = '\n'.join(line_bodies)
    else:
        data = f.read()
    f.close()
    
    print data
    
    if not data.endswith('\n'):
        logging.warning("Missing newline at end of file")
        data += '\n'
    
    # Build the lexer and parser
    lex.lex(bbc_lexer)
    
    if options.debug_lex:
        tokenize(data)
        
    yacc.yacc(module=bbc_grammar, debug = 1)
    
    parse_tree = yacc.parse(data)
    
    parse_tree.accept(parent_visitor.ParentVisitor())
    
    if options.use_simplification:
        parse_tree.accept(simplify_visitor.SimplificationVisitor())
    
    if options.use_typecheck:
        parse_tree.accept(typecheck_visitor.TypecheckVisitor())
        
    if options.use_clr:
        output_filename = filename + ".xml"
        print "Creating %s" % output_filename
        xml(parse_tree, output_filename)
    
    # Structural analysis
    #flatten(parse_tree)
    #assignIds(parse_tree)
    #correlateForNext(parse_tree)
    #correlateRepeatUntil(parse_tree)
    #correlateWhileEndwhile(parse_tree)
    #correlateDefProcEndproc(parse_tree)
    #correlateDefFnEndFn(parse_tree)
    #resolveGotoGosub(parse_tree)
    #splitBasicBlock(parse_tree)
    #buildSymbolTable(parse_tree)
    
    # Type checking and casting
    #determineTypes(parse_tree)
    #typeCheck(parse_tree)
    
    # Optimisation
    #foldConstants(parse_tree)
    #elimiateCommonSubexpressions(parse_tree    opti