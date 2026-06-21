"""Textual CIL emitter for the dotnet backend.

Lowers an analysed :class:`~owl_basic.codegen.backend.Program` to textual CIL
(``.il``) that the CoreCLR ``ilasm`` assembles into a .NET assembly. Output is
printed by calling into the OwlRuntime runtime library, whose default screen
mode is the headless raw console (stdout).

This is the first, deliberately small slice of the lowering — enough to compile
print/arithmetic programs such as six_times_seven. It reuses the opcode
knowledge of the legacy reflection-based ``codegen/clr/cil_visitor.py`` but
writes mnemonics as text instead of driving ``System.Reflection.Emit``.
"""

import re

from owl_basic.exceptions import CompileError, OwlBasicError
from owl_basic.owltyping.type_system import (
    AddressOwlType,
    ArrayOwlType,
    ByteOwlType,
    FloatOwlType,
    IntegerOwlType,
    LongIntegerOwlType,
    StringOwlType,
    SumOwlType,
)
from owl_basic.symbol_tables import SymbolInfo
from owl_basic.sigil import identifierToType
from owl_basic.ext.backends.dotnet.signatures import (
    MANIFEST_FILEPATH,
    SignatureManifest,
)

# Symbol modifiers that mean the variable is stored in a method (not globally).
_METHOD_SCOPED_MODIFIERS = frozenset(
    {SymbolInfo.modifier_arg, SymbolInfo.modifier_ref_arg,
     SymbolInfo.modifier_local, SymbolInfo.modifier_private}
)

# OwlRuntime call signatures come from the committed manifest, generated from the
# built assembly (see signatures.py) -- so the emitter no longer hand-writes a
# runtime method's CIL signature, and a drift from the DLL is caught by a test.
_MANIFEST = SignatureManifest.load(MANIFEST_FILEPATH)


def _runtime(method, *arg_types, cls="BasicCommands"):
    """The CIL ``call`` for an OwlRuntime method, with the overload chosen by
    *arg_types* (the CIL types of the pushed arguments)."""
    return _MANIFEST.call(cls, method, list(arg_types))


_PRINT_NEWLINE = _runtime("NewLine")

_MATH = "[System.Runtime]System.Math"

# math.pi as an IEEE-754 double literal -- identical to System.Math.PI (which is
# a const, so it cannot be loaded as a field in IL). Backs PI, RAD and DEG.
_PI = "3.141592653589793"

# INPUT reads a queue of typed values via the runtime, then dequeues each.
_TYPE_ARRAY = "class [System.Runtime]System.Type[]"
_QUEUE_OBJECT = "class [System.Collections]System.Collections.Generic.Queue`1<object>"
_GET_TYPE_FROM_HANDLE = (
    "call class [System.Runtime]System.Type "
    "[System.Runtime]System.Type::GetTypeFromHandle("
    "valuetype [System.Runtime]System.RuntimeTypeHandle)"
)
_CLR_TYPE_TOKEN = {
    "string": "[System.Runtime]System.String",
    "float64": "[System.Runtime]System.Double",
    "int32": "[System.Runtime]System.Int32",
    "int64": "[System.Runtime]System.Int64",
}

# CIL value types that must be boxed to reach an `object` slot (a sum/Object
# return). Reference types (string) are already assignable to object.
_BOXABLE_IL = frozenset(("int32", "int64", "float64"))

# OwlRuntime models BBC BASIC's address space as a byte array for ? indirection.
_MEMORY_ARRAY = _runtime("get_Memory", cls="MemoryMap")

_BYTE_INDIRECTIONS = frozenset({"UnaryByteIndirection", "DyadicByteIndirection"})
_INTEGER_INDIRECTIONS = frozenset({"UnaryIntegerIndirection", "DyadicIntegerIndirection"})

# DATA is compiled to a static string array read sequentially by READ.
_DATA_FIELD = "__data"
_DATA_ARRAY_TYPE = "string[]"
_DATA_INDEX_FIELD = "__dataIndex"

# Map a textual CIL operator mnemonic onto each binary arithmetic AST node.
# DIV/MOD operate on integer operands (the front-end types them so), so the same
# div/rem opcodes give BBC's integer division (truncating) and remainder.
_BINARY_OPS = {
    "Plus": "add",
    "Minus": "sub",
    "Multiply": "mul",
    "Divide": "div",
    "IntegerDivide": "div",
    "IntegerModulus": "rem",
}

# BBC transcendental functions -> the [System.Runtime]System.Math method. The
# argument and result are float64; LOG is base 10, LN is natural.
_MATH_UNARY = {
    "SinFunc": "Sin", "CosFunc": "Cos", "TanFunc": "Tan",
    "AtnFunc": "Atan", "AsnFunc": "Asin", "AcsFunc": "Acos",
    "ExpFunc": "Exp", "LnFunc": "Log", "LogFunc": "Log10",
}

# BBC BASIC's AND/OR/EOR are bitwise; with OWL booleans (0 / -1) they double as
# the logical connectives in conditions.
_LOGICAL_OPS = {
    "And": "and",
    "Or": "or",
    "Eor": "xor",
}

# Numeric relational operators, as CIL opcode sequences that leave an OWL
# boolean (0 / -1) on the stack. The trailing `neg` converts a CLR boolean
# (0 / 1) into BBC's 0 / -1; `<>`/`<=`/`>=` build on `ceq`/`clt`/`cgt`.
_RELATIONAL_OPS = {
    "Equal": ["ceq", "neg"],
    "NotEqual": ["ceq", "ldc.i4.1", "sub"],
    "LessThan": ["clt", "neg"],
    "GreaterThan": ["cgt", "neg"],
    "LessThanEqual": ["cgt", "ldc.i4.0", "ceq", "neg"],
    "GreaterThanEqual": ["clt", "ldc.i4.0", "ceq", "neg"],
}

_STRING_EQUALS = "call bool [System.Runtime]System.String::Equals(string, string)"
_STRING_COMPARE = "call int32 [System.Runtime]System.String::Compare(string, string)"

# String equality from String.Equals; ordering from the sign of String.Compare.
# All leave an OWL boolean (0 / -1).
_STRING_RELATIONAL = {
    "Equal": [_STRING_EQUALS, "neg"],
    "NotEqual": [_STRING_EQUALS, "ldc.i4.0", "ceq", "neg"],
    "LessThan": [_STRING_COMPARE, "ldc.i4.0", "clt", "neg"],
    "GreaterThan": [_STRING_COMPARE, "ldc.i4.0", "cgt", "neg"],
    "LessThanEqual": [_STRING_COMPARE, "ldc.i4.0", "cgt", "ldc.i4.0", "ceq", "neg"],
    "GreaterThanEqual": [_STRING_COMPARE, "ldc.i4.0", "clt", "ldc.i4.0", "ceq", "neg"],
}


class CodeGenerationError(OwlBasicError):
    """Raised when the emitter meets an AST node it cannot yet lower."""


# Map an OwlType onto the CIL type used for a local / runtime argument. Order
# matters: ChannelOwlType is an IntegerOwlType, ByteOwlType is distinct.
_IL_TYPES = [
    (StringOwlType, "string"),
    (FloatOwlType, "float64"),
    (LongIntegerOwlType, "int64"),
    (ByteOwlType, "int32"),
    (IntegerOwlType, "int32"),
]

# Element load/store opcodes for a 1-D array (vector), keyed by the element's
# CIL type. Multidimensional arrays use Get/Set method calls instead.
_LDELEM = {"int32": "ldelem.i4", "int64": "ldelem.i8", "float64": "ldelem.r8", "string": "ldelem.ref"}
_STELEM = {"int32": "stelem.i4", "int64": "stelem.i8", "float64": "stelem.r8", "string": "stelem.ref"}


def _il_type(owl_type):
    if isinstance(owl_type, ArrayOwlType):
        element = owl_type.elementType()
        element_il = _il_type(element) if element is not None else "int32"
        rank = owl_type.arrayRank() or 1     # rank is often unspecified -> 1-D
        return element_il + "[" + "," * (rank - 1) + "]"
    if isinstance(owl_type, SumOwlType):
        # A union of differing kinds (e.g. Integer|String) has no single CIL
        # primitive: erase it to object and box each value-typed arm at the
        # return site, tag-dispatching at the use site (see _print_call).
        return "object"
    for cls, il in _IL_TYPES:
        if isinstance(owl_type, cls):
            return il
    return "int32"


# Sigil -> a type-letter prefix, so a BBC identifier maps to a valid CIL name
# (and X$, X% and X stay distinct). Mirrors the legacy ctsName scheme.
_SIGIL_PREFIX = {"$": "s_", "%": "i_", "&": "b_", "~": "o_"}


def _global_field_name(identifier):
    """Map a global variable identifier to a CIL field name (e.g. ``score%`` -> ``i_score``)."""
    prefix = _SIGIL_PREFIX.get(identifier[-1:], "f_")
    stem = identifier[:-1] if identifier[-1:] in _SIGIL_PREFIX else identifier
    return prefix + _NON_IDENT.sub("_", stem)


def _field_name(identifier):
    """The static-field name for any variable reference. An array identifier
    ends in ``(`` (e.g. ``A%(``); its field gets an ``arr_`` prefix so the array
    ``A%()`` is distinct from the scalar ``A%``."""
    if identifier.endswith("("):
        return "arr_" + _global_field_name(identifier[:-1])
    return _global_field_name(identifier)


_MAIN_ENTRY = "__owl__main"

_NON_IDENT = re.compile(r"[^A-Za-z0-9_]")


def _method_name(owl_name):
    """Map an OWL routine name (e.g. ``PROCgreet``) to a CIL method name."""
    return _NON_IDENT.sub("_", owl_name)


