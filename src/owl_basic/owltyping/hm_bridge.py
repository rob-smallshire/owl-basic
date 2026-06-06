"""Bridge from the BBC BASIC AST to type inference of ``DEF FN`` return types.

Most BBC BASIC types are fixed by sigils (``A%`` is integer, ``A$`` is string),
so they need no inference. The genuinely-inferred quantity is a ``DEF FN``'s
*return type*, which follows from the function body and — under (mutual)
recursion — from the return types of the functions it calls.

Two mechanisms cooperate:

* **Hindley-Milner unification (linking).** A pure pass-through return such as
  ``= FNfoo`` means this function has exactly *the same* return type as
  ``FNfoo``. That is type *equality*, which HM unification expresses precisely:
  we give every function a type variable and unify the variables of functions
  linked this way, forming equivalence classes that must share a type.

* **A monotone lattice fixpoint (promotion).** BBC BASIC implicitly coerces
  numbers (``byte < integer < float``) and boxes genuine mismatches to object
  (e.g. ``numeric + string``). That is a *subtyping/lattice* relation, which
  equality-based unification cannot express. We resolve each equivalence class
  by joining the types of all its return expressions over the promotion
  lattice, iterating to a fixpoint so recursion converges monotonically.

Crucially, a pure-integer computation is **never** widened: ``int * int`` is
``integer``. Promotion fires only on a real mix, and a function's numeric type
follows its operands' *declared* (sigil) types — ``FN(n%)`` is integer,
``FN(n)`` (a real variable) is float.
"""

from owl_basic.owltyping import inference as hm
from owl_basic.owltyping.type_system import (
    ByteOwlType,
    FloatOwlType,
    IntegerOwlType,
    NumericOwlType,
    ObjectOwlType,
    StringOwlType,
)
from owl_basic.sigil import identifierToType
from owl_basic.syntax.ast import (
    BinaryIntegerOperator,
    Cast,
    Divide,
    FalseFunc,
    LiteralFloat,
    LiteralInteger,
    LiteralString,
    Minus,
    Multiply,
    Plus,
    Power,
    ReturnFromFunction,
    TrueFunc,
    UserFunc,
    Variable,
)

# Promotion ranks for the numeric sub-lattice: byte < integer < float.
_NUMERIC_RANK = [(FloatOwlType, 3), (IntegerOwlType, 2), (ByteOwlType, 1)]
_RANK_TYPE = {3: FloatOwlType, 2: IntegerOwlType, 1: ByteOwlType}

# BOTTOM (unknown / not yet constrained) is represented as None.
_BOTTOM = None


def _numeric_rank(owl_type):
    """Return the promotion rank of a numeric type, or 0 if not numeric."""
    for cls, rank in _NUMERIC_RANK:
        if isinstance(owl_type, cls):
            return rank
    return 0


def _join(left, right):
    """Least upper bound over the promotion lattice (used to combine returns).

    BOTTOM is the identity. Equal types join to themselves (so string+string is
    string). Two numerics promote to the wider one. Anything else — notably a
    numeric mixed with a string — boxes to object.
    """
    if left is _BOTTOM:
        return right
    if right is _BOTTOM:
        return left
    if left is right:
        return left
    rank = max(_numeric_rank(left), 0), max(_numeric_rank(right), 0)
    if rank[0] and rank[1]:
        return _RANK_TYPE[max(rank)]()
    return ObjectOwlType()


def _numeric_join(left, right):
    """Join for arithmetic operators: numeric promotion, else object.

    Unlike :func:`_join` this does not treat ``string`` op ``string`` as string
    (``-``/``*`` on strings is not concatenation), so non-numeric operands box.
    """
    if left is _BOTTOM or right is _BOTTOM:
        return _BOTTOM
    if _numeric_rank(left) and _numeric_rank(right):
        return _RANK_TYPE[max(_numeric_rank(left), _numeric_rank(right))]()
    return ObjectOwlType()


