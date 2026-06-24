"""Compile-time evaluation of constant expression subtrees.

``fold_constant(node)`` returns the constant Python value of an expression
subtree when it is a pure function of literal constants, or ``None`` when it is
not statically constant. It is a host-side evaluator (it interprets the AST in
Python; it never compiles and runs target code, so it stays correct when
cross-compiling -- see docs/eval-static-compilation.md).

Fidelity to the run-time splits in two:

* IEEE-exact cases -- integer arithmetic, float ``+ - * /`` and ``SQR`` -- agree
  bit-for-bit with the .NET run-time, *provided we mirror the target's operation
  order and types*. So ``RAD``/``DEG`` reproduce OWL's lowering ``x*PI/180``
  rather than calling ``math.radians`` (which pre-divides and differs by a ULP).
* Library transcendentals (``SIN COS TAN ASN ACS ATN EXP LN LOG`` and ``^``) use
  the host math library and may differ from .NET ``System.Math`` by ~1 ULP.
"""
import math

# Integer + - *, and the same in float64 when an operand is a float. Exact.
_BINARY = {
    "Plus": lambda a, b: a + b,
    "Minus": lambda a, b: a - b,
    "Multiply": lambda a, b: a * b,
}

# Library transcendentals: host math, ~1 ULP versus the .NET run-time. RAD/DEG
# mirror OWL's exact lowering instead of math.radians/degrees.
_UNARY_FN = {
    "SinFunc": math.sin, "CosFunc": math.cos, "TanFunc": math.tan,
    "AsnFunc": math.asin, "AcsFunc": math.acos, "AtnFunc": math.atan,
    "ExpFunc": math.exp, "LnFunc": math.log, "LogFunc": math.log10,
    "SqrFunc": math.sqrt,
    "RadFunc": lambda x: x * math.pi / 180.0,
    "DegFunc": lambda x: x * 180.0 / math.pi,
}


def fold_constant(node):
    """Return the constant value of *node*, or None if not statically constant."""
    if node is None:
        return None
    name = type(node).__name__

    if name in ("LiteralInteger", "LiteralFloat", "LiteralString"):
        return node.value
    if name == "PiFunc":
        return math.pi

    if name == "Concatenate":     # string concat after type-check converts Plus
        a, b = fold_constant(node.lhs), fold_constant(node.rhs)
        if isinstance(a, str) and isinstance(b, str):
            return a + b
        return None

    if name in _BINARY:
        a, b = fold_constant(node.lhs), fold_constant(node.rhs)
        if a is None or b is None:
            return None
        if isinstance(a, str) or isinstance(b, str):
            # Plus of two constant strings is concatenation (before type-check
            # turns it into a Concatenate). No other string arithmetic exists.
            if name == "Plus" and isinstance(a, str) and isinstance(b, str):
                return a + b
            return None
        return _BINARY[name](a, b)

    if name == "Divide":          # BBC '/' is always real division
        a, b = fold_constant(node.lhs), fold_constant(node.rhs)
        if a is None or b is None or float(b) == 0.0:
            return None
        return float(a) / float(b)

    if name == "Power":           # BBC '^' always yields a real
        a, b = fold_constant(node.lhs), fold_constant(node.rhs)
        if a is None or b is None:
            return None
        try:
            result = float(a) ** float(b)
        except (ValueError, OverflowError, ZeroDivisionError):
            return None
        return None if isinstance(result, complex) else result

    if name == "UnaryMinus":
        a = fold_constant(node.factor)
        return None if a is None else -a
    if name == "AbsFunc":
        a = fold_constant(node.factor)
        return None if a is None else abs(a)
    if name == "IntFunc":         # BBC INT is floor (toward -infinity)
        a = fold_constant(node.factor)
        return None if a is None else math.floor(a)
    if name == "SgnFunc":
        a = fold_constant(node.factor)
        return None if a is None else (a > 0) - (a < 0)

    if name in _UNARY_FN:
        a = fold_constant(node.factor)
        if a is None:
            return None
        try:
            return _UNARY_FN[name](float(a))
        except (ValueError, OverflowError, ZeroDivisionError):
            return None           # e.g. SQR/LN of a negative -- leave to run time

    return None
