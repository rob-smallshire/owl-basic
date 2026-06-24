"""OWL rejects un-compilable loop structures with a clear CompileError, not a crash.

A NEXT/UNTIL/ENDWHILE with no statically-matching opener -- in particular a FOR
opened conditionally (inside an IF, so it exists on only some execution paths) and
closed unconditionally -- relies on BBC BASIC's *dynamic* loop stack, which OWL
correlates statically and cannot compile. It must say so via a CompileError rather
than calling sys.exit (which would crash the compiler host) or emitting wrong code.
"""
import pytest

from owl_basic.analysis import analyse
from owl_basic.exceptions import CompileError


def test_next_without_for_raises_compile_error():
    with pytest.raises(CompileError):
        analyse("NEXT\n", name="t")


def test_until_without_repeat_raises_compile_error():
    with pytest.raises(CompileError):
        analyse("UNTIL FALSE\n", name="t")


def test_conditionally_opened_for_raises_compile_error():
    # FOR J opened inside an IF on line 1; NEXT, unconditional on line 2.
    src = "FOR I=1 TO 2:IF I FOR J=1 TO 3:PRINT J\nNEXT,\n"
    with pytest.raises(CompileError):
        analyse(src, name="t")


def test_message_explains_the_dynamic_stack_reason():
    with pytest.raises(CompileError) as excinfo:
        analyse("FOR I=1 TO 2:IF I FOR J=1 TO 3:PRINT J\nNEXT,\n", name="t")
    message = str(excinfo.value).lower()
    assert "for" in message
    assert "dynamic" in message or "conditional" in message


def test_cross_type_continue_through_inner_closer_rejects():
    # A conditional NEXT closing the *outer* FOR from inside a REPEAT that has its
    # own UNTIL. Unlike `UNTIL FALSE` (whose dead exit is pruned), the NEXT has a
    # live fall-through that reaches the inner UNTIL -- where the REPEAT is leaked
    # on the continue path but live otherwise. That genuine nesting divergence at
    # the inner closer is not statically compilable; reject, do not crash.
    src = "FORK=0TO3\nREPEAT\nIFK=2 NEXT\nUNTILB>1\nNEXT\n"
    with pytest.raises(CompileError):
        analyse(src, name="t")


def test_cross_type_endwhile_continue_through_inner_closer_rejects():
    # The WHILE/ENDWHILE analogue: IF c ENDWHILE closing the outer WHILE from inside
    # an inner FOR whose NEXT then sees divergent nesting.
    src = "WHILE A<3\nA=A+1\nFORI=0TO9\nIFI=5 ENDWHILE\nNEXT\nENDWHILE\n"
    with pytest.raises(CompileError):
        analyse(src, name="t")


def test_plain_triple_nested_next_comma_comma_compiles():
    # Control: three unconditionally nested loops closed by NEXT,, correlate
    # statically and compile -- nothing here is dynamic.
    assert not analyse(
        "FORR=0TO2\nFORY=0TO2\nFORX=0TO2\nN=1\nNEXT,,\n", name="t").diagnostics
