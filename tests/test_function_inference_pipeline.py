"""The DEF FN return-type bridge wired into the full analyse() pipeline.

These go through the real front-end (parse -> flow -> typecheck), so they also
exercise return collection over the control-flow graph, unlike the focused unit
tests in ``test_hm_bridge.py``.
"""

from helpers import function_return_types
from owl_basic.analysis import analyse
from owl_basic.owltyping.type_system import FloatOwlType, IntegerOwlType


def _function_return_types(source):
    return function_return_types(analyse(source, "t"))


def test_pipeline_infers_recursive_float_factorial():
    source = (
        "PRINT FN_factorial(5)\n"
        "END\n"
        "DEF FN_factorial(n)\n"
        "IF n=1 OR n=0 THEN =1\n"
        "=n*FN_factorial(n-1)\n"
    )
    assert _function_return_types(source)["FN_factorial"] is FloatOwlType()


def test_pipeline_infers_recursive_integer_factorial():
    source = (
        "PRINT FN_factorial(5)\n"
        "END\n"
        "DEF FN_factorial(n%)\n"
        "IF n%=1 OR n%=0 THEN =1\n"
        "=n%*FN_factorial(n%-1)\n"
    )
    assert _function_return_types(source)["FN_factorial"] is IntegerOwlType()
