"""Front-end analysis: plain-text BASIC source -> a backend-ready Program.

This runs the language front-end — parse, flow analysis, type checking and
symbol-table construction — and returns a :class:`~owl_basic.codegen.backend.Program`
for a code-generation :class:`~owl_basic.codegen.backend.Backend` to lower. It
is the analysis half of the compiler and is independent of any backend.

Modern OWL BASIC source is plain text with no line numbers; sequential logical
line numbers are synthesised here (the legacy tokenised-file path in
:mod:`owl_basic.main` derives them from the file instead).
"""

import logging

from owl_basic import (
    correlation_visitor,
    data_visitor,
    errors,
    line_number_visitor,
    parent_visitor,
    separation_visitor,
    simplify_visitor,
    symbol_table_visitor,
)
from owl_basic.abbreviations import expand_numbered_lines, expand_unnumbered
from owl_basic.algorithms import all_indices
from owl_basic.codegen.backend import Program
from owl_basic.flow import (
    convertLongjumpsToExceptions,
    convertSubroutinesToProcedures,
    createForwardControlFlowGraph,
    identifyBasicBlocks,
    locateEntryPoints,
    orderBasicBlocks,
)
from owl_basic.exceptions import CompileError, OwlBasicError
from owl_basic.line_mapper import LineMapper
from owl_basic.owltyping.typecheck import typecheck
from owl_basic.source_debugging import SourceDebuggingVisitor
from owl_basic.syntax import grammar as _grammar
from owl_basic.syntax import parser as syntax_parser

logger = logging.getLogger(__name__)


class _DefaultOptions:
    verbose = False
    use_clr = False
    debug_lex = False


def _line_parse_errors(text, options):
    """Parse a single line body; return the list of syntax errors (empty if OK)."""
    syntax_parser.parse(text if text.endswith("\n") else text + "\n", options)
    return list(_grammar.syntax_errors)


def _synthesize_line_numbers(source):
    """Assign AUTO line numbers to un-numbered plain-text source.

    BBC BASIC numbers un-numbered source as if typed under AUTO -- start 10,
    step 10 -- and GOTO/GOSUB target those numbers (the decoder.py path numbers
    the same way). Using 1-based numbers instead left a GOSUB110 with no line
    110 to resolve against.
    """
    bodies = source.split("\n")
    data = "\n".join(bodies)
    physical_to_logical_map = [(i + 1) * 10 for i in range(len(bodies))]
    cr_indices = all_indices(data, "\n")
    line_offsets = [0] + [i + 1 for i in cr_indices]
    line_number_prefixes = [0] * len(bodies)
    return data, physical_to_logical_map, line_offsets, line_number_prefixes


def analyse(source, name, source_filepath=None, options=None, tolerant=False):
    """Analyse plain-text BASIC *source* and return a :class:`Program`.

    Args:
        source: BASIC source text (no line numbers required).
        name: A short name for the program (used for the output assembly).
        source_filepath: Optional path to the source, for diagnostics.
        options: Optional options object exposing ``verbose``/``use_clr``/
            ``debug_lex``; sensible defaults are used if omitted.

    Returns:
        A :class:`Program` bundling the analysed program for a backend to lower.
    """
    options = options or _DefaultOptions()
    if not source.endswith("\n"):
        source += "\n"
    source = expand_unnumbered(source)  # MO.->MODE, P.->PRINT, ... (no-op if none)
    data, physical_to_logical_map, line_offsets, line_number_prefixes = (
        _synthesize_line_numbers(source)
    )
    return _run_pipeline(
        data, physical_to_logical_map, line_offsets, line_number_prefixes,
        name, source_filepath, options, tolerant=tolerant,
    )


