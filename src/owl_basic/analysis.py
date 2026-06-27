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
    constant_propagation,
    correlation_visitor,
    data_visitor,
    errors,
    eval_lowering,
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
    bridgeFallthroughSubroutines,
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


def _assembler_block_numbers(numbered_lines):
    """Line numbers lying within an inline-assembler ``[ ... ]`` block.

    The per-line parse gate checks each line independently, so it cannot see a
    block whose ``[`` and ``]`` are on different lines -- it would flag every
    assembler body line as unparseable BASIC. The block is opaque to BASIC, so
    identify its span here and let the gate skip it; the whole-program parse
    then captures the block as a single ASSEMBLER token.

    This mirrors the lexer's ``t_ASSEMBLER`` scan: a string literal is skipped
    whole, so neither a ``[`` nor a ``]`` inside quotes counts -- a ``[`` in a
    string does not open a block, and a ``]`` inside ``EQUS "Contains]"`` does
    not close one (per the BBC ROM, ``]`` terminates only at a statement start,
    and a quoted string is read as a single operand).
    """
    inside = set()
    in_block = False
    for number, text in numbered_lines:
        was_in_block = in_block
        opened_here = False
        i = 0
        while i < len(text):
            char = text[i]
            if char == '"':                       # skip a string literal whole
                i += 1
                while i < len(text) and text[i] != '"':
                    i += 1
            elif char == '[' and not in_block:
                in_block, opened_here = True, True
            elif char == ']' and in_block:
                in_block = False
            i += 1
        if was_in_block or opened_here or in_block:
            inside.add(number)
    return inside


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

    # Identifying unparseable lines line-by-line cannot see a construct that
    # legitimately spans lines -- a block IF/ENDIF, CASE/ENDCASE or [ ] assembler
    # block -- so it would flag each such line as bad. Parse the whole program
    # first: if it parses, no line is unparseable. Only on failure fall back to
    # the per-line check to pinpoint the offending lines (for the strict error
    # message and lenient recovery). The whole parse joins the bodies with the
    # newline that separates statements, so independent lines stay independent
    # and a genuinely broken line still fails -- only multi-line constructs are
    # newly accepted.
    whole_source = "\n".join(text for _, text in numbered_lines) + "\n"
    if _line_parse_errors(whole_source, options):
        # Lines inside a multi-line [ ... ] assembler block can't be parsed on
        # their own; the whole-program parse captures the block as one ASSEMBLER
        # token, so exclude them from the per-line gate too.
        assembler_lines = _assembler_block_numbers(numbered_lines)
        unparseable = [
            number for number, text in numbered_lines
            if number not in assembler_lines
            and text.strip() and _line_parse_errors(text, options)
        ]
    else:
        unparseable = []
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

    * native machine code -- an inline assembler block ``[ ... ]``. OWL's dotnet
      backend cannot run 6502/ARM, but that is a backend decision: the block
      parses to an ``InlineAssembler`` node and is rejected at code generation
      (see docs/backend-specific-constructs.md). This frontend message only
      fires when the *whole-program* parse fails with such a block present (the
      per-line gate could not capture it). ``CALL``/``USR``/``SYS`` are likewise
      target-specific but now parse into neutral nodes and reach the backend.

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
    has_assembler = False
    for token in lexer:
        if token.type == "ASSEMBLER":
            has_assembler = True
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
    raise CompileError("could not parse the source: %s"
                       % _grammar.syntax_errors[0])


def _reject_unsupported_constructs(parse_tree):
    """Reject constructs OWL cannot compile, up front, with a clear message.

    EVAL interprets a string as a BASIC expression at run time. Supporting it in
    general means shipping a run-time expression evaluator in OwlRuntime and
    handing it the string (as the interpreter does) -- and its result type is
    statically unknown, so it would also need a dynamic value. That evaluator is a
    project of its own and OWL does not yet provide one, so EVAL is rejected here
    -- naming EVAL -- rather than surfacing later as an opaque type or
    code-generation error. (CALL is machine code and also unsupported, but unlike
    EVAL it is still analysable -- the call graph shows it as an external sink --
    so it is rejected at code generation, not here.)
    """
    def walk(node):
        if node is None:
            return
        if type(node).__name__ == "EvalFunc":
            raise CompileError(
                "EVAL is not supported: it evaluates a string as a BASIC "
                "expression at run time, which needs a run-time expression "
                "evaluator that OWL does not yet provide."
            )
        node.forEachChild(walk)

    walk(parse_tree)


