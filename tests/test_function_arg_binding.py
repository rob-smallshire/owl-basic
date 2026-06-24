"""An unparenthesised function argument binds tightly (a factor), not a whole
expression.

BBC BASIC binds a function's bare argument to the next *factor*: `VAL M$ > 0` is
`(VAL M$) > 0`, and `"x"+CHR$10+"y"` is `"x"+(CHR$10)+"y"`. A few functions (VAL,
CHR$, COS, STR$) were declared to take a full `expr`; the old flat grammar made
them bind tightly anyway via the FUNCTION precedence, but the layered relational
grammar reduces `M$>0` to a comparison before the function reduces, so the
function would swallow the comparison -- giving `VAL(M$>0)` (String compared with
Integer, then VAL of an Integer). These are the constructs that broke Sphinx
(lines 288/312/323); pinned here as focused tests.
"""
from owl_basic.analysis import analyse


def _compiles(source):
    return not analyse(source, name="t").diagnostics


def test_val_binds_tighter_than_greater_than():
    # Sphinx line 288: IF VAL M$ > 0 ...  ->  (VAL M$) > 0, both Integer.
    assert _compiles('M$="5"\nIF VAL M$ > 0 PRINT 1\n')


def test_val_binds_tighter_than_equality():
    # Sphinx line 312: IF VAL M$ = 0 ...
    assert _compiles('M$="0"\nIF VAL M$ = 0 PRINT 1\n')


def test_chr_str_binds_tighter_than_plus():
    # Sphinx line 323: ..."mouse."+CHR$10+CHR$13+"..."  -> string concatenation,
    # not "mouse."+CHR$(10+CHR$13+...).
    assert _compiles('A$="x"+CHR$10+CHR$13+"y"\n')


def test_str_str_binds_tighter_than_plus():
    # STR$ converts a number to a string: "n="+STR$5+"!" is concatenation.
    assert _compiles('A$="n="+STR$5+"!"\n')


def test_cos_binds_tighter_than_arithmetic():
    # COS x*2 is (COS x)*2, a float; not COS(x*2) here, but either way numeric --
    # the point is it stays well-typed and binds like the other maths functions.
    assert _compiles('A=COS X*2+1\n')
