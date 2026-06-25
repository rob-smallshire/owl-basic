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

# Bitwise operators (CIL and/or/xor on the integer operands). Exact.
_BITWISE = {
    "And": lambda a, b: a & b,
    "Or": lambda a, b: a | b,
    "Eor": lambda a, b: a ^ b,
}

# Relational operators yield BBC's -1 (true) / 0 (false), matching the emitter's
# ceq/clt/cgt-then-neg sequences.
_RELATIONAL = {
    "Equal": lambda a, b: a == b,
    "NotEqual": lambda a, b: a != b,
    "LessThan": lambda a, b: a < b,
    "LessThanEqual": lambda a, b: a <= b,
    "GreaterThan": lambda a, b: a > b,
    "GreaterThanEqual": lambda a, b: a >= b,
}


def _trunc_div(a, b):
    """BBC/CIL integer division: truncate toward zero (not Python's floor)."""
    if b == 0:
        return None
    quotient = abs(a) // abs(b)
    return -quotient if (a < 0) != (b < 0) else quotient


def _trunc_mod(a, b):
    """BBC/CIL remainder: magnitude of abs(a) mod abs(b), sign of the dividend."""
    if b == 0:
        return None
    remainder = abs(a) % abs(b)
    return -remainder if a < 0 else remainder

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
    if name == "TrueFunc":            # BBC TRUE is -1, FALSE is 0
        return -1
    if name == "FalseFunc":
        return 0

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

    if name in ("IntegerDivide", "IntegerModulus", "And", "Or", "Eor"):
        a, b = fold_constant(node.lhs), fold_constant(node.rhs)
        # Integer operators; fold only when both operands are already integers, so
        # we never have to second-guess BBC's float->int coercion. A float operand
        # is left to run time.
        if not (isinstance(a, int) and isinstance(b, int)):
            return None
        if name == "IntegerDivide":
            return _trunc_div(a, b)
        if name == "IntegerModulus":
            return _trunc_mod(a, b)
        return _BITWISE[name](a, b)

    if name in _RELATIONAL:
        a, b = fold_constant(node.lhs), fold_constant(node.rhs)
        if a is None or b is None or isinstance(a, str) or isinstance(b, str):
            return None           # string comparison fidelity: leave to run time
        if isinstance(a, float) or isinstance(b, float):
            a, b = float(a), float(b)   # mirror the runtime's promotion to float64
        return -1 if _RELATIONAL[name](a, b) else 0

    if name == "Not":             # BBC NOT is bitwise complement: ~a == -a-1
        a = fold_constant(node.factor)
        return None if not isinstance(a, int) else ~a

    if name == "UnaryMinus":
        a = fold_constant(node.factor)
        return None if a is None else -a
    if name == "UnaryPlus":
        a = fold_constant(node.factor)
        return None if a is None else a
    if name == "AbsFunc":
        a = fold_constant(node.factor)
        return None if a is None else abs(a)
    if name == "IntFunc":         # BBC INT is floor (toward -infinity)
        a = fold_constant(node.factor)
        return None if a is None else math.floor(a)
    if name == "SgnFunc":
        a = fold_constant(node.factor)
        return None if a is None else (a > 0) - (a < 0)
    if name == "ChrStrFunc":      # CHR$(n) -- the character whose code is n
        a = fold_constant(node.factor)
        if a is None:
            return None
        try:
            return chr(int(a) & 0xFF)
        except (ValueError, OverflowError):
            return None

    if name in _UNARY_FN:
        a = fold_constant(node.factor)
        if a is None:
            return None
        try:
            return _UNARY_FN[name](float(a))
        except (ValueError, OverflowError, ZeroDivisionError):
            return None           # e.g. SQR/LN of a negative -- leave to run time

    return None
