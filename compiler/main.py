#!ipy

import logging
logging._srcfile = None
logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Python Standard Library
import sys
import os   
import re
import atexit
import StringIO
from optparse import OptionParser

import ply.lex as lex
import ply.yacc as yacc

import errors
from decoder import decode
import bbc_lexer
import bbc_grammar
import bbc_ast
import xml_visitor
from source_debugging import SourceDebuggingVisitor
import parent_visitor
import separation_visitor
import simplify_visitor
import line_number_visitor
from flow import locateEntryPoints
from flow import createForwardControlFlowGraph
from flow import convertLongjumpsToExceptions
from flow import convertSubroutinesToProcedures
from flow import identifyBasicBlocks
from flow import orderBasicBlocks
from typing import typecheck
import data_visitor
import gml_visitor
from xml_blocks import dumpXmlBlocks
import ast_utils
from line_mapper import LineMapper
import symbol_table_visitor
from symbol_tables import SymbolTable
import correlation_visitor
from algorithms import all_indices

def tokenize(data, lexer):
    # Give the lexer some input
    lexer.input(data)

    # Tokenize
    while 1:
        tok = lexer.token()
        if not tok: break      # No more input
        print tok
    # Running the lexer twice on the same input screws up the line numbers, so stop here.
    sys.exit(0)  

def readFile(filename):
    logging.debug("readFile")
    # Read the file - processing it for line numbers if necessary
    f = open(filename, 'rb')
    data = f.read()
    f.close()
    return data

def detokenize(data, options):
    logging.debug("detokenize")
    if options.verbose:
        sys.stderr.write("Detokenizing...")
    
    detokenized = StringIO.StringIO()
    decode(data, detokenized)
    if options.verbose:
        sys.stderr.write("done\n")
    
    detokenHandle = StringIO.StringIO(detokenized.getvalue())
    return detokenHandle

def indexLineNumbers(detokenHandle, options):
    logging.debug("indexLineNumbers")
    if options.verbose:
        sys.stderr.write("Mapping physical to logical line numbers... ")
    
    line_number_regex = re.compile(r'(\s*\d+\s*)(.*)') # TODO: Factor this out of here and decoder
    physical_line = 0
    logical_line = 0
    physical_to_logical_map = []
    line_bodies = []
    line_number_prefixes = []
    #line_offsets = [] # Offsets to the start of the line
    while True:
        #line_offsets.append(detokenHandle.tell())
        line = detokenHandle.readline()
        if not line:
            break
        m = line_number_regex.match(line)
        if not m:
            raise CompileException("Missing line number at physical line %d (after logical line %d)" % (physical_line, logical_line))
        
        logical_line_string = m.group(1)
        logical_line = int(logical_line_string)
        line_number_prefix_length = len(logical_line_string)
        line_number_prefixes.append(line_number_prefix_length)
        physical_to_logical_map.append(logical_line)
        line_bodies.append(m.group(2))
        physical_line += 1
    
    data = '\n'.join(line_bodies)
    detokenHandle.close()
    cr_indices = all_indices(data, '\n')
    line_indices = [index + 1 for index in cr_indices]
    line_offsets = [0]
    line_offsets.extend(line_indices)
    for i, offset in enumerate(line_offsets):
        print "%d ==> %s" % (i, data[offset:offset + 5])
    print data
    return data, physical_to_logical_map, line_offsets , line_number_prefixes

def warnOnMissingNewline(data):
    logging.debug("warnOnMissingNewline")
    if not data.endswith('\n'):
        logging.warning("Missing newline at end of file")
        data += '\n'  
    return data

def buildLexer(options):
    logging.debug("buildLexer")
    if options.verbose:
        sys.stderr.write("Building lexer...")
    # Build the lexer and parser
    
    lexer = lex.lex(bbc_lexer)
    if options.verbose:
        sys.stderr.write("done\n")
    
    return lexer

def buildParser(options):
    logging.debug("buildParser")
    if options.verbose:
        sys.stderr.write("Building parser... ")
    
    parser = yacc.yacc(module=bbc_grammar, picklefile="parsetab.pickle", debug=1)
    if options.verbose:
        sys.stderr.write("done\n")
    
    return parser

def parse(data, lexer, parser, options):
    logging.debug("parse")
    if options.verbose:
        sys.stderr.write("Parsing...")
    
    parse_tree = parser.parse(data, lexer=lexer, tracking=True)
    if options.verbose:
        sys.stderr.write("done\n")
    
    return parse_tree

def setSourceDebugging(data, line_offsets, line_number_prefixes, parse_tree):
    logging.debug("Set source debugging")
    # Read through the data and set character column information
    sdv = SourceDebuggingVisitor(data, line_offsets, line_number_prefixes)
    parse_tree.accept(sdv)

def setParents(parse_tree, options):
    logging.debug("setParents")
    if options.verbose:
        sys.stderr.write("Setting parents... ")
    
    parse_tree.accept(parent_visitor.ParentVisitor())
    if options.verbose:
        sys.stderr.write("done\n")

