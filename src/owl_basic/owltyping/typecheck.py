"""Type checking and DEF FN return-type inference for the BBC BASIC front-end.

The :class:`~owl_basic.owltyping.typecheck_visitor.TypecheckVisitor` synthesises
expression types bottom-up, but a user function's return type is not known until
its body (and the bodies of any functions it calls) have been analysed, so
function calls are left ``Pending`` on the first pass. We then infer every
function's return type with :mod:`owl_basic.owltyping.hm_bridge` and re-run the
visitor, at which point calls resolve and operators over them type correctly.
"""

import logging

from owl_basic.exceptions import CompileError
from owl_basic.flow.traversal import depthFirstSearch
from owl_basic.syntax.ast import DefineFunction, ReturnFromFunction, UserFunc

from .hm_bridge import infer_return_types
from .typecheck_visitor import TypecheckVisitor

logger = logging.getLogger(__name__)


def typecheck(parse_tree, entry_points, options):
    """Type check *parse_tree*, resolving user-function return types.

    :param parse_tree: The parse tree to be type checked.
    :param entry_points: A dictionary of entry-point names to AstStatements.
    :param options: Command-line options.
    """
    logger.debug("Type checking...")
    # First pass: synthesise types; user-function calls are left Pending. It runs
    # silently -- a Pending call assigned to a typed variable, or a return value
    # checked against the not-yet-inferred return type, is not a real error -- so
    # only the second pass reports diagnostics.
    parse_tree.accept(TypecheckVisitor(entry_points, report_diagnostics=False))
    # Resolve each DEF FN's return type (handles recursion and promotion).
    inferUserFunctionReturnTypes(entry_points)
    # Second pass: with return types known, calls and operators over them type.
    parse_tree.accept(TypecheckVisitor(entry_points))


def inferUserFunctionReturnTypes(entry_points):
    """Infer and record the return type of every ``DEF FN`` entry point.

    Each function's return expressions are collected by walking the control-flow
    graph from its entry point, then resolved together so (mutually) recursive
    functions converge.
    """
    define_functions = [
        entry_point for entry_point in entry_points.values()
        if isinstance(entry_point, DefineFunction)
    ]
    returns_by_name = {
        function.name: [
            vertex.returnValue
            for vertex in depthFirstSearch(function)
            if isinstance(vertex, ReturnFromFunction)
        ]
        for function in define_functions
    }
    inferred = infer_return_types(returns_by_name)
    for function in define_functions:
        function.returnType = inferred.get(function.name)

    # Two unresolvable shapes are real, diagnosable program errors rather than
    # mere gaps in the inferencer, so name the function and reject gracefully:
    #   * a DEF FN with no '= <expr>' at all -- it never returns a value;
    #   * a function all of whose returns are calls to (mutually) recursive
    #     functions with no concrete base case, so no type can ever ground out.
    # A None that arises only because a return expression is not yet modelled by
    # the inferencer is left lenient (it falls through as Pending) so we do not
    # reject programs the back end can still handle.
    details = []
    for function in define_functions:
        if function.returnType is not None:
            continue
        returns = returns_by_name[function.name]
        if not returns:
            details.append("%s has no '= <expr>' to return a value" % function.name)
        elif all(isinstance(r, UserFunc) for r in returns):
            details.append(
                "%s's return type could not be inferred -- every return is a call "
                "to another function and the recursion has no base case that "
                "yields a concrete value" % function.name)
    if details:
        raise CompileError("Cannot infer function return type(s): "
                           + "; ".join(details))
