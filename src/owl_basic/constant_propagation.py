"""General constant propagation over the per-method control-flow graph.

Replace every read of a provably-constant scalar with its literal value, so that
the passes downstream -- constant folding, EVAL lowering, DIM sizes, FOR limits --
see the constant rather than a variable. EVAL is not special-cased: EVAL(f$)
benefits simply because f$ becomes a string literal.

Soundness (no naive shortcuts -- a naive "assigned once" rule miscompiles a read
that runs before its assignment; see docs/constant-propagation.md):

  * A scalar is a *uniform constant* C iff every write of it anywhere in the
    program is a ScalarAssignment whose RHS folds to the same constant C. Any
    other write (INPUT/READ/FOR/+=, or a second/different constant) disqualifies
    it. Because every assignment yields C, the variable is always either C or its
    default before any assignment -- even across PROC calls, which can only
    re-assign C.

  * The only remaining question is use-before-assignment, settled by a per-method
    *definite-assignment* (forward must) dataflow over ordered_basic_blocks: a use
    is replaced only where the variable is assigned on every path from the method
    entry. The entry block's IN is forced empty, so a loop back-edge (e.g. RUN)
    cannot make a use-before-def look defined.

%% (int64) and & (byte) scalars are left alone: their width/narrowing semantics
make substituting a bare literal subtle (a small value in a %% operand shifts at
width 64), and they are rare. Uses in a method where the variable is only
assigned in another method are conservatively not propagated (sound, intra-method
incomplete).
"""

from owl_basic.syntax.ast import (
    AstStatement,
    LiteralFloat,
    LiteralInteger,
    LiteralString,
    Variable,
)
from owl_basic.constant_folding import fold_constant
from owl_basic.owltyping.type_system import (
    FloatOwlType,
    IntegerOwlType,
    LongIntegerOwlType,
    StringOwlType,
)

_INT32_MIN, _INT32_MAX = -(2 ** 31), 2 ** 31 - 1
_DISQUALIFIED = object()


def _walk(node, fn):
    if node is None:
        return
    fn(node)
    if hasattr(node, "forEachChild"):
        node.forEachChild(lambda child: _walk(child, fn))


def _walk_own(statement, fn):
    """Walk *statement* and its expression descendants, but stop at any nested
    statement -- IF/CASE clause bodies are separate CFG vertices (their own
    blocks), so their reads and writes belong to those blocks, not this one."""
    fn(statement)

    def descend(node):
        if node is None or isinstance(node, AstStatement):
            return
        fn(node)
        if hasattr(node, "forEachChild"):
            node.forEachChild(descend)

    if hasattr(statement, "forEachChild"):
        statement.forEachChild(descend)


def _is_propagatable_scalar(identifier):
    # @% is the runtime-owned print-format control word (a pseudo-variable parsed
    # as Variable("@%")), not an ordinary scalar -- leave it to the runtime.
    # %% (int64) and & (byte) have width/narrowing subtleties; everything else
    # (%, $, or a plain real) substitutes a literal cleanly.
    if identifier.startswith("@"):
        return False
    return not (identifier.endswith("%%") or identifier.endswith("&"))


def _uniform_constants(parse_tree):
    """Map each uniform-constant scalar name to its single constant value."""
    state = {}      # name -> set of constant values, or _DISQUALIFIED

    def record(node):
        if not (isinstance(node, Variable) and getattr(node, "isLValue", False)):
            return
        name = node.identifier
        if not _is_propagatable_scalar(name) or state.get(name) is _DISQUALIFIED:
            state.setdefault(name, _DISQUALIFIED)
            return
        assignment = node.parent
        if (type(assignment).__name__ == "ScalarAssignment"
                and getattr(assignment, "lValue", None) is node):
            value = fold_constant(assignment.rValue)
            if value is None or isinstance(value, bool):
                state[name] = _DISQUALIFIED          # non-constant assignment
            else:
                state.setdefault(name, set()).add(value)
        else:
            state[name] = _DISQUALIFIED              # INPUT/READ/FOR/+= target

    _walk(parse_tree, record)
    return {name: next(iter(values)) for name, values in state.items()
            if values is not _DISQUALIFIED and len(values) == 1}