def _check_array_dimensions(parse_tree):
    """Report arrays misused as either undimensioned or indexed with the wrong rank.

    Two related program errors that a real BBC raises at run time, and that the
    backend cannot lower to consistent IL:

    * An array element access whose array has no DIM -- and which is not a formal
      array parameter (DIMmed by the caller). The backend has no field of a known
      element type/rank to reference.
    * An access that indexes a DIMmed array with a different number of subscripts
      than its DIM (e.g. p%(c%) against ``DIM p%(9,7)``). The backend would emit
      an array reference of the wrong rank (int32[] against an int32[,] field),
      which ilasm rejects.

    Both are reported as diagnostics (collected like a type error, so codegen
    refuses) rather than emitting an invalid array reference. Each array is named
    once per problem.

    The check is conservative so order and scope never produce a false positive:
    a name is "declared" if it is DIMmed *anywhere* or appears as a formal array
    parameter, and the rank check is skipped for any name that is a formal
    parameter (rank is the caller's, unknown here) or is DIMmed at more than one
    rank (ambiguous).
    """
    declared = set()
    formal = set()                  # formal array parameters -- rank unknown
    ranks = {}                      # identifier -> declared rank, or None if ambiguous
    used = {}                       # identifier -> the lineNum of its first use
    accesses = []                   # (identifier, subscript count) for every access

    def _count(sequence):
        # dimensions/indices are sometimes a plain list, sometimes an
        # ExpressionList (.expressions) or other list node (.items).
        if sequence is None:
            return 0
        for attribute in ("expressions", "items"):
            elements = getattr(sequence, attribute, None)
            if elements is not None:
                return len(elements)
        return len(sequence)

    def walk(node):
        if node is None or not hasattr(node, "forEachChild"):
            return
        name = type(node).__name__
        if name == "AllocateArray":
            declared.add(node.identifier)
            rank = _count(node.dimensions)
            if node.identifier in ranks and ranks[node.identifier] != rank:
                ranks[node.identifier] = None
            else:
                ranks.setdefault(node.identifier, rank)
        elif name in ("FormalArgument", "FormalReferenceArgument"):
            argument = node.argument
            if type(argument).__name__ == "Array":
                declared.add(argument.identifier)
                formal.add(argument.identifier)
        elif name == "Indexer":
            used.setdefault(node.identifier, getattr(node, "lineNum", 0))
            accesses.append((node.identifier, _count(node.indices)))
        node.forEachChild(walk)

    walk(parse_tree)
    for identifier in used:
        if identifier not in declared:
            bare = identifier[:-1] if identifier.endswith("(") else identifier
            errors.error("the array %s() is used but never DIMmed" % bare)

    flagged_rank = set()
    for identifier, count in accesses:
        rank = ranks.get(identifier)
        if (rank is None or identifier in formal
                or identifier not in declared or identifier in flagged_rank):
            continue
        if count != rank:
            flagged_rank.add(identifier)
            bare = identifier[:-1] if identifier.endswith("(") else identifier
            errors.error(
                "the array %s() is DIMmed with %d subscript(s) but indexed with %d"
                % (bare, rank, count))


def _clear_cfg_edges(parse_tree):
    """Drop every control-flow edge from the statement graph, so the flow can be
    rebuilt cleanly after EVAL lowering appends dispatch-helper statements."""
    def walk(node):
        if node is None:
            return
        if hasattr(node, "clearOutEdges"):
            node.clearInEdges()
            node.clearOutEdges()
            node.clearComeFromGosubEdges()
            node.clearLoopBackEdges()
            node.clearLoopFromEdges()
        node.forEachChild(walk)

    walk(parse_tree)


