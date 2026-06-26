"""Compile-time evaluation of constant expression subtrees.

``fold_constant(node)`` returns the constant Python value of an expression
subtree when it is a pure function of literal constants, or ``None`` when it is
not statically constant. It is a host-side evaluator (it interprets the AST in
Python; it never compiles and runs target code, so it stays correct when
cross-compiling -- see docs/eval-static-compilation.md).

Coverage (everything pure; impure functions -- RND, GET, TIME, file/screen I/O,
READ, user functions, ... -- are never folded):

* arithmetic ``+ - * /`` and ``^``, unary ``+``/``-``;
* integer ``DIV``/``MOD`` (truncating; remainder takes the dividend's sign),
  bitwise ``AND OR EOR NOT`` and the shifts ``<< >> >>>`` -- folded only when
  both operands are integers, so BBC's float->int coercion is never
  second-guessed. ``>>`` is arithmetic, ``>>>`` logical, and a shift count
  outside ``[0, width)`` shifts every bit out (``<<``/``>>>`` give 0, arithmetic
  ``>>`` sign-fills) -- BBC BASIC V's ARM behaviour, *not* CIL's modulo-width
  masking. There is no BBC BASIC V disassembly; these match the emulator and are
  kept equal to the runtime helpers, so folding stays sound;
* the relational operators (numeric operands -> BBC's ``-1``/``0``);
* ``PI``, ``TRUE``, ``FALSE``;
* numeric functions ``ABS INT SGN`` and the transcendentals
  ``SIN COS TAN ASN ACS ATN EXP LN LOG SQR RAD DEG``;
* string functions of constants ``CHR$ LEN ASC LEFT$ RIGHT$ MID$ STRING$ INSTR
  VAL`` -- each mirroring the OwlRuntime BasicCommands implementation op-for-op.

``STR$`` is *not* folded: it formats per the runtime ``@%`` variable (see the
EVAL doc's STR$ discussion). Each call is reached by ``_foldConstant`` in the
type checker, which replaces the folded subtree with a literal before codegen.

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


_INT32_MIN, _INT32_MAX = -(2 ** 31), 2 ** 31 - 1


def _signed(value, width):
    """Interpret the low *width* bits of *value* as a two's-complement integer."""
    value &= (1 << width) - 1
    if value & (1 << (width - 1)):
        value -= 1 << width
    return value


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


# Pure string functions of constant arguments. Each mirrors the OwlRuntime
# BasicCommands implementation op-for-op (1-based indexing, the unsigned-clamp
# edge cases, the empty-string conventions) so a folded constant equals the
# value the runtime would compute.

def _fold_len(node):
    s = fold_constant(node.factor)
    return len(s) if isinstance(s, str) else None


def _fold_asc(node):
    s = fold_constant(node.factor)
    if not isinstance(s, str):
        return None
    return -1 if len(s) == 0 else ord(s[0])


def _fold_left(node):
    s, length = fold_constant(node.source), fold_constant(node.length)
    if not isinstance(s, str) or not isinstance(length, int):
        return None
    # A negative length reaches s.Length via the (uint) cast: the whole string.
    keep = len(s) if length < 0 else min(length, len(s))
    return s[:keep]


def _fold_right(node):
    s, length = fold_constant(node.source), fold_constant(node.length)
    if not isinstance(s, str) or not isinstance(length, int):
        return None
    keep = len(s) if length < 0 else min(length, len(s))
    return s[len(s) - keep:]


def _fold_mid(node):
    s = fold_constant(node.source)
    start = fold_constant(node.position)
    length = fold_constant(node.length)
    if not isinstance(s, str) or not isinstance(start, int) or not isinstance(length, int):
        return None
    if start < 0:                     # (uint) cast -> a huge index -> past the end
        return ""
    zero_based = max(start, 1) - 1     # MID$ is 1-based; 0 behaves as 1
    if zero_based >= len(s):
        return ""
    available = len(s) - zero_based
    keep = available if length < 0 else min(length, available)
    return s[zero_based:zero_based + keep]