def splitComplexNodes(parse_tree, options):
    logging.debug("splitComplexNodes")
    if options.verbose:
        sys.stderr.write("Separating complex Abstract Syntax Tree nodes... ")
    
    parse_tree.accept(separation_visitor.SeparationVisitor())
    if options.verbose:
        sys.stderr.write("done\n")

def simplifyAst(parse_tree, options):
    logging.debug("simplifyAst")
    if options.verbose:
        sys.stderr.write("Simplifying Abstract Syntax Tree... ")
    
    parse_tree.accept(simplify_visitor.SimplificationVisitor())
    if options.verbose:
        sys.stderr.write("done\n")

def createLineMapper(parse_tree, physical_to_logical_map):
    logging.debug("createLineMapper")
    lnv = line_number_visitor.LineNumberVisitor()
    parse_tree.accept(lnv)
    line_mapper = LineMapper(physical_to_logical_map, lnv.line_to_stmt)
    return line_mapper

def dumpXmlAst(parse_tree, output_filename, options):
    logging.debug("dumpXmlAst")
    if options.use_clr:
        if options.verbose:
            sys.stderr.write("Creating XML AST... ")
        
        xmlAst(parse_tree, output_filename)
        if options.verbose:
            sys.stderr.write("done\n")
           
def correlateLoops(entry_points, options):
    logging.debug("correlateLoops")
    if options.verbose:
        sys.stderr.write("Convert subroutines to procedures")
    
    for entry_point in entry_points.values():
        # Depth first search from this entry point through the CFG
        # maintaining a stack of loops as we go. Mark nodes that we
        visited = set()
        cv = correlation_visitor.CorrelationVisitor()
        cv.start(entry_point)
        
def buildSymbolTables(entry_points, options):
    logging.debug("buildSymbolTables")    
    # Attach symbol tables to each statement
    if options.verbose:
        sys.stderr.write("Building symbol tables")
    
    stv = symbol_table_visitor.SymbolTableVisitor()
    
    # Set the global symbol table for the main program entry point, if there is one
    if '__owl__main' in entry_points:
        entry_points['__owl__main'].symbolTable = stv.globalSymbols
    
    for entry_point in entry_points.values():
        entry_point.accept(stv)
    
    for table in SymbolTable.symbol_tables:
        title = "Symbol table '%s'" % table.name
        if table.parent is not None:
            parent_title = " with parent '%s'" % table.parent.name
        else:
            parent_title = "is the root symbol table"
        width = max(len(title), len(parent_title))
        print "-" * width
        print title
        print parent_title
        print "-" * width
        
        symbols = table.symbols.keys()
        symbols.sort()
        for symbol in symbols:
            print "%-10s %-10s %s" % (symbol, table.symbols[symbol].type.__doc__, table.symbols[symbol].modifier)
        print "-" * width
        print
    return stv
            
def extractData(parse_tree, options):
    """
    Extract all information from DATA statements
    """
    # All DATA is stored as strings, and is converted at run-time by the
    # READ statement
    logging.debug("extracting DATA")
    dv = data_visitor.DataVisitor()
    parse_tree.accept(dv)
    return dv   
    
def dumpXmlCfg(parse_tree, filename, options):
    logging.debug("dumpXmlCfg")   
    if options.use_clr:
        if options.verbose:
            sys.stderr.write("Creating XML CFG... ")
        xmlCfg(parse_tree, filename)
        if options.verbose:
            sys.stderr.write("done\n") 

def xmlAst(tree, filename):
    xmlv = xml_visitor.XmlVisitor(filename)
    tree.accept(xmlv)
    xmlv.close()
    
def xmlCfg(tree, filename):
    gmlv = gml_visitor.GmlVisitor(filename)
    tree.accept(gmlv)
    gmlv.close()

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

class CompileException(Exception):
    def __init__(self, msg):
        self.msg = msg

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        usage = "usage: %prog [options] source-file"
        version = "%prog 0.5"
        parser = OptionParser(usage=usage, version=version)
        parser.add_option("-x", "--debug-lex", action='store_true', dest='debug_lex', default=False)
        parser.add_option("-c", "--debug-no-clr", action='store_false', dest='use_clr', default=(sys.platform == 'cli'))
        parser.add_option("-v", "--verbose", action='store_true', dest='verbose', default=False)
        parser.add_option("-i", "--il", action='store_true', dest='create_il', default=False)

        (options, args) = parser.parse_args()
        if len(args) != 1:
            parser.error("No source file name supplied")
        compile(args[0], options)
    except Usage, err:
        parser.err(err.msg)
        return 2
    except CompileException, err:
        print >>sys.stderr, err.msg
        return 1
 