def emit_program(program, assembly_name):
    """Render *program* as a complete textual CIL assembly.

    Each entry point (the main program and every PROC) becomes its own static
    method; ``PROC`` calls become ``call`` instructions between them.
    """
    diagnostics = getattr(program, "diagnostics", None) or []
    if diagnostics:
        # The program did not type-check. Lowering it would emit nonsense IL
        # (e.g. a string reinterpreted as a number), so refuse before assembly.
        raise CompileError(
            "cannot generate code: %d type error(s) -- %s"
            % (len(diagnostics), "; ".join(diagnostics))
        )
    blocks_by_entry = program.ordered_basic_blocks or {}
    signatures = _collect_signatures(blocks_by_entry)
    longjump_targets = _collect_longjump_targets(blocks_by_entry)
    line_mapper = program.line_mapper
    # BBC BASIC variables are global unless they are formal parameters or made
    # LOCAL/PRIVATE; globals are static fields shared by every method. The
    # registry (field name -> CIL type) is populated as methods are lowered.
    globals_registry = {}
    # DATA becomes a static string array; READ reads it sequentially. The array
    # is built at the top of Main (before any PROC that might READ runs).
    data = getattr(program, "data", None)
    data_items = list(data.data) if data is not None and data.data else []
    # data.index is keyed by *physical* line; RESTORE <line> targets *logical*
    # lines, so re-key by logical line number via the line mapper.
    data_index = {}
    if data is not None and data.index:
        line_mapper = program.line_mapper
        for physical, item_index in data.index.items():
            logical = line_mapper.physicalToLogical(physical)
            if logical is not None:
                data_index[logical] = item_index
    # Main initialises all globals to their BBC defaults (string globals to "",
    # not CLR null) via __reset, then builds the DATA array. __reset runs once
    # at the top (outside any longjump dispatch loop) and again on RUN.
    prologue = ["call void __reset()"]
    if data_items:
        prologue += _data_init_lines(data_items)
    methods = [
        _emit_method(
            entry_name, blocks, signatures, globals_registry, data_index,
            longjump_targets, line_mapper,
            prologue if entry_name == _MAIN_ENTRY else None,
            data_count=len(data_items),
        )
        for entry_name, blocks in blocks_by_entry.items()
    ]
    fields = "".join(
        ".field static %s %s\n" % (il_type, name)
        for name, il_type in globals_registry.items()
    )
    if data_items:
        fields += ".field static %s %s\n" % (_DATA_ARRAY_TYPE, _DATA_FIELD)
        fields += ".field static int32 %s\n" % _DATA_INDEX_FIELD
    # __reset is always defined (Main calls it to initialise globals; RUN reuses
    # it to clear them), generated once all globals are known.
    methods.append(_emit_reset_method(globals_registry, bool(data_items)))
    return _ASSEMBLY_TEMPLATE.format(
        name=assembly_name, fields=fields, methods="\n\n".join(methods)
    )


def _formal_arguments(define_procedure):
    """Yield the formal parameter Variables of a ``DEFPROC``, in order."""
    parameters = define_procedure.formalParameters
    if parameters is None:
        return []
    return [formal.argument for formal in parameters.arguments]


def _default_value(il_type):
    """The CIL instruction loading the BBC default for a type ("" / 0 / 0.0)."""
    if il_type.endswith("]"):
        return "ldnull"            # an array reference defaults to null
    if il_type == "string":
        return 'ldstr ""'
    if il_type == "float64":
        return "ldc.r8 0.0"
    if il_type == "int64":
        return "ldc.i8 0"
    return "ldc.i4.0"


def _collect_locals(blocks):
    """Return ``[(node, owl_type)]`` for LOCAL/PRIVATE items in a routine.

    Each node is the l-value made local -- usually a ``Variable`` (or whole
    ``Array``), but possibly a ``?``/``!``/``$`` indirection. Named items are
    de-duplicated by identifier; l-value items are kept as they appear.
    """
    named = {}
    others = []
    for block in blocks:
        for statement in block.statements:
            if type(statement).__name__ in ("Local", "Private"):
                for variable in (statement.variables or []):
                    if type(variable).__name__ in ("Variable", "Array"):
                        named.setdefault(variable.identifier, variable)
                    else:
                        others.append(variable)
    return [(node, node.actualType) for node in list(named.values()) + others]


_DEFINITIONS = frozenset({"DefineProcedure", "DefineFunction"})

_LONGJUMP_EXCEPTION = "[OwlRuntime]OwlRuntime.LongJumpException"
_OVERFLOW_EXCEPTION = "[System.Runtime]System.OverflowException"
_NUMBER_TOO_BIG = "[OwlRuntime]OwlRuntime.NumberTooBigException"


def _emit_reset_method(globals_registry, has_data):
    """A method that resets all globals (and the DATA pointer) for RUN."""
    lines = []
    for name, il_type in globals_registry.items():
        if il_type.endswith("]"):
            lines.append("ldnull")          # an array reference: unallocated until DIM
        elif il_type == "string":
            lines.append('ldstr ""')
        elif il_type == "float64":
            lines.append("ldc.r8 0.0")
        elif il_type == "int64":
            lines.append("ldc.i8 0")
        else:
            lines.append("ldc.i4.0")
        lines.append("stsfld %s %s" % (il_type, name))
    # RUN clears variables; also release any DIM byte blocks so re-running DIM
    # re-allocates from the start of the heap rather than leaking it.
    lines.append(_runtime("ResetHeap", cls="MemoryMap"))
    if has_data:
        lines += ["ldc.i4.m1", "stsfld int32 %s" % _DATA_INDEX_FIELD]
    lines.append("ret")
    body = "\n".join("        " + line for line in lines)
    return _METHOD_TEMPLATE.format(
        return_type="void", name="__reset", signature="", entrypoint="",
        locals="", body=body,
    )


def _collect_longjump_targets(blocks_by_entry):
    """The set of constant target lines of LONGJUMPs (GOTO out of a routine)."""
    targets = set()
    for blocks in blocks_by_entry.values():
        for block in blocks:
            for statement in block.statements:
                if type(statement).__name__ == "LongJump":
                    target = statement.targetLogicalLine
                    if type(target).__name__ == "LiteralInteger":
                        targets.add(int(target.value))
    return targets


def _collect_signatures(blocks_by_entry):
    """Map each PROC/FN name to ``(return_type, [param_types])`` for call sites.

    A PROC returns ``void``; a FN returns its inferred ``returnType``.
    """
    signatures = {}
    for entry_name, blocks in blocks_by_entry.items():
        if entry_name == _MAIN_ENTRY or not blocks:
            continue
        define = blocks[0].statements[0]
        kind = type(define).__name__
        if kind not in _DEFINITIONS:
            continue
        return_type = "void" if kind == "DefineProcedure" else _il_type(define.returnType)
        params = [_il_type(a.actualType) for a in _formal_arguments(define)]
        signatures[entry_name] = (return_type, params)
    return signatures


def _emit_method(entry_name, blocks, signatures, globals_registry, data_index,
                 longjump_targets=frozenset(), line_mapper=None, prologue=None,
                 data_count=0):
    """Render one routine's basic blocks as a complete CIL method."""
    is_main = entry_name == _MAIN_ENTRY
    if not is_main and entry_name not in signatures:
        # GOSUB subroutines (SUB...) come later.
        raise CodeGenerationError("Cannot yet emit a method for %r" % entry_name)

    return_type = "void" if is_main else signatures[entry_name][0]

    # A PROC/FN's formal parameters are received as method arguments (so the
    # caller can pass them), then -- like LOCALs -- copied into the global field
    # of that name for the duration of the routine (BBC dynamic scoping: a called
    # routine sees the caller's parameter values via the global).
    formal_params = []   # (identifier, owl_type, arg_index)
    parameters = []
    if not is_main and blocks and type(blocks[0].statements[0]).__name__ in _DEFINITIONS:
        for index, argument in enumerate(_formal_arguments(blocks[0].statements[0])):
            formal_params.append((argument, argument.actualType, index))
            parameters.append("%s A%d" % (_il_type(argument.actualType), index))

    emitter = _MethodEmitter(
        signatures=signatures,
        globals_registry=globals_registry,
        data_index=data_index,
        return_type=return_type,
        longjump_targets=longjump_targets,
        line_mapper=line_mapper,
        data_count=data_count,
    )

    # Both formal parameters and LOCAL/PRIVATE variables are the globals of that
    # name, saved on entry and restored on every exit (BBC dynamic scoping). A
    # parameter is then initialised from its incoming argument; a LOCAL to the
    # default. Set up before lowering so ENDPROC/=expr emit the restores.
    save_prologue = []
    param_names = {
        node.identifier for node, _, _ in formal_params
        if type(node).__name__ in ("Variable", "Array")
    }
    inits = (
        [] if is_main else
        [(node, owl_type, ("arg", arg_index))
         for node, owl_type, arg_index in formal_params]
        + [(node, owl_type, ("default", None))
           for node, owl_type in _collect_locals(blocks)
           if not (type(node).__name__ in ("Variable", "Array")
                   and node.identifier in param_names)]
    )
    for node, owl_type, (init_kind, init_arg) in inits:
        il_type = _il_type(owl_type)
        init_line = _ldarg(init_arg) if init_kind == "arg" else _default_value(il_type)
        if type(node).__name__ in ("Variable", "Array"):
            # Cheap path (the common case): the global field of that name, saved
            # on entry and restored on exit. Unchanged from before.
            field = _field_name(node.identifier)
            globals_registry[field] = il_type
            save_slot = emitter._local_slot("__save_%s" % field, owl_type)
            emitter.local_restores.append(
                ["ldloc V_%d" % save_slot, "stsfld %s %s" % (il_type, field)]
            )
            save_prologue += [
                "ldsfld %s %s" % (il_type, field),     # save the caller's value
                "stloc V_%d" % save_slot,
                init_line,                             # arg value, or the default
                "stsfld %s %s" % (il_type, field),
            ]
        else:
            # L-value formal/LOCAL (?A, $@%, ...): save/assign/restore the cell.
            save_prologue += emitter._bind_lvalue(node, owl_type, il_type, init_line)

    emitter.lower_blocks(blocks)
    emitter.finish()

    # A LONGJUMP (GOTO out of a routine) is thrown as an exception; if any land
    # in this method (only Main, in practice), wrap the body in a dispatch loop
    # that catches them and resumes at the labelled target statement.
    if emitter.landed_longjumps:
        emitter.lines = _wrap_longjump_dispatch(emitter, prologue)
    else:
        startup = list(prologue) if prologue else []
        # Runs before the first block (DATA array in Main; LOCAL save elsewhere).
        emitter.lines = startup + save_prologue + emitter.lines
        # Guarantee a return; a fall-through restores LOCALs first.
        if not emitter.lines or emitter.lines[-1] != "ret":
            emitter.lines += emitter._local_restore_lines() + ["ret"]

    # An int64->int32 narrowing that overflows raises OverflowException via the
    # CLR's own conv.ovf.i4 (cheap on the in-range path). Catch it once, at the
    # program boundary, and re-raise it as BBC error 20 ("Number too big"). The
    # catch wraps Main, so overflow thrown anywhere (including inside a PROC)
    # surfaces with the BBC message.
    if is_main:
        emitter.lines = _wrap_overflow_report(emitter.lines)

    name = "Main" if is_main else _method_name(entry_name)
    entrypoint = "    .entrypoint\n" if is_main else ""
    body = "\n".join("        " + line for line in emitter.lines)
    return _METHOD_TEMPLATE.format(
        return_type=return_type,
        name=name,
        signature=", ".join(parameters),
        entrypoint=entrypoint,
        locals=emitter.locals_declaration(),
        body=body,
    )