def _build_flow(parse_tree, line_mapper, options):
    """Build the forward CFG, locate entry points, convert longjumps/subroutines,
    correlate loops, and return ``(entry_points, ordered_basic_blocks)``.

    Idempotent enough to run twice (it clears prior edges first; subroutine
    conversion finds no remaining GOSUBs on a re-run), so it can be re-run after a
    second EVAL pass appends dispatch helpers.
    """
    _clear_cfg_edges(parse_tree)
    createForwardControlFlowGraph(parse_tree, line_mapper, options)
    # An UNTIL FALSE / WHILE TRUE loop never exits, so the dead loop-exit edge its
    # closer draws must go before subroutine conversion classifies in-edges --
    # otherwise a GOSUB'd line that merely follows the loop looks fallen-into.
    correlation_visitor.prune_dead_loop_exits(parse_tree)
    entry_points = locateEntryPoints(parse_tree, line_mapper, options)
    convertLongjumpsToExceptions(parse_tree, line_mapper, options)
    # A fall-through into a GOSUB'd head (a jump-table handler with no RETURN, or
    # dead code before the head) is rewritten to an explicit PROC call so the head
    # converts as a GOSUB-only routine. The splice mutates the AST, so re-parent
    # before conversion inserts DEFPROCs by statement position.
    if bridgeFallthroughSubroutines(entry_points, line_mapper):
        parse_tree.accept(parent_visitor.ParentVisitor())
    convertSubroutinesToProcedures(parse_tree, entry_points, line_mapper, options)
    for entry_point in entry_points.values():
        correlation_visitor.CorrelationVisitor().start(entry_point)
    basic_blocks = identifyBasicBlocks(entry_points, options)
    return entry_points, orderBasicBlocks(basic_blocks, options)


def _build_line_map(parse_tree, physical_to_logical_map):
    lnv = line_number_visitor.LineNumberVisitor()
    parse_tree.accept(lnv)
    return LineMapper(physical_to_logical_map, lnv.line_to_stmt)


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
    parse_tree.accept(SourceDebuggingVisitor(data, line_offsets, line_number_prefixes))
    parse_tree.accept(parent_visitor.ParentVisitor())
    # Lower the EVALs compilable now (constant-string, dispatch). A second pass
    # runs after constant propagation, which can turn EVAL(f$) into EVAL of a
    # literal and a constant argument into a literal-argument dispatch; the shared
    # helper_serial keeps the two passes from colliding. The residue is rejected
    # only after that second pass (deferred from here). Re-parent afterwards so
    # the spliced expressions are seen by every downstream pass.
    helper_serial = eval_lowering.lower_eval(parse_tree, options)
    parse_tree.accept(parent_visitor.ParentVisitor())
    parse_tree.accept(separation_visitor.SeparationVisitor())
    parse_tree.accept(simplify_visitor.SimplificationVisitor())

    line_mapper = _build_line_map(parse_tree, physical_to_logical_map)

    dv = data_visitor.DataVisitor()
    parse_tree.accept(dv)

    # The flow build onward may reject a pathological program. In tolerant mode we
    # keep the partial program built so far for visualisation; otherwise failures
    # propagate as before.
    entry_points = {}
    ordered_basic_blocks = []
    global_symbols = None
    try:
        entry_points, ordered_basic_blocks = _build_flow(parse_tree, line_mapper, options)

        # Replace reads of provably-constant scalars with their literals, using the
        # per-method CFG for definite-assignment. A leaf swap inside statements, so
        # the blocks stay valid; typecheck/folding/DIM/FOR below see the constants.
        constant_propagation.propagate_constants(ordered_basic_blocks, parse_tree, options)

        # Second EVAL pass: propagation may have turned EVAL(f$) into EVAL of a
        # literal, or a constant argument into a literal-argument dispatch. A
        # constant-string splice only rewrites an expression (the blocks stay
        # valid), but a newly-enabled dispatch appends helper DEF FNs, so rebuild
        # the flow when the statement count grows.
        statement_count = len(parse_tree.statements)
        eval_lowering.lower_eval(parse_tree, options, helper_serial)
        parse_tree.accept(parent_visitor.ParentVisitor())
        if len(parse_tree.statements) != statement_count:
            parse_tree.accept(simplify_visitor.SimplificationVisitor())
            line_mapper = _build_line_map(parse_tree, physical_to_logical_map)
            dv = data_visitor.DataVisitor()
            parse_tree.accept(dv)
            entry_points, ordered_basic_blocks = _build_flow(parse_tree, line_mapper, options)

        _reject_unsupported_constructs(parse_tree)   # any EVAL we still cannot lower

        typecheck(parse_tree, entry_points, options)
        _check_array_dimensions(parse_tree)          # arrays used but never DIMmed

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
