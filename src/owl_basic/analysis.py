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
    line_number_visitor,
    parent_visitor,
    separation_visitor,
    simplify_visitor,
    symbol_table_visitor,
)
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
from owl_basic.line_mapper import LineMapper
from owl_basic.owltyping.typecheck import typecheck
from owl_basic.source_debugging import SourceDebuggingVisitor
from owl_basic.syntax import parser as syntax_parser

logger = logging.getLogger(__name__)


class _DefaultOptions:
    verbose = False
    use_clr = False
    debug_lex = False


def _synthesize_line_numbers(source):
    """Assign sequential logical line numbers to un-numbered plain-text source."""
    bodies = source.split("\n")
    data = "\n".join(bodies)
    physical_to_logical_map = [i + 1 for i in range(len(bodies))]
    cr_indices = all_indices(data, "\n")
    line_offsets = [0] + [i + 1 for i in cr_indices]
    line_number_prefixes = [0] * len(bodies)
    return data, physical_to_logical_map, line_offsets, line_number_prefixes


def analyse(source, name, source_filepath=None, options=None):
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
    data, physical_to_logical_map, line_offsets, line_number_prefixes = (
        _synthesize_line_numbers(source)
    )
    return _run_pipeline(
        data, physical_to_logical_map, line_offsets, line_number_prefixes,
        name, source_filepath, options,
    )


def analyse_numbered_lines(numbered_lines, name, source_filepath=None, options=None):
    """Analyse line-numbered BASIC source given as ``(line_number, text)`` pairs.

    Real programs carry explicit line numbers (e.g. detokenised Sphinx, whose
    detokeniser returns exactly these pairs) and GOTO/GOSUB reference them. The
    bodies (without their leading numbers) are parsed, and the *real* line
    numbers drive the physical->logical map so jump targets resolve.
    """
    options = options or _DefaultOptions()
    numbered_lines = list(numbered_lines)
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
        name, source_filepath, options,
    )


def _run_pipeline(data, physical_to_logical_map, line_offsets, line_number_prefixes,
                  name, source_filepath, options):
    """Run the front-end pipeline and bundle the result as a :class:`Program`."""
    parse_tree = syntax_parser.parse(data, options)
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

    for entry_point in entry_points.values():
        correlation_visitor.CorrelationVisitor().start(entry_point)

    basic_blocks = identifyBasicBlocks(entry_points, options)
    ordered_basic_blocks = orderBasicBlocks(basic_blocks, options)

    typecheck(parse_tree, entry_points, options)

    stv = symbol_table_visitor.SymbolTableVisitor()
    if "__owl__main" in entry_points:
        entry_points["__owl__main"].symbolTable = stv.globalSymbols
    for entry_point in entry_points.values():
        entry_point.accept(stv)

    return Program(
        name=name,
        source_filepath=source_filepath,
        entry_points=entry_points,
        ordered_basic_blocks=ordered_basic_blocks,
        global_symbols=stv.globalSymbols,
        data=dv,
        line_mapper=line_mapper,
    )