def _defs_in(statement, constants):
    """The constant-variable names this statement itself assigns."""
    names = set()

    def record(node):
        if (isinstance(node, Variable) and getattr(node, "isLValue", False)
                and node.identifier in constants):
            names.add(node.identifier)

    _walk_own(statement, record)
    return names


def _reads_in(statement, constants):
    """The constant-variable read nodes in this statement itself."""
    reads = []

    def record(node):
        if (isinstance(node, Variable) and not getattr(node, "isLValue", False)
                and node.identifier in constants):
            reads.append(node)

    _walk_own(statement, record)
    return reads


def _definite_assignment(blocks, constants):
    """id(block) -> constant names definitely assigned on entry to that block."""
    gen = {id(b): set().union(*[_defs_in(s, constants) for s in b.statements] or [set()])
           for b in blocks}
    universe = set(constants)
    entry = blocks[0] if blocks else None
    defined_out = {id(b): set(universe) for b in blocks}
    defined_in = {id(b): set() for b in blocks}

    changed = True
    while changed:
        changed = False
        for block in blocks:
            if block is entry:
                new_in = set()                       # the program start defines nothing
            else:
                preds = list(block.inEdges) + list(block.loopFromEdges)
                new_in = set(universe)
                for pred in preds:
                    new_in &= defined_out[id(pred)]
                if not preds:
                    new_in = set()
            new_out = new_in | gen[id(block)]
            if new_in != defined_in[id(block)] or new_out != defined_out[id(block)]:
                defined_in[id(block)] = new_in
                defined_out[id(block)] = new_out
                changed = True
    return defined_in


def _literal_for(value):
    if isinstance(value, bool):                      # bool is an int subclass
        return None
    if isinstance(value, str):
        literal = LiteralString(value=value)
        literal.actualType = StringOwlType()
        return literal
    if isinstance(value, int):
        literal = LiteralInteger(value=value)
        literal.actualType = (IntegerOwlType() if _INT32_MIN <= value <= _INT32_MAX
                              else LongIntegerOwlType())
        return literal
    if isinstance(value, float):
        literal = LiteralFloat(value=value)
        literal.actualType = FloatOwlType()
        return literal
    return None


_MAX_ITERATIONS = 64


def propagate_constants(ordered_basic_blocks, parse_tree, options=None):
    """Substitute reads of uniform-constant scalars with their literal values,
    where definite-assignment proves the value reaches the read. Iterated to a
    fixpoint so a chain (a=5 : b=a : c=b) resolves: once `a` is a literal, `b=a`
    becomes a constant assignment, and so on."""
    for _ in range(_MAX_ITERATIONS):
        constants = _uniform_constants(parse_tree)
        if not constants:
            return
        if _propagate_once(ordered_basic_blocks, parse_tree, constants) == 0:
            return


def _propagate_once(ordered_basic_blocks, parse_tree, constants):
    targets = []        # read nodes safe to replace
    for blocks in ordered_basic_blocks.values():
        if not blocks:
            continue
        defined_in = _definite_assignment(blocks, constants)
        for block in blocks:
            available = set(defined_in[id(block)])
            for statement in block.statements:
                for read in _reads_in(statement, constants):
                    if read.identifier in available:
                        targets.append(read)
                available |= _defs_in(statement, constants)

    substituted = 0
    for read in targets:
        literal = _literal_for(constants[read.identifier])
        if literal is None or read.parent is None:
            continue
        property_name, index = read.parent.findChild(read)
        if property_name is None:
            continue
        literal.lineNum = read.lineNum
        literal.parent = read.parent
        literal.parent_property = property_name
        literal.parent_index = index
        read.parent.setProperty(literal, property_name, index)
        substituted += 1
    return substituted
