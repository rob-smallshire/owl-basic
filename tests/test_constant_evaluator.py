"""The host-side constant-expression evaluator, fold_constant.

It returns the constant value of a pure-constant subtree (or None), recursing
through arithmetic and pure built-in functions -- so SIN(RAD(30)) folds whether
or not EVAL is involved. See docs/eval-static-compilation.md.
"""
import math

from owl_basic.syntax import parser
from owl_basic.analysis import _DefaultOptions
from owl_basic.constant_folding import fold_constant


def _rvalue(expression_source):
    """Parse `X=<expression>` and return the raw (un-folded) r-value AST node."""
    tree = parser.parse("X=" + expression_source + "\n", _DefaultOptions())
    found = []

    def visit(node):
        if node is None:
            return
        if type(node).__name__ == "ScalarAssignment":
            found.append(node.rValue)
        node.forEachChild(visit)

    visit(tree)
    assert found, "no assignment parsed from %r" % expression_source
    return found[0]


def fold(expression_source):
    return fold_constant(_rvalue(expression_source))


def test_integer_arithmetic_folds_exactly():
    assert fold("6*7") == 42
    assert fold("1+2") == 3
    assert fold("100-1") == 99
    assert isinstance(fold("6*7"), int)


def test_float_arithmetic_folds():
    assert fold("1/2") == 0.5
    assert fold("2^10") == 1024.0
    assert isinstance(fold("2^10"), float)   # BBC ^ is always real


def test_pure_functions_of_constants_fold():
    assert fold("ABS(-5)") == 5
    assert fold("INT(3.9)") == 3
    assert fold("INT(-2.5)") == -3           # BBC INT is floor
    assert fold("SGN(-7)") == -1
    assert fold("SQR(16)") == 4.0


def test_chr_str_of_constant_folds():
    # CHR$ of a constant code point folds to that character. CHR$34 is the quote
    # the EVAL dispatch's string-value hole is built from.
    assert fold("CHR$34") == '"'
    assert fold("CHR$(65)") == "A"
    assert fold("CHR$X") is None             # not a pure function of constants


def test_sin_rad_30_folds_recursively():
    # The motivating case: SIN(RAD(30)) reduces RAD(30) then SIN of that.
    assert fold("SIN(RAD(30))") == math.sin(30 * math.pi / 180.0)


def test_rad_mirrors_target_lowering_not_math_radians():
    # OWL lowers RAD as x*PI/180; fold_constant must do the same so a folded
    # constant matches the run-time (math.radians pre-divides, differing a ULP).
    assert fold("RAD(30)") == 30 * math.pi / 180.0


def test_pi_folds():
    assert fold("PI") == math.pi


def test_non_constant_subtrees_do_not_fold():
    assert fold("A%+1") is None              # references a variable
    assert fold("SIN(X)") is None
    assert fold("RND(6)") is None            # not a pure function of constants


def test_domain_errors_are_left_to_runtime():
    assert fold("SQR(-1)") is None           # negative root: do not fold
    assert fold("LN(-1)") is None
