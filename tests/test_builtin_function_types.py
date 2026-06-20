"""Built-in functions with a fixed return type must carry that type.

A node like POINT/MODE/OPENIN declares its result type via ``formal_type``, but
unless it also sets ``actual_type = formal_type`` its ``actualType`` defaults to
None. The type checker then crashes (`'NoneType' has no attribute 'isA'`) the
moment such a value is used in arithmetic -- e.g. POINT(x,y)+POINT(x,z). Each of
these functions returns a statically-known type, so its actualType must be set.
"""
from helpers import walk
from owl_basic.analysis import analyse
from owl_basic.owltyping.type_system import IntegerOwlType


def _types(source, node_name):
    program = analyse(source, name="t")
    return [type(n).__name__ for n in walk(program.parse_tree)
            if type(n).__name__ == node_name
            and getattr(n, "actualType", None) is not None]


def test_point_in_arithmetic_does_not_crash():
    # Was: AttributeError NoneType has no 'isA' in promoteNumericOperands.
    program = analyse("A=POINT(1,2)+POINT(3,4)\nEND\n", name="t")
    point = next(n for n in walk(program.parse_tree)
                 if type(n).__name__ == "PointFunc")
    assert point.actualType == IntegerOwlType()


def test_mode_function_is_an_integer():
    program = analyse("A=MODE\nEND\n", name="t")
    mode = next(n for n in walk(program.parse_tree)
                if type(n).__name__ == "ModeFunc")
    assert mode.actualType == IntegerOwlType()


def test_openin_result_used_in_arithmetic_does_not_crash():
    # OPENIN returns a channel (an integer-like handle); using it numerically
    # must not crash the type checker.
    analyse('C=OPENIN("f")+1\nEND\n', name="t")
