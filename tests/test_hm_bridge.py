"""HM-based inference of DEF FN return types (red-green-refactor).

Builds up the BBC BASIC -> Hindley-Milner bridge one capability at a time:
literal returns first, then function-call returns and (mutual) recursion.
"""

from owl_basic.owltyping.hm_bridge import (
    infer_function_return_types,
    infer_return_types,
)
from owl_basic.owltyping.type_system import (
    FloatOwlType,
    IntegerOwlType,
    ObjectOwlType,
    StringOwlType,
)
from owl_basic.syntax import parser as _parser
from owl_basic.syntax.ast import DefineFunction, ReturnFromFunction


class _Options:
    debug_lex = False
    verbose = False
    use_clr = False


def _infer(source):
    tree = _parser.parse(source + "\n", _Options())
    functions = [
        s for s in tree.statements.statements if isinstance(s, DefineFunction)
    ]
    return infer_function_return_types(functions)


def _walk(node):
    yield node
    for child in node.children.values():
        for sub in (child if isinstance(child, list) else [child]):
            if sub is not None and hasattr(sub, "children"):
                yield from _walk(sub)


def _returns_by_function(source):
    """Attribute every ``= expr`` return to the DEF FN it belongs to.

    Multi-line functions spread their returns across sibling statements (and
    into IF clauses); this mirrors the linear span the flow analysis computes,
    which is enough for these focused tests.
    """
    tree = _parser.parse(source + "\n", _Options())
    by_function = {}
    current = None
    seen = set()
    for statement in tree.statements.statements:
        if isinstance(statement, DefineFunction):
            current = statement.name
            by_function.setdefault(current, [])
        if current is None:
            continue
        for node in _walk(statement):
            if isinstance(node, ReturnFromFunction) and id(node) not in seen:
                seen.add(id(node))
                by_function[current].append(node.returnValue)
    return by_function


def _infer_multiline(source):
    return infer_return_types(_returns_by_function(source))


def test_integer_literal_return():
    assert _infer("DEF FN_x = 42")["FN_x"] is IntegerOwlType()


def test_float_literal_return():
    assert _infer("DEF FN_y = 3.14")["FN_y"] is FloatOwlType()


def test_string_literal_return():
    assert _infer('DEF FN_z = "hi"')["FN_z"] is StringOwlType()


def test_call_return_takes_callee_type():
    # FN_a just returns FN_b, which returns an integer.
    inferred = _infer("DEF FN_a = FN_b\nDEF FN_b = 42")
    assert inferred["FN_a"] is IntegerOwlType()
    assert inferred["FN_b"] is IntegerOwlType()


def test_forward_reference_resolves_via_shared_variable():
    # FN_a is defined before the FN_b it calls, and FN_b before FN_c: the type
    # only resolves once every function's variable is linked and one is grounded.
    inferred = _infer(
        "DEF FN_a = FN_b\nDEF FN_b = FN_c\nDEF FN_c = 3.14"
    )
    assert inferred["FN_a"] is FloatOwlType()
    assert inferred["FN_b"] is FloatOwlType()
    assert inferred["FN_c"] is FloatOwlType()


# --- operator typing: promotion fires only on a genuine type mix -------------

def test_integer_times_integer_stays_integer():
    # The key principle: a pure-integer computation is NOT widened to float.
    assert _infer("DEF FN_m = 2 * 3")["FN_m"] is IntegerOwlType()


def test_integer_times_float_promotes_to_float():
    assert _infer("DEF FN_p = 2 * 3.0")["FN_p"] is FloatOwlType()


def test_float_minus_integer_promotes_to_float():
    assert _infer("DEF FN_q = 3.0 - 1")["FN_q"] is FloatOwlType()


def test_string_concatenation_stays_string():
    assert _infer('DEF FN_cat = "a" + "b"')["FN_cat"] is StringOwlType()


def test_numeric_plus_string_is_object():
    assert _infer('DEF FN_mix = 1 + "a"')["FN_mix"] is ObjectOwlType()


def test_type_follows_parameter_sigil_not_value():
    # n% is integer, so int*int stays integer; n (no sigil) is float, so float.
    assert _infer("DEF FN_di(n%) = n% * 2")["FN_di"] is IntegerOwlType()
    assert _infer("DEF FN_df(n) = n * 2")["FN_df"] is FloatOwlType()


# --- multi-line bodies, recursion and mutual recursion -----------------------

def test_recursive_float_factorial_returns_float():
    # n has no sigil, so it is a real: n*FN(...) is float arithmetic.
    inferred = _infer_multiline(
        "DEF FN_factorial(n)\n"
        "IF n=1 OR n=0 THEN =1\n"
        "=n*FN_factorial(n-1)"
    )
    assert inferred["FN_factorial"] is FloatOwlType()


def test_recursive_integer_factorial_returns_integer():
    # With n% the whole computation is integer and is never widened to float.
    inferred = _infer_multiline(
        "DEF FN_factorial(n%)\n"
        "IF n%=1 OR n%=0 THEN =1\n"
        "=n%*FN_factorial(n%-1)"
    )
    assert inferred["FN_factorial"] is IntegerOwlType()


def test_mutual_recursion_resolves_to_integer():
    inferred = _infer_multiline(
        "DEF FN_is_even(n)\n"
        "IF n = 0 THEN =TRUE ELSE =FN_is_odd(ABS(n)-1)\n"
        "DEF FN_is_odd(n)\n"
        "IF n = 0 THEN =FALSE ELSE =FN_is_even(ABS(n)-1)"
    )
    assert inferred["FN_is_even"] is IntegerOwlType()
    assert inferred["FN_is_odd"] is IntegerOwlType()


def test_two_numeric_return_paths_promote_to_float():
    inferred = _infer_multiline(
        "DEF FN_int_or_float(n)\n"
        "IF n = 0 THEN = 1 ELSE = 3.14159"
    )
    assert inferred["FN_int_or_float"] is FloatOwlType()