def analyse_numbered_lines(numbered_lines, name, source_filepath=None, options=None,
                           strict=True, tolerant=False):
    """Analyse line-numbered BASIC source given as ``(line_number, text)`` pairs.

    Real programs carry explicit line numbers (e.g. detokenised Sphinx, whose
    detokeniser returns exactly these pairs) and GOTO/GOSUB reference them. The
    bodies (without their leading numbers) are parsed, and the *real* line
    numbers drive the physical->logical map so jump targets resolve.

    When ``strict`` (the default), any line that cannot be parsed raises a
    :class:`~owl_basic.exceptions.CompileError`. When not strict, such a line is
    recovered (replaced with a placeholder) so the rest of the program compiles
    — matching the interpreter, which stores odd lines and only errors on them
    at run time.
    """
    options = options or _DefaultOptions()
    numbered_lines = expand_numbered_lines(numbered_lines)  # expand abbreviations

    unparseable = [
        number for number, text in numbered_lines
        if text.strip() and _line_parse_errors(text, options)
    ]
    if unparseable and strict:
        raise CompileError(
            "could not parse %d line(s): %s"
            % (len(unparseable), ", ".join(str(n) for n in unparseable))
        )
    if unparseable:  # lenient: replace each unparseable line with a no-op placeholder
        bad = set(unparseable)
        logger.warning("lenient compile: %d unparseable line(s) recovered: %s",
                       len(bad), sorted(bad))
        numbered_lines = [
            (number, "REM (owl-basic: unparseable line recovered)" if number in bad else text)
            for number, text in numbered_lines
        ]

    source = "\n".join(text for _, text in numbered_lines) + "\n"
    data, synthesized, line_offsets, line_number_prefixes = _synthesize_line_numbers(source)
    physical_to_logical_map = [number for number, _ in numbered_lines]
    # _synthesize_line_numbers' split() yields a trailing empty body; pad the
    # real map to the same length so the per-line arrays stay aligned.
    while len(physical_to_logical_map) < len(synthesized):
        physical_to_logical_map.append(
            physical_to_logical_map[-1] + 1 if physical_to_logical_map else 1
        )
    return _run_pipeline(
        data, physical_to_logical_map, line_offsets, line_number_prefixes,
        name, source_filepath, options, tolerant=tolerant,
    )


def _diagnose_parse_failure(data, options):
    """Raise the most specific reason a source did not parse. Always raises.

    Only called once the parser has already failed, so a program that parses is
    never mistaken for any of these. A single token pass distinguishes, in
    priority order:

    * *binary / non-text input* -- a tokenised image, embedded graphics or
      machine-code data, or a garbage toot. The lexer cannot tokenise such bytes
      (it counts them), so rather than a misleading "Syntax error at <some token
      the skipped bytes happened to form>" -- or, worse, claiming an unsupported
      feature because the garbage contained a USR/[ token -- we say plainly that
      it is not a text BASIC listing. Checked first, so binary that happens to
      contain a USR or assembler token is reported as binary.

    * native machine code -- an inline assembler block ``[ ... ]`` or the ``USR``
      function (enter a 6502 routine at an address). OWL targets .NET and cannot
      run 6502, so these are named explicitly rather than surfacing as an opaque
      "Syntax error at 'USR'" (USR has no grammar production). ``USR`` is
      non-conditional in the ROM, so a ``USR`` token is always the keyword.

    * otherwise -- a genuine syntax error in an otherwise-text listing; name the
      first one the parser reported.

    A source that is itself a URL (commonly a bbcmic.ro share link pasted in place
    of a program) is named as such first of all: its encoded fragment would
    otherwise trip the binary counter and be mis-reported as "binary".
    """
    stripped = data.lstrip()
    lowered = stripped[:8].lower()
    if lowered.startswith("http://") or lowered.startswith("https://"):
        first_line = stripped.splitlines()[0]
        if "bbcmic.ro" in first_line:
            raise CompileError(
                "the source is a bbcmic.ro share link, not a BASIC program: the "
                "program is encoded in the URL after '#' and must be decoded "
                "before it can be compiled.")
        raise CompileError("the source is a URL, not a BASIC program.")
    lexer = syntax_parser.buildLexer(options)
    lexer.input(data)
    has_assembler = has_usr = False
    for token in lexer:
        if token.type == "ASSEMBLER":
            has_assembler = True
        elif token.type == "USR":
            has_usr = True
    if lexer.num_illegal_characters:
        raise CompileError(
            "the source contains %d character(s) that are not valid BASIC text "
            "(binary or control bytes outside a string), so it cannot be parsed "
            "as a text BASIC listing."
            % lexer.num_illegal_characters
        )
    if has_assembler:
        raise CompileError(
            "inline 6502 assembly ([ ... ]) is not supported: OWL targets "
            ".NET, which cannot run 6502 machine code."
        )
    if has_usr:
        raise CompileError(
            "USR is not supported: it enters a 6502 machine-code routine at "
            "an address, which OWL targets .NET and cannot run as machine "
            "code."
        )
    raise CompileError("could not parse the source: %s"
                       % _grammar.syntax_errors[0])


