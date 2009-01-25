#!ipy

# Python Standard Library
import sys
import re
import logging
import StringIO
from optparse import OptionParser

import ply.lex as lex
import ply.yacc as yacc

import errors
import bbc_lexer
import bbc_grammar
import bbc_ast
import xml_visitor
import parent_visitor
import separation_visitor
import simplify_visitor
import line_number_visitor
import typecheck_visitor
import flowgraph_visitor
import gml_visitor
import entry_point_visitor
import ast_utils
import flow_analysis
from line_mapper import LineMapper
import longjump_visitor
import symbol_table_visitor
import convert_sub_visitor

from Detoken import Decode

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

def xmlAst(tree, filename):
    xmlv = xml_visitor.XmlVisitor(filename)
    tree.accept(xmlv)
    xmlv.close()
    
def xmlCfg(tree, filename):
    gmlv = gml_visitor.GmlVisitor(filename)
    tree.accept(gmlv)
    gmlv.close()

if __name__ == '__main__':
    
    parser = OptionParser()
    parser.add_option("-x", "--debug-lex", action='store_true', dest='debug_lex', default=False)
    parser.add_option("-l", "--line-numbers", action='store_true', dest="line_numbers", default=False)
    parser.add_option("-c", "--debug-no-clr", action='store_false', dest='use_clr', default=True)
    parser.add_option("-p", "--debug-no-separation", action='store_false', dest='use_separation', default=True)
    parser.add_option("-s", "--debug-no-simplification", action='store_false', dest='use_simplification', default=True)
    parser.add_option("-t", "--debug-no-typecheck", action='store_false', dest='use_typecheck', default=True)
    parser.add_option("-f", "--debug-no-flowgraph", action='store_false', dest='use_flowgraph', default=True)
    parser.add_option("-e", "--debug-no-entrypoints", action='store_false', dest='use_entry_points', default=True)
    parser.add_option("-j", "--debug-no-longjumps", action='store_false', dest='use_longjumps', default=True)
    parser.add_option("-g", "--debug-no-convert-subs", action='store_false', dest='use_convert_subs', default=True)
    parser.add_option("-y", "--debug-no-symbol-tables", action='store_false', dest='use_symbol_tables', default=True)
    parser.add_option("-v", "--verbose", action='store_true', dest='verbose', default=False)
    
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
    
    if options.verbose:
        sys.stderr.write("Detokenizing...")
    #call the detokenize routine
    detokenized = StringIO.StringIO()
    lineNoNeeded = Decode(f.read(), detokenized)
    

    #lineNoNeeded is true if the file has line numbers (need testing for file without line numbers)
    #I dont know how to change the parameter on the command line

    f.close()
    
    if options.verbose:
        sys.stderr.write("done\n")
    
    detokenHandle = StringIO.StringIO(detokenized.getvalue())
    
    if options.verbose:
        sys.stderr.write("Mapping physical to logical line numbers... ")
    
    if options.line_numbers:
        line_number_regex = re.compile(r'\s*(\d+)\s*(.*)')
        physical_line = 0
        logical_line = 0
        physical_to_logical_map = [0]
        line_bodies = []
        while True:
            line = detokenHandle.readline()
            #print line   # ians debug line
            if not line:
                break
            physical_line += 1
            m = line_number_regex.match(line)
            if not m:
                logging.error("Missing line number at physical line %d (after logical line %d)", physical_line, logical_line)
                sys.exit(1)
            logical_line = int(m.group(1))
            physical_to_logical_map.append(logical_line)
            line_bodies.append(m.group(2))
        #print physical_to_logical_map
        data = '\n'.join(line_bodies)
    else:
        physical_to_logical_map = None
        data = detokenHandle.read()
    detokenHandle.close()
    
    if options.verbose:
        sys.stderr.write("done\n")
    
    if not data.endswith('\n'):
        logging.warning("Missing newline at end of file")
        data += '\n'
    
    if options.verbose:
        sys.stderr.write("Building lexer...")
    
    # Build the lexer and parser
    
    lex.lex(bbc_lexer)
    
    if options.verbose:
        sys.stderr.write("done\n")
    
    if options.debug_lex:
        tokenize(data)
    
    if options.verbose:
        sys.stderr.write("Builder parser... ")
        
    yacc.yacc(module=bbc_grammar, debug = 1)
    
    if options.verbose:
        sys.stderr.write("done\n")
        sys.stderr.write("Parsing...")
    
    parse_tree = yacc.parse(data)
    
    if options.verbose:
        sys.stderr.write("done\n")
        sys.stderr.write("Setting parents... ")
    
    parse_tree.accept(parent_visitor.ParentVisitor())
    
    if options.verbose:
        sys.stderr.write("done\n")
    
    if options.use_separation:
        if options.verbose:
            sys.stderr.write("Separating complex Abstract Syntax Tree nodes... ")
        parse_tree.accept(separation_visitor.SeparationVisitor())
        if options.verbose:
            sys.stderr.write("done\n")
    
    if options.use_simplification:
        if options.verbose:
            sys.stderr.write("Simplifying Abstract Syntax Tree... ")
        parse_tree.accept(simplify_visitor.SimplificationVisitor())
        if options.verbose:
            sys.stderr.write("done\n")
    
    lnv = line_number_visitor.LineNumberVisitor()
    parse_tree.accept(lnv)
    
    print lnv.line_to_stmt
    
    line_mapper = LineMapper(physical_to_logical_map, lnv.line_to_stmt)
                                
    if options.use_typecheck:
        if options.verbose:
            sys.stderr.write("Type checking... ")
        parse_tree.accept(typecheck_visitor.TypecheckVisitor())
        if options.verbose:
            sys.stderr.write("done\n")
        
    if options.use_clr:
        if options.verbose:
            sys.stderr.write("Creating XML AST... ")
        output_filename = filename + "_ast.xml"
        print "Creating %s" % output_filename
        xmlAst(parse_tree, output_filename)
        if options.verbose:
            sys.stderr.write("done\n") 
    
    if options.use_flowgraph:
        if options.verbose:
            sys.stderr.write("Creating Control Flow Graph...")
        parse_tree.accept(flowgraph_visitor.FlowgraphForwardVisitor(line_mapper))
        #parse_tree.accept(flowgraph_visitor.FlowgraphBackwardVisitor(lnv.line_to_stmt))
        if options.verbose:
            sys.stderr.write("done\n")
        
    if options.use_entry_points:
        if options.verbose:
            sys.stderr.write("Finding entry points...")
        epv = entry_point_visitor.EntryPointVisitor(line_mapper)
        parse_tree.accept(epv)
        first_statement = line_mapper.firstStatement()
        #print "first_statement = %s" % first_statement
        epv.mainEntryPoint(first_statement)
        if options.verbose:
            sys.stderr.write("done\n")

        if options.verbose:
            sys.stderr.write("Checking for direct execution of function or procedure bodies...")    
        # Check for incoming execution edges to entry points
        for entry_point in epv.entry_points:
            if isinstance(entry_point, bbc_ast.DefinitionStatement):
                if len(entry_point.inEdges) != 0:
                    errors.warning("Execution of procedure/function at line %s" % entry_point.lineNum)
                    # TODO: Could use ERROR statement here
                    raise_stmt = bbc_ast.Raise(type = "ExecutedDefinitionException")
                    ast_utils.insertStatementBefore(entry_point, raise_stmt)
                    raise_stmt.clearOutEdges()
                    entry_point.clearInEdges()
        if options.verbose:
            sys.stderr.write("done\n")
    
        # Tag each statement with its predecesor entry point
        if options.verbose:
            sys.stderr.write("Tagging statements with entry point\n")
        for entry_point in epv.entry_points:
            flow_analysis.tagSuccessors(entry_point)
        if options.verbose:
            sys.stderr.write("done\n")
    
    print epv.entry_points
    
    if options.use_longjumps:
        # Insert longjumps where flow control jumps out of a procedure
        if options.verbose:
            sys.stderr.write("Finding longjump locations")
        ljv = longjump_visitor.LongjumpVisitor(line_mapper)
        parse_tree.accept(ljv)
        if options.verbose:
            sys.stderr.write("done\n")
            sys.stderr.write("Creating long jumps")
            
        ljv.createLongjumps()
        
        if options.verbose:
            sys.stderr.write("done\n")
    
    print epv.entry_points
        
    if options.use_convert_subs:
        # Convert subroutines to procedures
        if options.verbose:
            sys.stderr.write("Convert subroutines to procedures")
        
        entry_points_to_remove = []
        entry_points_to_add = []
        for entry_point in epv.entry_points:
            print "entry_point = %s at %s" % (entry_point, entry_point.lineNum)
            # TODO: This will only work with simple (i.e. single entry) subroutines
            subname = iter(entry_point.entryPoints).next()
            if subname.startswith('SUB'):
                procname = subname
                assert len(entry_point.inEdges) == 0
                defproc = bbc_ast.DefineProcedure(name=procname, formalParameters=None)
                ast_utils.insertStatementBefore(entry_point, defproc)
                flow_analysis.deTagSuccessors(entry_point)
                entry_point.clearEntryPoints()
                entry_points_to_remove.append(entry_point)
                entry_points_to_add.append(defproc)
                flow_analysis.tagSuccessors(defproc)
        for eptr in entry_points_to_remove:
            epv.entry_points.remove(eptr)
        epv.entry_points.extend(entry_points_to_add)
        
        csv = convert_sub_visitor.ConvertSubVisitor()
        parse_tree.accept(csv)
                
        if options.verbose:
            sys.stderr.write("done\n")
    
    print epv.entry_points
        
    if options.use_symbol_tables:
        # Attach symbol tables to each statement
        if options.verbose:
            sys.stderr.write("Building symbol tables")
        
        stv = symbol_table_visitor.SymbolTableVisitor()
        
        # Set the global symbol table for the main program entry point
        # TODO: This assumes the program doesn't start with e.g. a DEF PROC
        print "epv.entry_points[0] = %s" % epv.entry_points[0]
        epv.entry_points[0].symbolTable = stv.globalSymbols
        
        for entry_point in epv.entry_points:
            print "entry_point = %s" % entry_point
            entry_point.accept(stv)
        if options.verbose:
            sys.stderr.write("done\n")
        
    if options.use_clr:
        if options.verbose:
            sys.stderr.write("Creating XML CFG... ")
        output_filename = filename + "_cfg.graphml"
        print "Creating %s" % output_filename
        xmlCfg(parse_tree, output_filename)
        if options.verbose:
            sys.stderr.write("done\n") 
    
    # TODO: Inline single-entry GOSUB
    #
    # Trace back from RETURN statements - if only one
    # GOSUB is reached - move the code in the GOSUB to the call site
    # of the GOSUB. 
    
    # Locate nodes with no inbound edges and trace unreachable code
    # from them. Remove unreachable code from the CFG and the AST. This
    # will need to be traced from program and procedure entry points
    
    
    # Convert GOSUB blocks to procedures if they are called more than once,
    # otherwise inline them.
    
    
    
    # TODO: Replace Goto -> ReturnFromProcedure with ReturnFromProcedure
    
    
    
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
    #extractData(parse_tree)
    # Type checking and casting
    #determineTypes(parse_tree)
    #typeCheck(parse_tree)
    
    # Optimisation
    #foldConstants(parse_tree)
    #elimiateCommonSubexpressions(parse_tree    opti