def _return_expressions(define_function):
    """Yield the expressions a ``DEF FN`` returns (its ``= expr`` clauses)."""
    following = define_function.followingStatement
    if isinstance(following, ReturnFromFunction):
        return [following.returnValue]
    # TODO: multi-line FN bodies — walk the body for ReturnFromFunction nodes.
    return []


def infer_return_types(returns_by_name):
    """Infer each function's return type from its return expressions.

    *returns_by_name* maps a function name (e.g. ``"FN_factorial"``) to the list
    of expressions it returns. Returns a ``{name: OwlType}`` mapping; a function
    whose type cannot be determined (e.g. unconstrained mutual recursion with no
    base case) maps to ``None``.
    """
    returns = {name: list(exprs) for name, exprs in returns_by_name.items()}

    # --- HM linking: equivalence classes of functions that must share a type --
    variables = {name: hm.TypeVariable() for name in returns}
    for name, expressions in returns.items():
        for expression in expressions:
            if isinstance(expression, UserFunc) and expression.name in variables:
                hm.unify(variables[name], variables[expression.name])

    classes = {}
    for name in returns:
        representative = id(hm.prune(variables[name]))
        classes.setdefault(representative, []).append(name)

    # --- lattice fixpoint: promote each class's returns to its joined type -----
    estimates = {name: _BOTTOM for name in returns}

    def type_of(expr):
        if isinstance(expr, LiteralInteger):
            return IntegerOwlType()
        if isinstance(expr, LiteralFloat):
            return FloatOwlType()
        if isinstance(expr, LiteralString):
            return StringOwlType()
        if isinstance(expr, (TrueFunc, FalseFunc)):
            # TRUE (-1) and FALSE (0) are integers in BBC BASIC.
            return IntegerOwlType()
        if isinstance(expr, Cast):
            # The type checker inserts casts (e.g. integer->float) during the
            # first pass; a cast's value already has the target type.
            return expr.targetType
        if isinstance(expr, Variable):
            return identifierToType(expr.identifier)
        if isinstance(expr, UserFunc):
            # Recursion/forward references read the callee's current estimate;
            # unknown (builtin) callees stay BOTTOM for now.
            return estimates.get(expr.name, _BOTTOM)
        if isinstance(expr, Plus):
            # '+' is numeric add or string concatenation; _join handles both.
            return _join(type_of(expr.lhs), type_of(expr.rhs))
        if isinstance(expr, (Minus, Multiply)):
            return _numeric_join(type_of(expr.lhs), type_of(expr.rhs))
        if isinstance(expr, (Divide, Power)):
            # '/' and '^' are real arithmetic: float when operands are numeric.
            lhs, rhs = type_of(expr.lhs), type_of(expr.rhs)
            if lhs is _BOTTOM or rhs is _BOTTOM:
                return _BOTTOM
            if _numeric_rank(lhs) and _numeric_rank(rhs):
                return FloatOwlType()
            return ObjectOwlType()
        if isinstance(expr, BinaryIntegerOperator):
            lhs, rhs = type_of(expr.lhs), type_of(expr.rhs)
            if lhs is _BOTTOM or rhs is _BOTTOM:
                return _BOTTOM
            return IntegerOwlType()
        return _BOTTOM

    changed = True
    while changed:
        changed = False
        for members in classes.values():
            joined = _BOTTOM
            for name in members:
                for expression in returns[name]:
                    joined = _join(joined, type_of(expression))
            for name in members:
                if estimates[name] is not joined:
                    estimates[name] = joined
                    changed = True

    return estimates


def infer_function_return_types(define_functions):
    """Infer and record the return type of each ``DEF FN`` node.

    A convenience wrapper over :func:`infer_return_types` that collects each
    function's single-line ``= expr`` return and, as a side effect, sets every
    function's ``returnType`` so later passes can read it.
    """
    functions = {f.name: f for f in define_functions}
    returns = {name: _return_expressions(f) for name, f in functions.items()}
    estimates = infer_return_types(returns)
    for name, function in functions.items():
        function.returnType = estimates[name]
    return estimates