def _reject_unsupported_constructs(parse_tree):
    """Reject constructs OWL cannot compile, up front, with a clear message.

    EVAL interprets a string as a BASIC expression at run time, so its type and
    behaviour are unknowable to a static compiler; compiling even a restricted
    subset is a project of its own. Reject it here -- naming EVAL -- rather than
    let it surface later as an opaque type or code-generation error. (CALL is
    machine code and also cannot be compiled, but unlike EVAL it is still
    analysable -- the call graph shows it as an external sink -- so it is rejected
    at code generation, not here.)
    """
    def walk(node):
        if node is None:
            return
        if type(node).__name__ == "EvalFunc":
            raise CompileError(
                "EVAL is not supported: it evaluates a string as BASIC at run "
                "time, which a static compiler cannot reproduce."
            )
        node.forEachChild(walk)

    walk(parse_tree)


def _run_pipeline(data, physical_to_logical_map, line_offsets, line_number_prefixes,
                  name, source_filepath, options, tolerant=False):
    """Run the front-end pipeline and bundle the result as a :class:`Program`.

    When *tolerant*, a failure in the passes *after* the forward control-flow
    graph is built (loop correlation, basic blocks, type check, symbols) is
    caught and a *partial* Program is returned -- with the parse tree, entry
    points and forward CFG intact, but no basic blocks or symbols. This lets the
    ``cfg`` and ``ast`` visualisations render a program that does not fully
    analyse (e.g. one OWL rejects at loop correlation), which is exactly when
    seeing its graph is most useful. Only an :class:`OwlBasicError` is tolerated;
    an unexpected crash still propagates, so tolerant mode never hides a real
    bug. The default (non-tolerant) path is unchanged: any failure raises.
    """
    errors.reset()  # fresh per-compilation diagnostic dedup (no cross-pollution)
    parse_tree = syntax_parser.parse(data, options)
    if _grammar.syntax_errors:
        # The parser logs each syntax error and recovers a partial tree so it can
        # report more, but that tree must not be analysed as a real program
        # (garbage toots -- keyword soup, stray operators -- would mis-compile).
        # Diagnose *why* it did not parse, as specifically as we can. A program
        # that parses is never diagnosed here, so a valid listing that merely
        # contains a few stray bytes (Sphinx) or an unterminated string is not
        # mistaken for binary.
        _diagnose_parse_failure(data, options)
    _reject_unsupported_constructs(parse_tree)
    parse_tree.accept(SourceDebuggingVisitor(data, line_offsets, line_number_prefixes))
    parse_tree.accept(parent_visitor.ParentVisitor())
    parse_tree.accept(separation_visitor.SeparationVisitor())
    parse_tree.accept(simplify_visitor.SimplificationVisitor())

    lnv = line_number_visitor.LineNumberVisitor()
    parse_tree.accept(lnv)
    line_mapper = LineMapper(physical_to_logical_map, lnv.line_to_stmt)

    dv = data_visitor.DataVisitor()
    parse_tree.accept(dv)

    createForwardControlFlowGraph(parse_tree, line_mapper, options)
    entry_points = locateEntryPoints(parse_tree, line_mapper, options)
    convertLongjumpsToExceptions(parse_tree, line_mapper, options)
    convertSubroutinesToProcedures(parse_tree, entry_points, line_mapper, options)

    # Everything from loop correlation onward may reject a pathological program.
    # In tolerant mode we keep the partial program built so far (forward CFG) for
    # visualisation; otherwise the failure propagates as before.
    ordered_basic_blocks = []
    global_symbols = None
    try:
        for entry_point in entry_points.values():
            correlation_visitor.CorrelationVisitor().start(entry_point)

        basic_blocks = identifyBasicBlocks(entry_points, options)
        ordered_basic_blocks = orderBasicBlocks(basic_blocks, options)

        typecheck(parse_tree, entry_points, options)

        stv = symbol_table_visitor.SymbolTableVisitor()
        if "__owl__main" in entry_points:
            entry_points["__owl__main"].symbolTable = stv.globalSymbols
        for entry_point in entry_points.values():
            stv.start(entry_point)
        global_symbols = stv.globalSymbols
    except OwlBasicError:
        if not tolerant:
            raise
        logger.warning(
            "tolerant analysis of %s: a post-CFG pass failed, returning a "
            "partial program (forward CFG only -- no basic blocks or symbols)",
            name,
        )

    return Program(
        name=name,
        source_filepath=source_filepath,
        entry_points=entry_points,
        ordered_basic_blocks=ordered_basic_blocks,
        global_symbols=global_symbols,
        data=dv,
        line_mapper=line_mapper,
        parse_tree=parse_tree,
        # Carry any reported type errors so a backend can refuse to lower a
        # program that did not type-check (rather than emit nonsense IL).
        diagnostics=errors.reported_errors(),
    )