def compile(filename, options):   
    if options.use_clr:
        # .NET Framework
        import clr
        clr.AddReference('System.Xml')
        from System.Xml import XmlTextWriter, Formatting
    
    if not options.use_clr:
        # TODO: Use non-recursive code for the flowgraph
        sys.setrecursionlimit(2000)
    
    data = readFile(filename)
    detokenHandle = detokenize(data, options)
    data, physical_to_logical_map, line_offsets, line_number_prefixes = indexLineNumbers(detokenHandle, options)
    data = warnOnMissingNewline(data)
    lexer = buildLexer(options)
    
    if options.debug_lex:
        tokenize(data, lexer)
    
    parser = buildParser(options)
    parse_tree = parse(data, lexer, parser, options)
    setSourceDebugging(data, line_offsets, line_number_prefixes, parse_tree)
    setParents(parse_tree, options)
    splitComplexNodes(parse_tree, options)
    simplifyAst(parse_tree, options)
    line_mapper = createLineMapper(parse_tree, physical_to_logical_map)
    dv = extractData(parse_tree, options)
    createForwardControlFlowGraph(parse_tree, line_mapper, options)
    entry_points = locateEntryPoints(parse_tree, line_mapper, options)  
    convertLongjumpsToExceptions(parse_tree, line_mapper, options)
    convertSubroutinesToProcedures(parse_tree, entry_points, line_mapper, options)
    correlateLoops(entry_points, options)
    basic_blocks = identifyBasicBlocks(entry_points, options)
    ordered_basic_blocks = orderBasicBlocks(basic_blocks, options)
    typecheck(parse_tree, entry_points, options)
    stv = buildSymbolTables(entry_points, options)
    
    dumpXmlAst(parse_tree, filename + "_ast.xml", options)
    dumpXmlCfg(parse_tree, filename + "_cfg.graphml", options)
    dumpXmlBlocks(basic_blocks, filename + "_blocks.graphml", options)

    output_name = os.path.splitext(os.path.basename(filename))[0]
    source_path = os.path.abspath(filename)
    from urllib import pathname2url
    source_url = 'file:' + pathname2url(source_path)
    source_url = source_url.replace('C|', 'C:')
    if options.use_clr:
        from codegen.clr.generate import AssemblyGenerator
        ag = AssemblyGenerator(line_mapper)
        exe_filename = ag.generateAssembly(source_path, output_name, stv.globalSymbols, dv, ordered_basic_blocks)
        if options.create_il:
            # Create debuggable CIL files by disassebling and reassembling the
            # executable
            # Run ILDASM on the produced file
            # TODO: Should be able to determine this path using the information at http://bytes.com/topic/net/answers/106694-code-obtain-path-ildasm-exe
            logging.debug("Disassembling to CIL")
            ildasm_exe = r'C:\Program Files (x86)\Microsoft SDKs\Windows\v7.0A\bin\NETFX 4.0 Tools\x64\ildasm.exe'
            il_filename = exe_filename[:-3] + 'il'
            process(ildasm_exe, '/OUT=%s' % il_filename, exe_filename)
            
            logging.debug("Reassembling with CIL debug info")
            ilasm_exe = r'C:\Windows\Microsoft.NET\Framework\v2.0.50727\ilasm.exe'
            process(ilasm_exe, '/EXE', '/DEBUG', il_filename)
                                      
    # Structural analysis

    #splitBasicBlock(parse_tree)

    # Type checking and casting
    # Have we finished type-checking?
    # == Optimisation ==
    # Remove basic blocks containing only GOTO. Is this the same as replacing all GOTOs
    #  with edges in the CFG?
    # constant folding
    # constant propagation
    # Note - during constant propagation we can
    # eliminate some redundant casts by changing the
    # type of the constant at compile time
    # for example A = 5 can become A = 5.0 and
    # A% = 6.0 can become A% = 6
    # String Concatenation using the different forms
    # of String.Concat
    # eliminate locals
    # static single assignment form
    # TODO: Inline single-entry GOSUB
    # Optimise by combining conditions and branches better
    # rather than relying on Brtrue and Brfalse.  
    #
    # Trace back from RETURN statements - if only one
    # GOSUB is reached - move the code in the GOSUB to the call site
    # of the GOSUB
    # Locate nodes with no inbound edges and trace unreachable code
    # from them. Remove unreachable code from the CFG and the AST. This
    # will need to be traced from program and procedure entry points
        
    # TODO: Replace Goto -> ReturnFromProcedure with ReturnFromProcedure
    #elimiateCommonSubexpressions(parse_tree    opti

def process(name, *args):
    '''
    Execute an external process, and wait for it to complete
    '''
    from System.Diagnostics import Process
    p = Process()
    p.StartInfo.FileName = name
    p.StartInfo.Arguments = ' '.join(args)
    p.StartInfo.CreateNoWindow = True
    p.Start()
    p.WaitForExit()
    p.Close()
    
def printProfile():
    import clr
    for p in sorted(clr.GetProfilerData(), key=lambda p: p.ExclusiveTime):
        print '%s\t%d\t%d\t%d' % (p.Name, p.InclusiveTime, p.ExclusiveTime, p.Calls)


if __name__ == "__main__":
    import clr
    clr.EnableProfiler(False)
    atexit.register(printProfile)
    sys.exit(main())