def _fold_string(node):              # STRING$(count, s$)
    count, s = fold_constant(node.count), fold_constant(node.source)
    if not isinstance(count, int) or not isinstance(s, str):
        return None
    return "" if count <= 0 or len(s) == 0 else s * count


def _fold_instr(node):
    searched = fold_constant(node.source)
    substring = fold_constant(node.subString)
    if not isinstance(searched, str) or not isinstance(substring, str):
        return None
    start = 1
    if node.startPosition is not None:
        start = fold_constant(node.startPosition)
        if not isinstance(start, int):
            return None
    if len(substring) == 0:           # InstrAt returns the start index unchanged
        return start
    if len(substring) > len(searched):
        return 0
    if not (1 <= start <= len(searched) + 1):
        return None                   # C# IndexOf would throw; leave it to runtime
    return searched.find(substring, start - 1) + 1   # 1-based; 0 if not found


def _fold_val(node):
    s = fold_constant(node.factor)
    if not isinstance(s, str):
        return None
    # Mirror BasicCommands.Val: skip spaces, an optional sign, digits, an optional
    # '.', and an optional E exponent (consumed only when well-formed).
    i, n = 0, len(s)
    while i < n and s[i] == " ":
        i += 1
    start = i
    if i < n and s[i] in "+-":
        i += 1
    saw_digit = False
    while i < n and "0" <= s[i] <= "9":
        i += 1
        saw_digit = True
    if i < n and s[i] == ".":
        i += 1
        while i < n and "0" <= s[i] <= "9":
            i += 1
            saw_digit = True
    if saw_digit and i < n and s[i] == "E":
        j = i + 1
        if j < n and s[j] in "+-":
            j += 1
        if j < n and "0" <= s[j] <= "9":
            i = j
            while i < n and "0" <= s[i] <= "9":
                i += 1
    try:
        result = float(s[start:i])
    except ValueError:
        return 0.0                    # no leading number is 0
    return None if math.isinf(result) else result   # overflow faults at runtime


_STRING_FUNCS = {
    "LenFunc": _fold_len,
    "AscFunc": _fold_asc,
    "LeftStrFunc": _fold_left,
    "RightStrFunc": _fold_right,
    "MidStrFunc": _fold_mid,
    "StringStrFunc": _fold_string,
    "InstrFunc": _fold_instr,
    "ValFunc": _fold_val,
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

    if name in ("ShiftLeft", "ShiftRight", "ShiftRightUnsigned"):
        a, b = fold_constant(node.lhs), fold_constant(node.rhs)
        if not (isinstance(a, int) and isinstance(b, int)):
            return None
        # BBC BASIC V (ARM): the shifted value's magnitude sets the width (32-bit
        # unless it needs 64); a count outside [0, width-1) shifts every bit out,
        # so << and >>> give 0 and arithmetic >> gives the sign fill. (Verified
        # against the emulator, not a disassembly; kept equal to the runtime
        # helpers so folding is sound.)
        width = 32 if _INT32_MIN <= a <= _INT32_MAX else 64
        if name == "ShiftRight":                 # signed / arithmetic
            return (a >> b) if 0 <= b < width else (-1 if a < 0 else 0)
        if not (0 <= b < width):
            return 0                             # << and >>> shift everything out
        if name == "ShiftLeft":
            return _signed(a << b, width)
        return _signed((a & ((1 << width) - 1)) >> b, width)   # logical

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

    if name == "UnaryMinus":              # numeric only (-A$ is a Type mismatch)
        a = fold_constant(node.factor)
        return -a if isinstance(a, (int, float)) else None
    if name == "UnaryPlus":               # identity on any scalar, strings too
        a = fold_constant(node.factor)
        return None if a is None else a
    if name == "AbsFunc":
        a = fold_constant(node.factor)
        return abs(a) if isinstance(a, (int, float)) else None
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

    if name in _STRING_FUNCS:
        return _STRING_FUNCS[name](node)

    if name in _UNARY_FN:
        a = fold_constant(node.factor)
        if a is None:
            return None
        try:
            return _UNARY_FN[name](float(a))
        except (ValueError, OverflowError, ZeroDivisionError):
            return None           # e.g. SQR/LN of a negative -- leave to run time

    return None
