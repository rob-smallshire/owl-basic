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


def test_plain_triple_nested_next_comma_comma_compiles():
    # Control case: three unconditionally nested loops closed by NEXT,, correlate
    # statically. This must compile -- it proves the rejection below is specific to
    # the conditional NEXT, not a blanket rejection of NEXT,, or deep nesting.
    assert not analyse(
        "FORR=0TO2\nFORY=0TO2\nFORX=0TO2\nN=1\nNEXT,,\n", name="t").diagnostics


def test_conditional_next_continue_before_inner_loop_is_rejected():
    # The corpus shape (678936c066cc): a conditional `IF c NEXT` continue inside
    # the middle (Y) loop, before the inner (X) loop, all closed by NEXT,,. When
    # the conditional NEXT fires on Y's final iteration it pops Y early, so the
    # join at FOR X is reached inside [R,Y] on one path and [R] on the other; the
    # later NEXT,, then has one too few loops -- its closers pair with FOR Y on one
    # path and FOR R on the other. Only BBC's runtime stack can resolve that.
    src = "FORR=0TO2\nFORY=0TO2\nIFY=1 NEXT\nFORX=0TO2\nN=1\nNEXT,,\n"
    with pytest.raises(CompileError) as excinfo:
        analyse(src, name="t")
    assert "dynamic" in str(excinfo.value).lower()


def test_conditional_next_continue_without_inner_loop_is_rejected():
    # The same early-pop without an inner loop: NEXT, then has nothing to close on
    # the path where the conditional NEXT already popped Y.
    src = "FORR=0TO2\nFORY=0TO2\nIFY=1 NEXT\nN=1\nNEXT,\n"
    with pytest.raises(CompileError):
        analyse(src, name="t")
