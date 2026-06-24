"""Static lowering of EVAL whose argument is statically known.

Constant-string EVAL: when EVAL's argument folds to a constant string, that
string is a BASIC expression known at compile time. Re-parse it and splice the
resulting expression in place of the EVAL; downstream constant folding then
reduces it -- EVAL("1+2") -> 3, EVAL("SIN(RAD(30))") -> 0.5. Nested EVAL falls
out by re-lowering: parsing EVAL("EVAL(""1+2"")") yields another EvalFunc, which
the next pass over the tree lowers in turn.

An EVAL whose argument is not statically a constant string is left in place for
later increments (value-hole templates, function-by-name dispatch) or, failing
those, the honest "needs a run-time evaluator" rejection.

See docs/eval-static-compilation.md.
"""
from owl_basic.constant_folding import fold_constant
from owl_basic.exceptions import CompileError
from owl_basic.parent_visitor import ParentVisitor
from owl_basic.syntax import parser as syntax_parser
from owl_basic.syntax import grammar as _grammar
from owl_basic.syntax.ast import ValFunc


def lower_eval(parse_tree, options):
    """Splice every constant-string EVAL in *parse_tree* with its parsed expression.

    Iterates to a fixpoint so a nested EVAL exposed by lowering an outer one is
    lowered too. Parent references on the spliced subtrees are re-established as we
    go, so a freshly exposed inner EVAL can itself be spliced.
    """
    while _lower_once(parse_tree, options):
        pass


def _lower_once(parse_tree, options):
    progressed = False
    for eval_node in _collect_evals(parse_tree):
        source = _constant_string(eval_node.factor)
        if source is not None:
            # Constant-string EVAL: re-parse the string and splice it.
            expression = _parse_expression(source, eval_node.lineNum, options)
            _splice(eval_node, expression)
            progressed = True
        elif _is_provably_decimal_string(eval_node.factor):
            # Digit idiom: EVAL of a string provably containing only decimal
            # digits (a slice of a digit-only literal) is EVAL == VAL. Rewrite to
            # VAL of the same argument -- no run-time evaluator needed.
            _splice(eval_node, ValFunc(factor=eval_node.factor))
            progressed = True
    return progressed


def _collect_evals(parse_tree):
    found = []

    def visit(node):
        if node is None:
            return
        if type(node).__name__ == "EvalFunc":
            found.append(node)
        node.forEachChild(visit)

    visit(parse_tree)
    return found


def _constant_string(node):
    value = fold_constant(node)
    return value if isinstance(value, str) else None


def _is_provably_decimal_string(node):
    """Whether *node* always yields a string of decimal digits at run time.

    A slice (MID$/LEFT$/RIGHT$) of a digit-only string literal is such a string,
    whatever the runtime index: every character is a digit, so EVAL of it parses
    the same plain numeral that VAL does. (A constant digit string is handled by
    the constant-string path instead.)
    """
    name = type(node).__name__
    if name in ("MidStrFunc", "LeftStrFunc", "RightStrFunc"):
        return _is_digit_literal(node.source)
    return False


def _is_digit_literal(node):
    return (type(node).__name__ == "LiteralString"
            and len(node.value) > 0 and node.value.isdigit())


def _parse_expression(source, line_num, options):
    """Parse *source* as a BASIC expression node, or raise naming the bad EVAL."""
    del _grammar.syntax_errors[:]
    tree = syntax_parser.parse("X=" + source + "\n", options)
    if _grammar.syntax_errors or tree is None:
        raise CompileError(
            "EVAL at line %d evaluates the string %r, which is not a valid BASIC "
            "expression." % (line_num, source))
    found = []

    def visit(node):
        if node is None:
            return
        if type(node).__name__ == "ScalarAssignment":
            found.append(node.rValue)
        node.forEachChild(visit)

    visit(tree)
    if not found:
        raise CompileError(
            "EVAL at line %d evaluates the string %r, which is not a BASIC "
            "expression." % (line_num, source))
    return found[0]


def _splice(eval_node, expression):
    """Replace *eval_node* with *expression* in the tree, fixing up references."""
    expression.parent = eval_node.parent
    expression.parent_property = eval_node.parent_property
    expression.parent_index = eval_node.parent_index
    eval_node.parent.setProperty(
        expression, eval_node.parent_property, eval_node.parent_index)
    _set_line_num(expression, eval_node.lineNum)
    # Parent the spliced subtree's own descendants so a nested EVAL inside it can
    # be spliced on the next pass; expression.parent itself is set above.
    expression.accept(ParentVisitor())


def _set_line_num(node, line_num):
    node.lineNum = line_num
    node.forEachChild(lambda child: _set_line_num(child, line_num) if child else None)