def _wrap_overflow_report(lines):
    """Wrap a method body so an int32-narrowing OverflowException re-raises as
    the BBC "Number too big" error. The CLR's conv.ovf.i4 does the (cheap)
    range check; this only pays on the exceptional path."""
    body = ["leave OWL_OVERFLOW_DONE" if line == "ret" else line for line in lines]
    return (
        [".try", "{"]
        + body
        + ["leave OWL_OVERFLOW_DONE", "}",
           "catch %s" % _OVERFLOW_EXCEPTION, "{",
           "pop",
           "newobj instance void %s::.ctor()" % _NUMBER_TOO_BIG,
           "throw", "}",
           "OWL_OVERFLOW_DONE:", "ret"]
    )


def _wrap_longjump_dispatch(emitter, prologue):
    """Wrap a method body so LONGJUMP exceptions resume at the target statement.

    Structure: one-time prologue, then a dispatch loop with the body in a .try;
    the catch records the exception's target line and re-enters, where a
    dispatcher branches to the matching ``L_<line>:`` label. Normal completion
    leaves the loop. The prologue (e.g. building the DATA array) is outside the
    loop so it runs once.
    """
    slot = emitter._local_slot("__ljTarget", IntegerOwlType())
    body = ["leave DONE" if line == "ret" else line for line in emitter.lines]
    dispatcher = []
    for line in sorted(emitter.landed_longjumps):
        dispatcher += ["ldloc V_%d" % slot, "ldc.i4 %d" % line, "beq L_%d" % line]
    return (
        list(prologue or [])
        + ["ldc.i4.0", "stloc V_%d" % slot, "DISPATCH:", ".try", "{"]
        + dispatcher
        + body
        + ["leave DONE", "}",
           "catch %s" % _LONGJUMP_EXCEPTION, "{",
           "ldfld int32 %s::TargetLogicalLine" % _LONGJUMP_EXCEPTION,
           "stloc V_%d" % slot,
           "leave DISPATCH", "}",
           "DONE:", "ret"]
    )


# Statements that emit their own control transfer (or end the method), so the
# block they end needs no implicit fall-through branch generated for it.
_BRANCHING_STATEMENTS = frozenset(
    {"If", "OnGoto", "End", "ReturnFromProcedure", "ReturnFromFunction",
     "LongJump", "Run", "Raise"}
)


_ASSEMBLY_TEMPLATE = """\
// Generated by OWL BASIC (dotnet backend)
.assembly extern System.Runtime {{ }}
.assembly extern System.Collections {{ }}
.assembly extern OwlRuntime {{ }}
.assembly {name} {{ }}
.module {name}.dll

{fields}
{methods}
"""


_METHOD_TEMPLATE = """\
.method static {return_type} {name}({signature}) cil managed
{{
{entrypoint}    .maxstack 8
{locals}{body}
}}"""


def _ldarg(index):
    return "ldarg.%d" % index if index <= 3 else "ldarg %d" % index


def _sole_loop_back(node, what):
    """Return the single loop-back target (REPEAT for UNTIL, FOR for NEXT)."""
    targets = list(node.loopBackEdges)
    if len(targets) != 1:
        raise CodeGenerationError("non-correlated %s" % what)
    return targets[0]


def _load_zero(il_type):
    if il_type == "float64":
        return "ldc.r8 0.0"
    if il_type == "int64":
        return "ldc.i8 0"
    return "ldc.i4.0"


def _data_init_lines(items):
    """CIL that builds the static DATA string array and resets the read index."""
    lines = ["ldc.i4 %d" % len(items), "newarr [System.Runtime]System.String"]
    for index, item in enumerate(items):
        lines += ["dup", "ldc.i4 %d" % index, "ldstr " + _il_string(item),
                  "stelem.ref"]
    lines += ["stsfld %s %s" % (_DATA_ARRAY_TYPE, _DATA_FIELD),
              "ldc.i4.m1", "stsfld int32 %s" % _DATA_INDEX_FIELD]
    return lines


