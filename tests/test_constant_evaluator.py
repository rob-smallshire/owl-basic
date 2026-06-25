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


def test_integer_div_and_mod_fold():
    assert fold("7 DIV 2") == 3
    assert fold("-7 DIV 2") == -3            # truncate toward zero, not floor
    assert fold("7 MOD 3") == 1
    assert fold("-7 MOD 3") == -1            # remainder takes the dividend's sign
    assert fold("7 MOD -3") == 1
    assert fold("5 DIV 0") is None           # division by zero: leave to runtime
    assert fold("5 MOD 0") is None


def test_div_mod_of_float_operands_do_not_fold():
    # Integer operators over a float operand are left to runtime (we do not
    # second-guess BBC's float->int coercion here).
    assert fold("7.5 DIV 2") is None
    assert fold("7 MOD 2.0") is None


def test_bitwise_operators_fold():
    assert fold("5 AND 3") == 1
    assert fold("5 OR 2") == 7
    assert fold("5 EOR 1") == 4
    assert fold("NOT 0") == -1
    assert fold("NOT 5") == -6               # bitwise complement: ~5 == -6


def test_shift_operators_fold():
    assert fold("5 << 2") == 20
    assert fold("1 << 31") == -2147483648        # overflows int32 to the sign bit
    assert fold("1 << 40") == 256                # count masked to the width (40 & 31)
    assert fold("-8 >> 1") == -4                 # >> is arithmetic (signed)
    assert fold("-1 >> 1") == -1
    assert fold("-1 >>> 1") == 2147483647        # >>> is logical (zero-fill)
    assert fold("8 >>> 1") == 4
    assert fold("2.0 << 1") is None              # float operand: leave to runtime


def test_relational_operators_fold_to_minus_one_or_zero():
    assert fold("1=1") == -1
    assert fold("1=2") == 0
    assert fold("2<3") == -1 and fold("3<2") == 0
    assert fold("2<=2") == -1 and fold("3>=4") == 0
    assert fold("1<>2") == -1 and fold("2<>2") == 0
    assert fold("1.5<2") == -1               # float comparison


def test_true_false_and_unary_plus_fold():
    assert fold("TRUE") == -1
    assert fold("FALSE") == 0
    assert fold("3*TRUE") == -3
    assert fold("+7") == 7


def test_len_and_asc_fold():
    assert fold('LEN("hello")') == 5
    assert fold('LEN("")') == 0
    assert fold('ASC("A")') == 65
    assert fold('ASC("")') == -1            # ASC of the empty string is -1


def test_left_and_right_str_fold_with_clamping():
    assert fold('LEFT$("HELLO",2)') == "HE"
    assert fold('LEFT$("HELLO",0)') == ""
    assert fold('LEFT$("HELLO",10)') == "HELLO"    # clamped to the string
    assert fold('LEFT$("HELLO",-1)') == "HELLO"    # negative -> whole (uint clamp)
    assert fold('RIGHT$("HELLO",2)') == "LO"
    assert fold('RIGHT$("HELLO",10)') == "HELLO"
    assert fold('RIGHT$("HELLO",-1)') == "HELLO"


def test_mid_str_folds_one_based_with_clamping():
    assert fold('MID$("HELLO",2,3)') == "ELL"       # 1-based start
    assert fold('MID$("HELLO",1,5)') == "HELLO"
    assert fold('MID$("HELLO",0,2)') == "HE"         # 0 behaves as 1
    assert fold('MID$("HELLO",2,-1)') == "ELLO"      # negative length -> rest
    assert fold('MID$("HELLO",10,2)') == ""          # start past the end
    assert fold('MID$("HELLO",-1,2)') == ""          # negative start -> empty


def test_string_str_and_instr_fold():
    assert fold('STRING$(3,"ab")') == "ababab"
    assert fold('STRING$(0,"x")') == ""
    assert fold('STRING$(-1,"x")') == ""
    assert fold('INSTR("HELLO","L")') == 3           # 1-based
    assert fold('INSTR("HELLO","Z")') == 0           # not found
    assert fold('INSTR("HELLO","LO")') == 4
    assert fold('INSTR("HELLO","")') == 1            # empty -> the start index
    assert fold('INSTR("AB","ABC")') == 0            # substring longer than searched


def test_val_folds_like_the_runtime_parser():
    assert fold('VAL("42")') == 42.0
    assert fold('VAL("3.5")') == 3.5
    assert fold('VAL("1E3")') == 1000.0              # exponent, like VAL/STR$
    assert fold('VAL("12x")') == 12.0               # leading numeric part
    assert fold('VAL("abc")') == 0.0                # no number -> 0
    assert fold('VAL("1E999")') is None             # overflow: runtime "Too big"


def test_non_constant_subtrees_do_not_fold():
    assert fold("A%+1") is None              # references a variable
    assert fold("SIN(X)") is None
    assert fold("RND(6)") is None            # not a pure function of constants


def test_domain_errors_are_left_to_runtime():
    assert fold("SQR(-1)") is None           # negative root: do not fold
    assert fold("LN(-1)") is None