class _MethodEmitter:
    def __init__(self, signatures=None,
                 globals_registry=None, data_index=None, return_type="void",
                 longjump_targets=frozenset(), line_mapper=None, data_count=0):
        self.lines = []
        self._local_slots = {}   # variable identifier -> local slot index
        self._local_types = []   # CIL type string, indexed by slot
        self._signatures = signatures or {}  # PROC/FN name -> (return_type, [params])
        self._return_type = return_type      # this method's CIL return type
        self._globals = globals_registry if globals_registry is not None else {}
        self._symbol_table = None  # the symbol table of the statement being lowered
        self._for_loops = {}       # id(ForToStep) -> loop state, shared with NEXT
        self._label_seq = 0        # for unique intra-method labels
        self._elementwise_index = None  # local slot when lowering a whole-array op
        self._data_index = data_index or {}  # DATA line number -> data array index
        self._data_count = data_count        # total DATA items (for RESTORE past end)
        self._longjump_targets = longjump_targets  # logical lines LONGJUMPs target
        self._line_mapper = line_mapper
        self.landed_longjumps = set()  # target lines that have an L_<line>: here
        self._input_queue_slot = None  # reused local for the INPUT result queue
        self.local_restores = []       # per formal/LOCAL: CIL lines that restore it
        self._end_label_used = False   # a branch (terminal IF) targets the method end

    def emit(self, text):
        self.lines.append(text)

    def _local_slot(self, identifier, owl_type):
        """Return the local slot for *identifier*, allocating one on first use."""
        if identifier not in self._local_slots:
            self._local_slots[identifier] = len(self._local_types)
            self._local_types.append(_il_type(owl_type))
        return self._local_slots[identifier]

    def locals_declaration(self):
        """Render the method's ``.locals init`` block (empty if no locals)."""
        if not self._local_types:
            return ""
        entries = ",\n".join(
            "        %s V_%d" % (il_type, slot)
            for slot, il_type in enumerate(self._local_types)
        )
        return "    .locals init (\n%s\n    )\n" % entries

    # -- basic blocks -------------------------------------------------------

    def lower_blocks(self, blocks):
        """Lower a routine's basic blocks (in topological order) with labels.

        Control flow is carried by the block-level CFG: each block gets a label,
        and a block whose single successor is not the next block in order ends
        with an explicit branch (otherwise it falls through).
        """
        self._block_index = {id(block): index for index, block in enumerate(blocks)}
        for index, block in enumerate(blocks):
            self.emit("%s:" % self._block_label(block))
            for statement in block.statements:
                # A statement that a LONGJUMP targets gets a label so the
                # dispatch loop can resume at it (targets are often mid-block).
                self._maybe_longjump_label(statement)
                # Variable storage (arg / local / global) is resolved against
                # the symbol table of the statement being lowered.
                self._symbol_table = getattr(statement, "symbolTable", None)
                self.lower_statement(statement)
            self._emit_fall_through(block, index)

    def _variable_field(self, variable):
        """The static field backing a variable reference.

        Every BBC variable is a global static field. Formal parameters and
        LOCAL/PRIVATE variables are also that global, saved on entry and restored
        on exit (dynamic scoping: a called routine sees the caller's value) by
        the save/restore prologue -- so all references are just the field.
        """
        field = _global_field_name(variable.identifier)
        if field not in self._globals:
            self._globals[field] = _il_type(variable.actualType)
        return field

    def _block_label(self, block):
        return "BB_%d" % self._block_index[id(block)]

    def _maybe_longjump_label(self, statement):
        if not self._longjump_targets or self._line_mapper is None:
            return
        logical = self._line_mapper.physicalToLogical(statement.lineNum)
        if logical in self._longjump_targets and logical not in self.landed_longjumps:
            self.landed_longjumps.add(logical)
            self.emit("L_%d:" % logical)

    def _emit_fall_through(self, block, index):
        last = block.statements[-1] if block.statements else None
        if last is not None and type(last).__name__ in _BRANCHING_STATEMENTS:
            return  # the statement emitted its own control transfer
        successors = list(block.outEdges)
        if len(successors) == 1:
            successor = successors[0]
            if self._block_index.get(id(successor)) != index + 1:
                self.emit("br " + self._block_label(successor))
        elif len(successors) == 0:
            # A terminal block (no forward successor) ends the routine. Falling
            # through is only correct when it is physically last; emit an
            # explicit ret so a block ordered after it -- e.g. a back-edge-only
            # `UNTIL FALSE`, which the constant-loop correlation leaves with no
            # forward edge -- is not entered by fall-through. The method wrapper
            # rewrites ret -> leave inside the overflow/longjump regions.
            self.emit("ret")

    def _method_end_label(self):
        """Label for the method's end, where a terminal IF branch lands."""
        self._end_label_used = True
        return "IF_END"

    def finish(self):
        # Emit the method-end label if a terminal IF branch targets it; the
        # trailing `ret` (added by _emit_method) then follows it.
        if self._end_label_used:
            self.emit("IF_END:")

    # -- statements ---------------------------------------------------------

    def lower_statement(self, node):
        name = type(node).__name__
        handler = getattr(self, "_stmt_" + name, None)
        if handler is None:
            raise CodeGenerationError("Cannot lower statement node %r" % name)
        handler(node)

    def _stmt_Print(self, node):
        items = list(node.printList or [])
        suppress_newline = False
        for index, print_item in enumerate(items):
            item = print_item.item
            kind = type(item).__name__
            if kind == "FormatManipulator":
                last = index == len(items) - 1
                self._emit_print_manipulator(item)
                # A trailing ';' (or ',') suppresses PRINT's end-of-line newline.
                if last and item.manipulator in (";", ","):
                    suppress_newline = True
            elif kind in ("TabH", "TabXY"):
                # PRINT TAB(x) / TAB(x,y): move the cursor (a void call).
                self.lower_expression(item.xCoord)
                if kind == "TabH":
                    self.emit(_runtime("TabH", "int32"))
                else:
                    self.lower_expression(item.yCoord)
                    self.emit(_runtime("TabXY", "int32", "int32"))
            elif kind == "Spc":
                # PRINT SPC(n): print n spaces (a void call).
                self.lower_expression(item.spaces)
                self.emit(_runtime("Spc", "int32"))
            else:
                self.lower_expression(item)
                self.emit(self._print_call(item))
        if not suppress_newline:
            self.emit(_PRINT_NEWLINE)

    def _emit_print_manipulator(self, node):
        manipulator = node.manipulator
        if manipulator == "'":
            self.emit(_PRINT_NEWLINE)            # force a newline
        elif manipulator == "~":
            self.emit(_runtime("HexFormat"))
        elif manipulator == ",":
            self.emit(_runtime("CompleteField"))
        elif manipulator == ";":
            pass  # a separator; trailing ';' suppresses the newline (above)
        else:
            raise CodeGenerationError(
                "PRINT manipulator %r not supported" % manipulator
            )

    def _stmt_ScalarAssignment(self, node):
        target = node.lValue
        name = type(target).__name__
        if name in _BYTE_INDIRECTIONS:
            # ?addr = v / base?offset = v : write a byte into the address space.
            self._push_memory_index(target)
            self.lower_expression(node.rValue)
            self.emit("stelem.i1")
            return
        if name in _INTEGER_INDIRECTIONS:
            # !addr = v / base!offset = v : write a 4-byte integer.
            self._push_indirection_address(target)
            self.lower_expression(node.rValue)
            self.emit(_runtime("WriteInteger", "int32", "int32", cls="MemoryMap"))
            return
        if name == "UnaryStringIndirection":
            # $addr = s$ : write the string and a CR terminator.
            self._push_indirection_address(target)
            self.lower_expression(node.rValue)
            self.emit(_runtime("WriteString", "int32", "string", cls="MemoryMap"))
            return
        if name == "UnaryFloatIndirection":
            # |addr = v : write an 8-byte float.
            self._push_indirection_address(target)
            self.lower_expression(node.rValue)
            self.emit(_runtime("WriteFloat", "int32", "float64", cls="MemoryMap"))
            return
        if name == "LomemValue":
            # LOMEM = v : the runtime models the BBC memory boundary as a property.
            self.lower_expression(node.rValue)
            self.emit(_runtime("set_Lomem", "int32"))
            return
        if name == "TimeValue":
            # TIME = v : reset the centisecond clock.
            self.lower_expression(node.rValue)
            self.emit(_runtime("set_Time", "int32"))
            return
        if name == "Indexer":
            # A(i) = v : store into an array element.
            self._store_element(target, node.rValue)
            return
        if name == "Variable" and target.identifier == "@%":
            # @% = v : the print/STR$ format control word. Route it to the
            # runtime's format state rather than storing a plain global. A string
            # r-value uses the printf-style form (@% = "G10.5"); else the packed
            # 32-bit control word.
            self.lower_expression(node.rValue)
            if isinstance(node.rValue.actualType, StringOwlType):
                self.emit(_runtime("SetAtPercentFormat", "string"))
            else:
                self.emit(_runtime("set_AtPercent", "int32"))
            return
        if name != "Variable":
            # Other pseudo-variable l-values come later.
            raise CodeGenerationError(
                "Cannot lower assignment to %r l-value" % name
            )
        self.lower_expression(node.rValue)
        self._store_variable(target)

    def _stmt_If(self, node):
        # Flow analysis emptied the clauses into their own blocks; branch to them
        # by block, falling through where the layout allows (cf. the legacy CIL
        # visitor). The condition leaves an OWL boolean (0 / -1) on the stack.
        self.lower_expression(node.condition)
        # Identify the true/false successor statements. One clause may be empty
        # (e.g. IF c THEN ELSE foo); whichever clause is present names its target,
        # and the remaining out-edge is the other branch.
        # The branch this clause does not name is the other out-edge -- or, when
        # the IF is the last statement, that fall-through path runs off the end of
        # the program (a terminal branch with no out-edge; see flowgraph_visitor).
        edges = set(node.outEdges)
        if node.trueClause:
            true_statement = node.trueClause[0]
            others = edges - {true_statement}
            false_statement = next(iter(others)) if others else None
            if len(others) > 1:
                raise CodeGenerationError("IF with %d false targets" % len(others))
        elif node.falseClause:
            false_statement = node.falseClause[0]
            others = edges - {false_statement}
            true_statement = next(iter(others)) if others else None
            if len(others) > 1:
                raise CodeGenerationError("IF with %d true targets" % len(others))
        else:
            raise CodeGenerationError("IF with no clauses")

        this_index = self._block_index[id(node.block)]

        def target(statement):
            # (label, block index) for a branch target; the method-end label and
            # None index for a terminal branch (one that falls off the end).
            if statement is None:
                return self._method_end_label(), None
            return (self._block_label(statement.block),
                    self._block_index[id(statement.block)])

        true_label, true_index = target(true_statement)
        false_label, false_index = target(false_statement)

        if true_index == this_index + 1:
            self.emit("brfalse " + false_label)          # fall through to true
        elif false_index == this_index + 1:
            self.emit("brtrue " + true_label)            # fall through to false
        else:
            self.emit("brtrue " + true_label)
            self.emit("br " + false_label)

    def _stmt_Goto(self, node):
        # GOTO carries no code itself: the branch to its (single) successor block
        # is generated by the block fall-through logic.
        pass

    def _stmt_Run(self, node):
        # RUN clears all variables and restarts from the first block. The reset
        # is a generated __reset method (globals are known only once every method
        # is lowered). RUN in a PROC would restart that method's first block, not
        # the program's -- only RUN in the main program is fully modelled.
        self.emit("call void __reset()")
        self.emit("br BB_0")

    def _stmt_OnGoto(self, node):
        # ON x GOTO a, b, c : a jump table. BBC selects 1-based, so subtract 1
        # for the 0-based CIL switch; out of range goes to the ELSE clause or
        # raises an ON-range error.
        self.lower_expression(node.switch)
        self.emit("ldc.i4.1")
        self.emit("sub")
        labels = ", ".join(
            self._block_label(target.block) for target in node.targetStatements
        )
        self.emit("switch (%s)" % labels)
        if node.outOfRangeStatement is not None:
            self.emit("br " + self._block_label(node.outOfRangeStatement.block))
        else:
            self.emit("newobj instance void "
                      "[OwlRuntime]OwlRuntime.OnRangeException::.ctor()")
            self.emit("throw")

    def _stmt_LongJump(self, node):
        # GOTO out of a routine: throw, to be caught by Main's dispatch loop.
        self.lower_expression(node.targetLogicalLine)
        self.emit("newobj instance void %s::.ctor(int32)" % _LONGJUMP_EXCEPTION)
        self.emit("throw")

    def _stmt_Raise(self, node):
        # Throw a named OwlRuntime exception carrying the source line (e.g.
        # ExecutedDefinitionException when control reaches a DEF line).
        logical = 0
        if self._line_mapper is not None:
            logical = self._line_mapper.physicalToLogical(node.lineNum) or 0
        self.emit("ldc.i4 %d" % logical)
        self.emit("newobj instance void [OwlRuntime]OwlRuntime.%s::.ctor(int32)"
                  % node.type)
        self.emit("throw")

    def _stmt_DefineProcedure(self, node):
        # The method header is the definition; the marker emits no code.
        pass

    def _stmt_DefineFunction(self, node):
        # The method header is the definition; the marker emits no code.
        pass

    def _stmt_Local(self, node):
        # LOCAL only declares which variables are method-scoped (the symbol
        # table records that); each gets a local slot when it is referenced.
        pass

    def _new_label(self, stem):
        self._label_seq += 1
        return "%s_%d" % (stem, self._label_seq)

    def _stmt_ForToStep(self, node):
        # counter = first; stash last and step in locals; mark the loop-body top.
        # The continuation test lives in the correlated NEXT (BBC FOR is
        # post-tested, so the body always runs at least once).
        counter = node.identifier
        counter_il = _il_type(counter.actualType)
        self.lower_expression(node.first)
        self._store_variable(counter)
        last_slot = self._local_slot("__for_last_%d" % id(node), counter.actualType)
        self.lower_expression(node.last)
        self.emit("stloc V_%d" % last_slot)
        step_slot = self._local_slot("__for_step_%d" % id(node), counter.actualType)
        self.lower_expression(node.step)
        self.emit("stloc V_%d" % step_slot)
        body_label = self._new_label("FOR_body")
        self.emit("%s:" % body_label)
        self._for_loops[id(node)] = (body_label, counter, last_slot, step_slot, counter_il)

    def _stmt_Next(self, node):
        for_statement = _sole_loop_back(node, "NEXT")
        body_label, counter, last_slot, step_slot, counter_il = self._for_loops[
            id(for_statement)
        ]
        # counter += step
        self._load_variable(counter)
        self.emit("ldloc V_%d" % step_slot)
        self.emit("add")
        self._store_variable(counter)
        # Continue while the counter has not passed `last`, in the step's
        # direction: step > 0 -> while counter <= last, else while counter >= last.
        positive = self._new_label("FOR_pos")
        loop_back = self._new_label("FOR_back")
        self.emit("ldloc V_%d" % step_slot)
        self.emit(_load_zero(counter_il))
        self.emit("bgt " + positive)
        # negative step: NOT (counter < last)
        self._load_variable(counter)
        self.emit("ldloc V_%d" % last_slot)
        self.emit("clt")
        self.emit("ldc.i4.0")
        self.emit("ceq")
        self.emit("br " + loop_back)
        self.emit("%s:" % positive)
        # positive step: NOT (counter > last)
        self._load_variable(counter)
        self.emit("ldloc V_%d" % last_slot)
        self.emit("cgt")
        self.emit("ldc.i4.0")
        self.emit("ceq")
        self.emit("%s:" % loop_back)
        self.emit("brtrue " + body_label)

    def _stmt_Input(self, node):
        # Prompt strings/manipulators interleave with variables; a run of
        # consecutive variables is read together (one line, comma-separated),
        # following the legacy CIL visitor's query-prompt logic.
        items = [print_item.item for print_item in (node.inputList or [])]
        query = True
        index = 0
        while index < len(items):
            item = items[index]
            kind = type(item).__name__
            if kind == "LiteralString":
                self.lower_expression(item)
                self.emit(self._print_call(item))
                query = False
                index += 1
            elif kind == "InputManipulator":
                if item.manipulator == "'":
                    self.emit(_PRINT_NEWLINE)
                else:                       # ',' / ';' re-enable the '?' prompt
                    query = True
                index += 1
            elif kind == "Variable":
                # A run of variables read together (one line): bare, or separated
                # by ',' / ';' manipulators (which mean "same input line").
                run = [item]
                index += 1
                while index < len(items):
                    nxt = items[index]
                    if type(nxt).__name__ == "Variable":
                        run.append(nxt)
                        index += 1
                    elif (type(nxt).__name__ == "InputManipulator"
                          and nxt.manipulator in (",", ";")
                          and index + 1 < len(items)
                          and type(items[index + 1]).__name__ == "Variable"):
                        run.append(items[index + 1])
                        index += 2
                    else:
                        break
                self._emit_input_run(run, query)
            else:
                raise CodeGenerationError("INPUT item %r not supported" % kind)

    def _emit_input_run(self, variables, query):
        # Build a Type[] of the variables' types and read them via the runtime.
        self.emit("ldc.i4.%d" % (1 if query else 0))    # bool prompt
        self.emit("ldc.i4 %d" % len(variables))
        self.emit("newarr [System.Runtime]System.Type")
        for index, variable in enumerate(variables):
            self.emit("dup")
            self.emit("ldc.i4 %d" % index)
            self.emit("ldtoken %s" % _CLR_TYPE_TOKEN[_il_type(variable.actualType)])
            self.emit(_GET_TYPE_FROM_HANDLE)
            self.emit("stelem.ref")
        self.emit("call %s [OwlRuntime]OwlRuntime.BasicCommands::Input(bool, %s)"
                  % (_QUEUE_OBJECT, _TYPE_ARRAY))
        queue_slot = self._input_queue_local()
        self.emit("stloc V_%d" % queue_slot)
        for variable in variables:
            self.emit("ldloc V_%d" % queue_slot)
            self.emit("callvirt instance !0 %s::Dequeue()" % _QUEUE_OBJECT)
            il = _il_type(variable.actualType)
            if il == "string":
                self.emit("castclass [System.Runtime]System.String")
            else:
                self.emit("unbox.any %s" % il)
            self._store_variable(variable)

    def _input_queue_local(self):
        if self._input_queue_slot is None:
            self._input_queue_slot = len(self._local_types)
            self._local_types.append(_QUEUE_OBJECT)
        return self._input_queue_slot

    def _stmt_Mode(self, node):
        if node.number is None:
            raise CodeGenerationError("extended MODE syntax not yet supported")
        self.lower_expression(node.number)
        self.emit(_runtime("Mode", "int32"))

    def _stmt_Cls(self, node):
        # CLS: clear the text screen and home the cursor.
        self.emit(_runtime("Cls"))

    def _stmt_Colour(self, node):
        # COLOUR n: set the text foreground (n < 128) or background colour. The
        # RISC OS TINT form is not modelled by the runtime yet.
        if node.tint is not None:
            raise CodeGenerationError("COLOUR ... TINT not yet supported")
        self.lower_expression(node.colour)
        self.emit(_runtime("Colour", "int32"))

    def _stmt_Gcol(self, node):
        # GCOL mode, colour: set the graphics colour and plot action.
        if node.tint is not None:
            raise CodeGenerationError("GCOL ... TINT not yet supported")
        self.lower_expression(node.mode)
        self.lower_expression(node.logicalColour)
        self.emit(_runtime("Gcol", "int32", "int32"))

    def _stmt_Move(self, node):
        # MOVE x,y is PLOT 4 (absolute) / PLOT 0 (relative) -- move, no draw.
        self._emit_plot(0 if node.relative else 4, node.xCoord, node.yCoord)

    def _stmt_Draw(self, node):
        # DRAW x,y is PLOT 5 (absolute) / PLOT 1 (relative) -- draw a line.
        self._emit_plot(1 if node.relative else 5, node.xCoord, node.yCoord)

    def _stmt_Plot(self, node):
        # PLOT mode,x,y: the mode carries the absolute/relative and draw action.
        self.lower_expression(node.mode)
        self._push_plot_coord(node.xCoord)
        self._push_plot_coord(node.yCoord)
        self.emit(_runtime("Plot", "int32", "int32", "int32"))

    def _emit_plot(self, plot_mode, x_node, y_node):
        self.emit("ldc.i4 %d" % plot_mode)
        self._push_plot_coord(x_node)
        self._push_plot_coord(y_node)
        self.emit(_runtime("Plot", "int32", "int32", "int32"))

    def _push_plot_coord(self, node):
        # Plot coordinates are int32; a real-valued expression (e.g. i%*dx with a
        # real dx) narrows to integer.
        self.lower_expression(node)
        self._coerce("int32", node.actualType)

    def _stmt_Vdu(self, node):
        # VDU sends raw bytes to the VDU driver. Each item is a byte (',' form,
        # length 1) or a 16-bit word ('; form', length 2, low byte then high).
        items = node.bytes
        if not isinstance(items, list):     # VduList not elided to a plain list
            items = items.items
        for vdu_item in items:
            self.lower_expression(vdu_item.item)
            if vdu_item.length == 2:
                self.emit("conv.i2")
                self.emit(_runtime("Vdu", "int16"))
            else:
                self.emit("conv.u1")
                self.emit(_runtime("Vdu", "uint8"))

    def _stmt_Data(self, node):
        # DATA is compiled to a static array (built in Main); no inline code.
        pass

    def _stmt_Restore(self, node):
        target = node.targetLogicalLine
        if target is None:
            index = 0                       # bare RESTORE: back to the first item
        elif type(target).__name__ == "LiteralInteger":
            # RESTORE <line>: the first DATA item on or after that line, resolved
            # at compile time.
            index = self._resolve_restore(int(target.value))
        else:
            self._emit_dynamic_restore(target)
            return
        # The read index is pre-incremented, so point one before the target.
        self.emit("ldc.i4 %d" % (index - 1))
        self.emit("stsfld int32 %s" % _DATA_INDEX_FIELD)

    def _emit_dynamic_restore(self, target):
        # RESTORE <expr>: an inline jump table over the (compile-time-known) DATA
        # lines, since the read index must be set from a runtime line number.
        # BBC RESTORE points at the first DATA statement *at or after* the given
        # line, not only an exact match -- so, testing the DATA lines in
        # ascending order, the first line with target <= line is the target
        # (this matches the constant path in _resolve_restore).
        self.lower_expression(target)            # line number on the stack
        end = self._new_label("ENDR")
        cases = []
        for line, item_index in sorted(self._data_index.items()):
            label = self._new_label("SETR")
            self.emit("dup")
            self.emit("ldc.i4 %d" % line)
            self.emit("ble %s" % label)
            cases.append((label, item_index))
        self.emit("pop")                         # no DATA at or after: past the end
        self.emit("ldc.i4 %d" % (self._data_count - 1))
        self.emit("stsfld int32 %s" % _DATA_INDEX_FIELD)
        self.emit("br %s" % end)
        for label, item_index in cases:
            self.emit("%s:" % label)
            self.emit("pop")
            self.emit("ldc.i4 %d" % (item_index - 1))
            self.emit("stsfld int32 %s" % _DATA_INDEX_FIELD)
            self.emit("br %s" % end)
        self.emit("%s:" % end)

    def _resolve_restore(self, line):
        if line in self._data_index:
            return self._data_index[line]
        at_or_after = [n for n in self._data_index if n >= line]
        if not at_or_after:
            # No DATA at or after the line: point past the end so the next READ
            # is out of data (matching BBC, which would error then).
            return self._data_count
        return self._data_index[min(at_or_after)]

    def _stmt_Repeat(self, node):
        # The loop top is just the start of this block; UNTIL branches back to
        # its label. REPEAT itself emits no code.
        pass

    def _stmt_Until(self, node):
        # Loop back to the correlated REPEAT while the condition is false.
        self.lower_expression(node.condition)
        repeat = _sole_loop_back(node, "UNTIL")
        self.emit("brfalse " + self._block_label(repeat.block))

    def _stmt_CallProcedure(self, node):
        for actual in node.actualParameters or []:
            self.lower_expression(actual)
        _, params = self._signatures.get(node.name, ("void", []))
        self.emit("call void %s(%s)" % (_method_name(node.name), ", ".join(params)))

    def _local_restore_lines(self):
        """Restore each formal/LOCAL on routine exit (BBC dynamic scoping).

        Each entry is the ready-made CIL line list that writes the saved value
        back -- to a global field for a simple variable, or to a memory cell for
        an l-value formal/LOCAL.
        """
        lines = []
        for restore in self.local_restores:
            lines += restore
        return lines

    def _stmt_ReturnFromProcedure(self, node):
        self.lines.extend(self._local_restore_lines())
        self.emit("ret")

    def _stmt_ReturnFromFunction(self, node):
        # =expr : push the result (computed with LOCALs still in effect), coerce
        # to the return type, restore LOCALs, then ret.
        self.lower_expression(node.returnValue)
        self._coerce(self._return_type, node.returnValue.actualType)
        self.lines.extend(self._local_restore_lines())
        self.emit("ret")

    def _coerce(self, target_il, value_type):
        """Insert a numeric conversion if a value's type differs from target_il."""
        value_il = _il_type(value_type)
        if value_il == target_il:
            return
        if target_il == "object":
            # A sum/Object return: box a value-typed arm so it becomes an object
            # reference (a string arm is already one). The boxed cell carries the
            # runtime type, which the use site tag-dispatches on.
            if value_il in _BOXABLE_IL:
                self.emit("box %s" % _CLR_TYPE_TOKEN[value_il])
            return
        conversions = {"float64": "conv.r8", "int64": "conv.i8", "int32": "conv.i4"}
        if target_il in conversions and value_il in conversions:
            self.emit(conversions[target_il])

    def _stmt_StarCommand(self, node):
        # *HELP / *FX19 / ... : hand the text after the leading '*' to the OS
        # command interpreter (OSCLI). Every star command is treated alike.
        self.emit("ldstr " + _il_string(node.command.lstrip("*")))
        self.emit(_runtime("Oscli", "string"))

    def _stmt_Oscli(self, node):
        # OSCLI <string> : evaluate the command string and hand it to the OS.
        self.lower_expression(node.command)
        self.emit(_runtime("Oscli", "string"))

    def _stmt_Rem(self, node):
        # A comment generates no code.
        pass

    def _stmt_End(self, node):
        # Returning from Main ends the program; the template's trailing `ret`
        # also covers a program with no explicit END.
        self.emit("ret")

    # -- expressions --------------------------------------------------------

    def lower_expression(self, node):
        name = type(node).__name__
        if name in _BINARY_OPS:
            self.lower_expression(node.lhs)
            self.lower_expression(node.rhs)
            self.emit(_BINARY_OPS[name])
            return
        if name in _LOGICAL_OPS:
            self.lower_expression(node.lhs)
            self.lower_expression(node.rhs)
            self.emit(_LOGICAL_OPS[name])
            return
        if name in _RELATIONAL_OPS:
            self._lower_relational(node)
            return
        if name in _MATH_UNARY:
            self.lower_expression(node.factor)
            if not isinstance(node.factor.actualType, FloatOwlType):
                self.emit("conv.r8")
            self.emit("call float64 %s::%s(float64)" % (_MATH, _MATH_UNARY[name]))
            return
        handler = getattr(self, "_expr_" + name, None)
        if handler is None:
            raise CodeGenerationError("Cannot lower expression node %r" % name)
        handler(node)

    def _lower_relational(self, node):
        name = type(node).__name__
        string_operands = isinstance(node.lhs.actualType, StringOwlType) or isinstance(
            node.rhs.actualType, StringOwlType
        )
        self.lower_expression(node.lhs)
        self.lower_expression(node.rhs)
        opcodes = _STRING_RELATIONAL[name] if string_operands else _RELATIONAL_OPS[name]
        for opcode in opcodes:
            self.emit(opcode)

    def _expr_Power(self, node):
        # BBC '^' is exponentiation; the type checker has coerced both operands
        # to float, so this is a straight System.Math.Pow(double, double).
        self.lower_expression(node.lhs)
        self.lower_expression(node.rhs)
        self.emit("call float64 %s::Pow(float64, float64)" % _MATH)

    def _expr_LiteralString(self, node):
        self.emit("ldstr " + _il_string(node.value))

    def _expr_LiteralInteger(self, node):
        # A literal typed as a 64-bit LongInteger (too big for int32) loads wide.
        if isinstance(node.actualType, LongIntegerOwlType):
            self.emit("ldc.i8 %d" % int(node.value))
        else:
            self.emit("ldc.i4 %d" % int(node.value))

    def _expr_LiteralFloat(self, node):
        self.emit("ldc.r8 %r" % float(node.value))

    def _load_variable(self, variable):
        if variable.identifier == "@%":
            # @% reads back the current print/STR$ format control word.
            self.emit(_runtime("get_AtPercent"))
            return
        field = self._variable_field(variable)
        self.emit("ldsfld %s %s" % (self._globals[field], field))

    def _store_variable(self, variable):
        field = self._variable_field(variable)
        self.emit("stsfld %s %s" % (self._globals[field], field))

    def _expr_Variable(self, node):
        self._load_variable(node)

    # -- arrays -------------------------------------------------------------

    def _array_field(self, identifier, rank):
        """The static field, array CIL type and element CIL type for an array
        reference. ``identifier`` includes the open paren (e.g. ``A%(``); the
        sigil before it gives the element type. The ``arr_`` prefix keeps the
        array variable distinct from the scalar of the same name (``A%``)."""
        base = identifier[:-1] if identifier.endswith("(") else identifier
        element_il = _il_type(identifierToType(base))
        array_il = element_il + "[" + "," * (rank - 1) + "]"
        field = "arr_" + _global_field_name(base)
        self._globals.setdefault(field, array_il)
        return field, array_il, element_il

    def _push_indices(self, indices):
        """Push each (integer) subscript onto the stack."""
        for index in indices:
            self.lower_expression(index)
            if isinstance(getattr(index, "actualType", None), FloatOwlType):
                self.emit("conv.i4")     # BBC subscripts are integers

    def _throw_bad_dim(self, node):
        """Throw BadDimException carrying the source line."""
        logical = 0
        if self._line_mapper is not None:
            logical = self._line_mapper.physicalToLogical(node.lineNum) or 0
        self.emit("ldc.i4 %d" % logical)
        self.emit("newobj instance void "
                  "[OwlRuntime]OwlRuntime.BadDimException::.ctor(int32)")
        self.emit("throw")

    def _stmt_AllocateArray(self, node):
        """DIM A(n[,m...]): allocate an array of n+1 (by m+1...) elements.

        One dimension is a CIL vector (``newarr``); more use the rectangular
        array type's ``.ctor``, which takes a length per dimension. BBC forbids
        re-DIMing, so an already-allocated (non-null) array is a Bad DIM."""
        dimensions = node.dimensions
        rank = len(dimensions)
        field, array_il, element_il = self._array_field(node.identifier, rank)
        already = self._new_label("dim_ok")
        self.emit("ldsfld %s %s" % (array_il, field))
        self.emit("brfalse %s" % already)        # null -> not yet allocated -> OK
        self._throw_bad_dim(node)
        self.emit("%s:" % already)
        for dimension in dimensions:
            self.lower_expression(dimension)
            if isinstance(getattr(dimension, "actualType", None), FloatOwlType):
                self.emit("conv.i4")
            self.emit("ldc.i4.1")
            self.emit("add")             # DIM A(n) -> 0..n -> n+1 elements
        if rank == 1:
            self.emit("newarr %s" % element_il)
        else:
            args = ", ".join(["int32"] * rank)
            self.emit("newobj instance void %s::.ctor(%s)" % (array_il, args))
        self.emit("stsfld %s %s" % (array_il, field))

    def _stmt_AllocateBlock(self, node):
        """DIM b n: reserve n+1 bytes of the address space and store the base
        address in b. The block is then read/written through ?/!/$ indirection,
        which index the same MemoryMap byte array, so the address must come from
        it (not an independent array). BadDimException on a negative size or an
        exhausted heap is raised by MemoryMap.Allocate."""
        self.lower_expression(node.size)
        if isinstance(getattr(node.size, "actualType", None), FloatOwlType):
            self.emit("conv.i4")
        self.emit("ldc.i4.1")
        self.emit("add")                 # DIM b n -> n+1 bytes (b?0 .. b?n)
        self.emit(_runtime("Allocate", "int32", cls="MemoryMap"))
        self._store_variable(node.identifier)

    def _array_rank(self, node):
        """The rank of a whole-array reference -- from its type if known, else
        1 (array params/actuals usually leave rank unspecified)."""
        owl_type = getattr(node, "actualType", None)
        if isinstance(owl_type, ArrayOwlType) and owl_type.arrayRank():
            return owl_type.arrayRank()
        return 1

    def _expr_Array(self, node):
        """A whole-array reference. Inside a whole-array assignment it means the
        i-th element of that array (B%() -> B%[i]); elsewhere (a PROC/FN actual)
        it pushes the array reference itself."""
        if self._elementwise_index is not None:
            field, array_il, element_il = self._array_field(node.identifier, 1)
            self.emit("ldsfld %s %s" % (array_il, field))
            self.emit("ldloc V_%d" % self._elementwise_index)
            self.emit(_LDELEM[element_il])
            return
        field, array_il, _element = self._array_field(node.identifier,
                                                       self._array_rank(node))
        # Rank isn't tracked on array param/actual types, so we assume 1-D; if the
        # array was actually DIMmed multidimensional, fail cleanly rather than
        # passing a mismatched reference.
        if "," in self._globals.get(field, ""):
            raise CodeGenerationError(
                "passing a multidimensional array as a parameter is not "
                "supported yet")
        self.emit("ldsfld %s %s" % (array_il, field))

    def _stmt_ArrayAssignment(self, node):
        """Whole-array assignment A() = <expr> (BASIC V): assign every element.

        Lowered as a loop over the target's elements; the right-hand side is
        evaluated element-wise, so a scalar fills (A() = 0), a whole array copies
        (A() = B()), and a mix is applied per element (A() = B() + C()). One
        dimension for now; the RHS is a single expression."""
        target = node.lValue
        rvalues = node.rValue
        if len(rvalues) != 1:
            raise CodeGenerationError(
                "array initialiser lists (A() = a, b, ...) are not supported yet")
        # The real rank is the one the array was DIMmed with (registered field
        # type), not the 1-D type we would compute here -- check that before the
        # 1-D element loop, so a multidim array fails cleanly rather than silently.
        if "," in self._globals.get(_field_name(target.identifier), ""):
            raise CodeGenerationError(
                "whole-array operations on multidimensional arrays are not "
                "supported yet")
        field, array_il, element_il = self._array_field(target.identifier, 1)
        rhs = rvalues[0]
        index = self._local_slot("__wa_index", IntegerOwlType())
        top = self._new_label("wa_top")
        end = self._new_label("wa_end")
        self.emit("ldc.i4.0")
        self.emit("stloc V_%d" % index)
        self.emit("%s:" % top)
        self.emit("ldloc V_%d" % index)                 # i >= length -> done
        self.emit("ldsfld %s %s" % (array_il, field))
        self.emit("ldlen")
        self.emit("conv.i4")
        self.emit("bge %s" % end)
        self.emit("ldsfld %s %s" % (array_il, field))   # target[i] = <rhs(i)>
        self.emit("ldloc V_%d" % index)
        self._elementwise_index = index
        self.lower_expression(rhs)
        self._elementwise_index = None
        self.emit(_STELEM[element_il])
        self.emit("ldloc V_%d" % index)                 # i = i + 1
        self.emit("ldc.i4.1")
        self.emit("add")
        self.emit("stloc V_%d" % index)
        self.emit("br %s" % top)
        self.emit("%s:" % end)

    def _expr_Indexer(self, node):
        """A(i[,j...]) as an r-value: load the element."""
        indices = node.indices
        rank = len(indices)
        field, array_il, element_il = self._array_field(node.identifier, rank)
        self.emit("ldsfld %s %s" % (array_il, field))
        self._push_indices(indices)
        if rank == 1:
            self.emit(_LDELEM[element_il])
        else:
            args = ", ".join(["int32"] * rank)
            self.emit("call instance %s %s::Get(%s)" % (element_il, array_il, args))

    def _store_element(self, node, rvalue):
        """A(i[,j...]) = v: store into an array element."""
        indices = node.indices
        rank = len(indices)
        field, array_il, element_il = self._array_field(node.identifier, rank)
        self.emit("ldsfld %s %s" % (array_il, field))
        self._push_indices(indices)
        self.lower_expression(rvalue)
        if rank == 1:
            self.emit(_STELEM[element_il])
        else:
            args = ", ".join(["int32"] * rank)
            self.emit("call instance void %s::Set(%s, %s)"
                      % (array_il, args, element_il))

    def _push_memory_index(self, indirection):
        """Push the OwlRuntime address-space byte array and the target index.

        ``?addr`` indexes at ``addr``; ``base?offset`` at ``base + offset``.
        """
        self.emit(_MEMORY_ARRAY)
        if type(indirection).__name__ == "UnaryByteIndirection":
            self.lower_expression(indirection.expression)
        else:  # DyadicByteIndirection
            self.lower_expression(indirection.base)
            self.lower_expression(indirection.offset)
            self.emit("add")

    def _expr_UnaryByteIndirection(self, node):
        self._push_memory_index(node)
        self.emit("ldelem.u1")   # unsigned: ?addr yields 0..255

    def _expr_DyadicByteIndirection(self, node):
        self._push_memory_index(node)
        self.emit("ldelem.u1")

    def _push_indirection_address(self, node):
        """Push the integer target address of an indirection.

        ``!addr``/``$addr``/``|addr`` -> ``addr``; ``base!offset`` -> ``base +
        offset``. (Byte ``?`` uses :meth:`_push_memory_index` and inline ldelem.)
        """
        if type(node).__name__.startswith("Unary"):
            self.lower_expression(node.expression)
        else:  # dyadic
            self.lower_expression(node.base)
            self.lower_expression(node.offset)
            self.emit("add")

    def _expr_UnaryIntegerIndirection(self, node):
        self._push_indirection_address(node)
        self.emit(_runtime("ReadInteger", "int32", cls="MemoryMap"))

    def _expr_DyadicIntegerIndirection(self, node):
        self._push_indirection_address(node)
        self.emit(_runtime("ReadInteger", "int32", cls="MemoryMap"))

    def _expr_UnaryStringIndirection(self, node):
        self._push_indirection_address(node)
        self.emit(_runtime("ReadString", "int32", cls="MemoryMap"))

    def _expr_UnaryFloatIndirection(self, node):
        self._push_indirection_address(node)
        self.emit(_runtime("ReadFloat", "int32", cls="MemoryMap"))

    # -- l-value formal/LOCAL binding ---------------------------------------

    def _capture(self, thunk):
        """Run *thunk* (which emits) and return only the lines it emitted,
        leaving the main buffer untouched. Lets us lower an expression into a
        separately-built prologue."""
        saved, self.lines = self.lines, []
        try:
            thunk()
            return self.lines
        finally:
            self.lines = saved

    def _lvalue_load(self, node, addr_slot):
        """Lines pushing the value currently at an indirection l-value (address
        held in *addr_slot*)."""
        name = type(node).__name__
        addr = "ldloc V_%d" % addr_slot
        if name in _BYTE_INDIRECTIONS:
            return [_MEMORY_ARRAY, addr, "ldelem.u1"]
        if name in _INTEGER_INDIRECTIONS:
            return [addr, _runtime("ReadInteger", "int32", cls="MemoryMap")]
        if name == "UnaryStringIndirection":
            return [addr, _runtime("ReadString", "int32", cls="MemoryMap")]
        if name == "UnaryFloatIndirection":
            return [addr, _runtime("ReadFloat", "int32", cls="MemoryMap")]
        raise CodeGenerationError(
            "Cannot bind l-value formal/LOCAL of kind %r" % name
        )

    def _lvalue_store(self, node, addr_slot, value_lines):
        """Lines storing *value_lines*' value into an indirection l-value
        (address held in *addr_slot*)."""
        name = type(node).__name__
        addr = "ldloc V_%d" % addr_slot
        if name in _BYTE_INDIRECTIONS:
            return [_MEMORY_ARRAY, addr] + value_lines + ["stelem.i1"]
        if name in _INTEGER_INDIRECTIONS:
            return [addr] + value_lines + [_runtime("WriteInteger", "int32", "int32", cls="MemoryMap")]
        if name == "UnaryStringIndirection":
            return [addr] + value_lines + [_runtime("WriteString", "int32", "string", cls="MemoryMap")]
        if name == "UnaryFloatIndirection":
            return [addr] + value_lines + [_runtime("WriteFloat", "int32", "float64", cls="MemoryMap")]
        raise CodeGenerationError(
            "Cannot bind l-value formal/LOCAL of kind %r" % name
        )

    def _bind_lvalue(self, node, owl_type, il_type, init_line):
        """Save / assign / restore an l-value formal or LOCAL.

        Handles ?/!/$/| indirection and array elements. The *locator* (the
        address, or the element's subscripts) is captured once on entry, so the
        restore writes back the same cell even if the body mutates the locator
        expression; the cell's contents are saved, the incoming argument/default
        assigned, and a restore registered. Returns the entry (save+assign) CIL.
        """
        save_slot = self._local_slot("__save_%d" % id(node), owl_type)
        if type(node).__name__ == "Indexer":
            capture, load, store = self._array_element_accessors(node)
        else:
            capture, load, store = self._indirection_accessors(node)
        entry = (
            capture
            + load + ["stloc V_%d" % save_slot]      # save the cell's current value
            + store([init_line])                     # assign the argument / default
        )
        self.local_restores.append(store(["ldloc V_%d" % save_slot]))
        return entry

    def _indirection_accessors(self, node):
        """``(capture, load, store)`` for a ?/!/$/| indirection l-value, where
        *capture* stores the address in a slot and *load*/``store(value_lines)``
        read/write through it."""
        addr_slot = self._local_slot("__addr_%d" % id(node), AddressOwlType())
        capture = self._capture(lambda: self._push_indirection_address(node)) + [
            "stloc V_%d" % addr_slot
        ]
        load = self._lvalue_load(node, addr_slot)
        store = lambda value_lines: self._lvalue_store(node, addr_slot, value_lines)
        return capture, load, store

    def _array_element_accessors(self, node):
        """``(capture, load, store)`` for an array-element l-value, A(i[,j...]).

        The subscripts are captured into slots so the same element is restored
        even if the body changes the index variables."""
        indices = getattr(node.indices, "expressions", node.indices)
        rank = len(indices)
        field, array_il, element_il = self._array_field(node.identifier, rank)
        capture = []
        index_slots = []
        for k, index_expr in enumerate(indices):
            slot = self._local_slot("__idx_%d_%d" % (id(node), k), IntegerOwlType())
            capture += self._capture(lambda e=index_expr: self.lower_expression(e))
            capture += ["stloc V_%d" % slot]
            index_slots.append(slot)
        locator = ["ldsfld %s %s" % (array_il, field)] + [
            "ldloc V_%d" % slot for slot in index_slots
        ]
        if rank == 1:
            load = locator + [_LDELEM[element_il]]
            store = lambda value_lines: locator + value_lines + [_STELEM[element_il]]
        else:
            args = ", ".join(["int32"] * rank)
            load = locator + ["call instance %s %s::Get(%s)" % (element_il, array_il, args)]
            store = lambda value_lines: (
                locator + value_lines
                + ["call instance void %s::Set(%s, %s)" % (array_il, args, element_il)]
            )
        return capture, load, store

    def _expr_UserFunc(self, node):
        # FN call: push the arguments, call the function method, value left on stack.
        for actual in node.actualParameters or []:
            self.lower_expression(actual)
        return_type, params = self._signatures.get(node.name, ("int32", []))
        self.emit("call %s %s(%s)"
                  % (return_type, _method_name(node.name), ", ".join(params)))

    def _expr_ReadFunc(self, node):
        # Read the next DATA item (a string) and convert it to the target type.
        self.emit("ldsfld %s %s" % (_DATA_ARRAY_TYPE, _DATA_FIELD))
        self.emit("ldsfld int32 %s" % _DATA_INDEX_FIELD)
        self.emit("ldc.i4.1")
        self.emit("add")
        self.emit("dup")
        self.emit("stsfld int32 %s" % _DATA_INDEX_FIELD)
        self.emit("ldelem.ref")
        target = node.actualType
        if isinstance(target, StringOwlType):
            return
        # READ of a numeric uses BBC's VAL semantics (leading numeric part, 0 if
        # none) rather than a strict Parse, so empty DATA items (between adjacent
        # commas) and trailing whitespace yield 0 instead of throwing.
        self.emit(_runtime("Val", "string"))
        if not isinstance(target, FloatOwlType):  # integer / byte
            self.emit("conv.i4")

    # -- string operations --------------------------------------------------

    def _expr_Concatenate(self, node):
        self.lower_expression(node.lhs)
        self.lower_expression(node.rhs)
        self.emit("call string [System.Runtime]System.String::Concat(string, string)")

    def _expr_LenFunc(self, node):
        self.lower_expression(node.factor)
        self.emit("call instance int32 [System.Runtime]System.String::get_Length()")

    def _expr_AscFunc(self, node):
        self.lower_expression(node.factor)
        self.emit(_runtime("Asc", "string"))

    def _expr_ValFunc(self, node):
        self.lower_expression(node.factor)
        self.emit(_runtime("Val", "string"))

    def _expr_ChrStrFunc(self, node):
        self.lower_expression(node.factor)
        self.emit(_runtime("Chr", "int32"))

    def _expr_PointFunc(self, node):
        # POINT(x, y): the logical colour at a graphics coordinate. The runtime
        # method is a stub that raises at run time (reading the screen back is
        # not yet implemented), so a program using POINT compiles but does not
        # run -- rather than failing to compile at all.
        self.lower_expression(node.xCoord)
        self.lower_expression(node.yCoord)
        self.emit(_runtime("Point", "int32", "int32"))

    def _expr_InstrFunc(self, node):
        self.lower_expression(node.source)
        self.lower_expression(node.subString)
        if node.startPosition is not None:
            self.lower_expression(node.startPosition)
            self.emit(_runtime("InstrAt", "string", "string", "int32"))
        else:
            self.emit(_runtime("Instr", "string", "string"))

    def _expr_LeftStrFunc(self, node):
        self.lower_expression(node.source)
        if node.length is not None:
            self.lower_expression(node.length)
            self.emit(_runtime("LeftStr", "string", "int32"))
        else:
            self.emit(_runtime("LeftStr", "string"))

    def _expr_RightStrFunc(self, node):
        self.lower_expression(node.source)
        if node.length is not None:
            self.lower_expression(node.length)
            self.emit(_runtime("RightStr", "string", "int32"))
        else:
            self.emit(_runtime("RightStr", "string"))

    def _expr_MidStrFunc(self, node):
        self.lower_expression(node.source)
        self.lower_expression(node.position)
        if node.length is not None:
            self.lower_expression(node.length)
            self.emit(_runtime("MidStr", "string", "int32", "int32"))
        else:
            self.emit(_runtime("MidStr", "string", "int32"))

    # -- simple numeric / boolean functions ---------------------------------

    def _expr_TrueFunc(self, node):
        self.emit("ldc.i4.m1")    # BBC TRUE is -1

    def _expr_FalseFunc(self, node):
        self.emit("ldc.i4.0")

    def _expr_Not(self, node):
        self.lower_expression(node.factor)
        self.emit("not")          # bitwise complement (BBC NOT)

    def _expr_AbsFunc(self, node):
        self.lower_expression(node.factor)
        il = _il_type(node.factor.actualType)
        self.emit("call %s %s::Abs(%s)" % (il, _MATH, il))

    def _expr_SgnFunc(self, node):
        self.lower_expression(node.factor)
        self.emit("call int32 %s::Sign(%s)"
                  % (_MATH, _il_type(node.factor.actualType)))

    def _expr_SqrFunc(self, node):
        self.lower_expression(node.factor)
        self.emit(_runtime("Sqr", "float64"))

    def _lower_factor_as_float(self, factor):
        """Lower *factor* and coerce an integer result to float64."""
        self.lower_expression(factor)
        if not isinstance(factor.actualType, FloatOwlType):
            self.emit("conv.r8")

    def _expr_PiFunc(self, node):
        self.emit("ldc.r8 " + _PI)

    def _expr_RadFunc(self, node):
        # RAD: degrees -> radians, x * PI / 180 (left-to-right, as BBC computes).
        self._lower_factor_as_float(node.factor)
        self.emit("ldc.r8 " + _PI)
        self.emit("mul")
        self.emit("ldc.r8 180.0")
        self.emit("div")

    def _expr_DegFunc(self, node):
        # DEG: radians -> degrees, x * 180 / PI.
        self._lower_factor_as_float(node.factor)
        self.emit("ldc.r8 180.0")
        self.emit("mul")
        self.emit("ldc.r8 " + _PI)
        self.emit("div")

    def _expr_RndFunc(self, node):
        if node.option is not None:
            self.lower_expression(node.option)
            self.emit(_runtime("Rnd", "int32"))
        else:
            self.emit(_runtime("Rnd"))

    def _expr_PosFunc(self, node):
        self.emit(_runtime("Pos"))

    def _expr_VposFunc(self, node):
        self.emit(_runtime("VPos"))

    def _expr_LomemValue(self, node):
        self.emit(_runtime("get_Lomem"))

    def _expr_GetFunc(self, node):
        # GET: read one keypress, returning its code.
        self.emit(_runtime("Get"))

    def _expr_IntFunc(self, node):
        # INT: floor to an integer (the factor is a real after type checking).
        self.lower_expression(node.factor)
        self.emit("call float64 %s::Floor(float64)" % _MATH)
        self.emit("conv.ovf.i4")

    def _expr_TimeValue(self, node):
        # TIME: the elapsed centisecond clock.
        self.emit(_runtime("get_Time"))

    def _expr_StrStringFunc(self, node):
        # STR$: format a number as PRINT would. (STR$~ hex base not yet handled.)
        if getattr(node, "base", 10) != 10:
            raise CodeGenerationError("STR$ with a non-decimal base is not supported yet")
        self.lower_expression(node.factor)
        if not isinstance(getattr(node.factor, "actualType", None), FloatOwlType):
            self.emit("conv.r8")          # StrString takes a float64
        self.emit(_runtime("StrString", "float64"))

    def _expr_UnaryMinus(self, node):
        self.lower_expression(node.factor)
        self.emit("neg")

    def _expr_UnaryPlus(self, node):
        self.lower_expression(node.factor)

    def _expr_Cast(self, node):
        # Numeric coercions the type checker inserts (e.g. integer -> float for
        # mixed arithmetic, or assigning an integer to a real variable).
        self.lower_expression(node.value)
        target = node.targetType
        if isinstance(target, FloatOwlType):
            self.emit("conv.r8")
        elif isinstance(target, LongIntegerOwlType):
            # Widen to 64 bits (e.g. an int32 operand in a %% expression).
            self.emit("conv.i8")
        elif isinstance(target, (IntegerOwlType, ByteOwlType, AddressOwlType)):
            # Addresses and bytes are int32-sized on the CIL stack. Narrowing a
            # 64-bit value to 32 bits is checked by the CLR's own conv.ovf.i4
            # (near-free on the in-range path); the OverflowException it raises
            # is converted once, at the program boundary, into BBC error 20
            # ("Number too big"). Float->int stays a plain (truncating)
            # conversion, matching BBC INT semantics.
            if isinstance(getattr(node, "sourceType", None), LongIntegerOwlType):
                self.emit("conv.ovf.i4")
            else:
                self.emit("conv.i4")
        else:
            raise CodeGenerationError(
                "Cannot lower cast to %r" % type(target).__name__
            )

    # -- runtime call selection --------------------------------------------

    def _print_call(self, item):
        owl_type = getattr(item, "actualType", None)
        if isinstance(owl_type, StringOwlType):
            arg = "string"
        elif isinstance(owl_type, LongIntegerOwlType):
            arg = "int64"
        elif isinstance(owl_type, (IntegerOwlType, ByteOwlType)):
            arg = "int32"
        elif isinstance(owl_type, FloatOwlType):
            arg = "float64"
        elif isinstance(owl_type, SumOwlType):
            # A union: the value arrives already boxed (the function returns
            # object). Print(object) tag-dispatches on its runtime type.
            arg = "object"
        else:
            # Fall back to the static node shape when the type is unresolved.
            arg = _arg_from_node(item)
        return _runtime("Print", arg)


def _arg_from_node(node):
    name = type(node).__name__
    if name == "LiteralString":
        return "string"
    if name == "LiteralFloat":
        return "float64"
    # Integers and integer arithmetic.
    return "int32"


_ESCAPES = {"\\": "\\\\", '"': '\\"', "\n": "\\n", "\r": "\\r", "\t": "\\t"}


def _il_string(value):
    """Render a Python string as an ILAsm string literal."""
    out = []
    for ch in value:
        if ch in _ESCAPES:
            out.append(_ESCAPES[ch])
        elif 32 <= ord(ch) < 127:
            out.append(ch)
        else:
            out.append("\\%03o" % ord(ch))  # ILAsm octal escape
    return '"' + "".join(out) + '"'
