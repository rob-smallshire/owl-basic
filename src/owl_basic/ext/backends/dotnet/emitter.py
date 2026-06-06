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

from owl_basic.exceptions import OwlBasicError
from owl_basic.owltyping.type_system import (
    AddressOwlType,
    ByteOwlType,
    FloatOwlType,
    IntegerOwlType,
    StringOwlType,
)
from owl_basic.symbol_tables import SymbolInfo

# Symbol modifiers that mean the variable is stored in a method (not globally).
_METHOD_SCOPED_MODIFIERS = frozenset(
    {SymbolInfo.modifier_arg, SymbolInfo.modifier_ref_arg,
     SymbolInfo.modifier_local, SymbolInfo.modifier_private}
)

# A curated slice of the OwlRuntime "signature manifest": the textual CIL
# signatures of the BasicCommands methods we call. This will be generated from
# OwlRuntime.dll (via monodis / reflection) rather than hand-listed; for now the
# handful we emit are spelled out. See BasicCommands in the OwlRuntime project.
_RUNTIME = "[OwlRuntime]OwlRuntime.BasicCommands"

_PRINT_NEWLINE = "call void {0}::NewLine()".format(_RUNTIME)

# OwlRuntime models BBC BASIC's address space as a byte array for ? indirection.
_MEMORY_ARRAY = "call uint8[] [OwlRuntime]OwlRuntime.MemoryMap::get_Memory()"

_BYTE_INDIRECTIONS = frozenset({"UnaryByteIndirection", "DyadicByteIndirection"})

# DATA is compiled to a static string array read sequentially by READ.
_DATA_FIELD = "__data"
_DATA_ARRAY_TYPE = "string[]"
_DATA_INDEX_FIELD = "__dataIndex"

# Map a textual CIL operator mnemonic onto each binary arithmetic AST node.
_BINARY_OPS = {
    "Plus": "add",
    "Minus": "sub",
    "Multiply": "mul",
    "Divide": "div",
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


class CodeGenerationError(OwlBasicError):
    """Raised when the emitter meets an AST node it cannot yet lower."""


# Map an OwlType onto the CIL type used for a local / runtime argument. Order
# matters: ChannelOwlType is an IntegerOwlType, ByteOwlType is distinct.
_IL_TYPES = [
    (StringOwlType, "string"),
    (FloatOwlType, "float64"),
    (ByteOwlType, "int32"),
    (IntegerOwlType, "int32"),
]


def _il_type(owl_type):
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
    blocks_by_entry = program.ordered_basic_blocks or {}
    signatures = _collect_proc_signatures(blocks_by_entry)
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
    prologue = _data_init_lines(data_items) if data_items else None
    methods = [
        _emit_method(
            entry_name, blocks, signatures, globals_registry, data_index,
            prologue if entry_name == _MAIN_ENTRY else None,
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
    return _ASSEMBLY_TEMPLATE.format(
        name=assembly_name, fields=fields, methods="\n\n".join(methods)
    )


def _formal_arguments(define_procedure):
    """Yield the formal parameter Variables of a ``DEFPROC``, in order."""
    parameters = define_procedure.formalParameters
    if parameters is None:
        return []
    return [formal.argument for formal in parameters.arguments]


def _collect_proc_signatures(blocks_by_entry):
    """Map each PROC name to its CIL parameter types, so calls can be typed."""
    signatures = {}
    for entry_name, blocks in blocks_by_entry.items():
        if entry_name == _MAIN_ENTRY or not blocks:
            continue
        define = blocks[0].statements[0]
        if type(define).__name__ == "DefineProcedure":
            signatures[entry_name] = [
                _il_type(argument.actualType)
                for argument in _formal_arguments(define)
            ]
    return signatures


def _emit_method(entry_name, blocks, signatures, globals_registry, data_index,
                 prologue=None):
    """Render one routine's basic blocks as a complete CIL method."""
    is_main = entry_name == _MAIN_ENTRY
    if not is_main and not entry_name.startswith("PROC"):
        # FN methods (return values) and GOSUB subroutines come later.
        raise CodeGenerationError("Cannot yet emit a method for %r" % entry_name)

    # A PROC's formal parameters become method arguments (ldarg/starg); every
    # other variable is a local.
    formal_args = {}
    parameters = []
    if not is_main and blocks and type(blocks[0].statements[0]).__name__ == "DefineProcedure":
        for index, argument in enumerate(_formal_arguments(blocks[0].statements[0])):
            formal_args[argument.identifier] = index
            parameters.append("%s A%d" % (_il_type(argument.actualType), index))

    emitter = _MethodEmitter(
        formal_args=formal_args,
        proc_signatures=signatures,
        globals_registry=globals_registry,
        data_index=data_index,
    )
    emitter.lower_blocks(blocks)
    emitter.finish()
    if prologue:
        # Runs before the first block (e.g. building the DATA array in Main).
        emitter.lines = list(prologue) + emitter.lines
    # Guarantee the method returns: add a trailing `ret` unless the last block
    # already ends in one (END / ENDPROC), which avoids an unreachable duplicate.
    if not emitter.lines or emitter.lines[-1] != "ret":
        emitter.emit("ret")

    name = "Main" if is_main else _method_name(entry_name)
    entrypoint = "    .entrypoint\n" if is_main else ""
    body = "\n".join("        " + line for line in emitter.lines)
    return _METHOD_TEMPLATE.format(
        name=name,
        signature=", ".join(parameters),
        entrypoint=entrypoint,
        locals=emitter.locals_declaration(),
        body=body,
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
.assembly extern OwlRuntime {{ }}
.assembly {name} {{ }}
.module {name}.dll

{fields}
{methods}
"""


_METHOD_TEMPLATE = """\
.method static void {name}({signature}) cil managed
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
    return "ldc.r8 0.0" if il_type == "float64" else "ldc.i4.0"


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
    def __init__(self, formal_args=None, proc_signatures=None,
                 globals_registry=None, data_index=None):
        self.lines = []
        self._local_slots = {}   # variable identifier -> local slot index
        self._local_types = []   # CIL type string, indexed by slot
        self._formal_args = formal_args or {}        # identifier -> arg index
        self._proc_signatures = proc_signatures or {}  # PROC name -> [il types]
        self._globals = globals_registry if globals_registry is not None else {}
        self._symbol_table = None  # the symbol table of the statement being lowered
        self._for_loops = {}       # id(ForToStep) -> loop state, shared with NEXT
        self._label_seq = 0        # for unique intra-method labels
        self._data_index = data_index or {}  # DATA line number -> data array index

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
                # Variable storage (arg / local / global) is resolved against
                # the symbol table of the statement being lowered.
                self._symbol_table = getattr(statement, "symbolTable", None)
                self.lower_statement(statement)
            self._emit_fall_through(block, index)

    def _variable_storage(self, variable):
        """Classify a variable reference as ('arg'|'local'|'global', locus).

        Formal parameters are method arguments; LOCAL/PRIVATE variables are
        method locals; everything else is a program-wide global static field
        (BBC BASIC variables are global by default).
        """
        identifier = variable.identifier
        if identifier in self._formal_args:
            return "arg", self._formal_args[identifier]
        symbol = self._symbol_table.lookup(identifier) if self._symbol_table else None
        modifier = getattr(symbol, "modifier", None)
        if modifier in _METHOD_SCOPED_MODIFIERS:
            return "local", self._local_slot(identifier, variable.actualType)
        field = _global_field_name(identifier)
        if field not in self._globals:
            self._globals[field] = _il_type(variable.actualType)
        return "global", field

    def _block_label(self, block):
        return "BB_%d" % self._block_index[id(block)]

    def _emit_fall_through(self, block, index):
        last = block.statements[-1] if block.statements else None
        if last is not None and type(last).__name__ in _BRANCHING_STATEMENTS:
            return  # the statement emitted its own control transfer
        successors = list(block.outEdges)
        if len(successors) == 1:
            successor = successors[0]
            if self._block_index.get(id(successor)) != index + 1:
                self.emit("br " + self._block_label(successor))

    def finish(self):
        # The assembly template appends the trailing `ret`; nothing to do yet.
        pass

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
            if type(item).__name__ == "FormatManipulator":
                last = index == len(items) - 1
                self._emit_print_manipulator(item)
                # A trailing ';' (or ',') suppresses PRINT's end-of-line newline.
                if last and item.manipulator in (";", ","):
                    suppress_newline = True
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
            self.emit("call void {0}::HexFormat()".format(_RUNTIME))
        elif manipulator == ",":
            self.emit("call void {0}::CompleteField()".format(_RUNTIME))
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
        if name != "Variable":
            # Indexed / pseudo-variable l-values come later.
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
        if not node.trueClause:
            # Empty THEN clause (e.g. IF c THEN ELSE ...): the true target is the
            # fall-through, which we can't yet distinguish from the false target.
            raise CodeGenerationError("IF with an empty THEN clause")
        true_statement = node.trueClause[0]
        false_targets = set(node.outEdges)
        false_targets.discard(true_statement)
        if len(false_targets) != 1:
            raise CodeGenerationError("IF with %d false targets" % len(false_targets))
        false_statement = next(iter(false_targets))

        this_index = self._block_index[id(node.block)]
        true_index = self._block_index[id(true_statement.block)]
        false_index = self._block_index[id(false_statement.block)]
        true_label = self._block_label(true_statement.block)
        false_label = self._block_label(false_statement.block)

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

    def _stmt_DefineProcedure(self, node):
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

    def _stmt_Data(self, node):
        # DATA is compiled to a static array (built in Main); no inline code.
        pass

    def _stmt_Restore(self, node):
        target = node.targetLogicalLine
        if target is None:
            index = 0                       # bare RESTORE: back to the first item
        elif type(target).__name__ == "LiteralInteger":
            # RESTORE <line>: the first DATA item on or after that line. Resolved
            # at compile time; a non-literal target would need a runtime map.
            index = self._resolve_restore(int(target.value))
        else:
            raise CodeGenerationError("RESTORE with a non-constant line")
        # The read index is pre-incremented, so point one before the target.
        self.emit("ldc.i4 %d" % (index - 1))
        self.emit("stsfld int32 %s" % _DATA_INDEX_FIELD)

    def _resolve_restore(self, line):
        if line in self._data_index:
            return self._data_index[line]
        at_or_after = [n for n in self._data_index if n >= line]
        if not at_or_after:
            raise CodeGenerationError(
                "RESTORE %d: no DATA at or after that line" % line
            )
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
        types = self._proc_signatures.get(node.name, [])
        self.emit("call void %s(%s)" % (_method_name(node.name), ", ".join(types)))

    def _stmt_ReturnFromProcedure(self, node):
        self.emit("ret")

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
            self._lower_relational(node, _RELATIONAL_OPS[name])
            return
        handler = getattr(self, "_expr_" + name, None)
        if handler is None:
            raise CodeGenerationError("Cannot lower expression node %r" % name)
        handler(node)

    def _lower_relational(self, node, opcodes):
        if isinstance(node.lhs.actualType, StringOwlType) or isinstance(
            node.rhs.actualType, StringOwlType
        ):
            # String comparison (String.Compare/Equals) comes later.
            raise CodeGenerationError("string comparison not yet lowered")
        self.lower_expression(node.lhs)
        self.lower_expression(node.rhs)
        for opcode in opcodes:
            self.emit(opcode)

    def _expr_LiteralString(self, node):
        self.emit("ldstr " + _il_string(node.value))

    def _expr_LiteralInteger(self, node):
        self.emit("ldc.i4 %d" % int(node.value))

    def _expr_LiteralFloat(self, node):
        self.emit("ldc.r8 %r" % float(node.value))

    def _load_variable(self, variable):
        kind, locus = self._variable_storage(variable)
        if kind == "arg":
            self.emit(_ldarg(locus))
        elif kind == "local":
            self.emit("ldloc V_%d" % locus)
        else:
            self.emit("ldsfld %s %s" % (self._globals[locus], locus))

    def _store_variable(self, variable):
        kind, locus = self._variable_storage(variable)
        if kind == "arg":
            self.emit("starg %d" % locus)
        elif kind == "local":
            self.emit("stloc V_%d" % locus)
        else:
            self.emit("stsfld %s %s" % (self._globals[locus], locus))

    def _expr_Variable(self, node):
        self._load_variable(node)

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
        if isinstance(target, FloatOwlType):
            self.emit("call float64 [System.Runtime]System.Double::Parse(string)")
        else:  # integer / byte
            self.emit("call int32 [System.Runtime]System.Int32::Parse(string)")

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
        self.emit("call int32 {0}::Asc(string)".format(_RUNTIME))

    def _expr_ChrStrFunc(self, node):
        self.lower_expression(node.factor)
        self.emit("call string {0}::Chr(int32)".format(_RUNTIME))

    def _expr_InstrFunc(self, node):
        self.lower_expression(node.source)
        self.lower_expression(node.subString)
        if node.startPosition is not None:
            self.lower_expression(node.startPosition)
            self.emit("call int32 {0}::InstrAt(string, string, int32)".format(_RUNTIME))
        else:
            self.emit("call int32 {0}::Instr(string, string)".format(_RUNTIME))

    def _expr_LeftStrFunc(self, node):
        self.lower_expression(node.source)
        if node.length is not None:
            self.lower_expression(node.length)
            self.emit("call string {0}::LeftStr(string, int32)".format(_RUNTIME))
        else:
            self.emit("call string {0}::LeftStr(string)".format(_RUNTIME))

    def _expr_RightStrFunc(self, node):
        self.lower_expression(node.source)
        if node.length is not None:
            self.lower_expression(node.length)
            self.emit("call string {0}::RightStr(string, int32)".format(_RUNTIME))
        else:
            self.emit("call string {0}::RightStr(string)".format(_RUNTIME))

    def _expr_MidStrFunc(self, node):
        self.lower_expression(node.source)
        self.lower_expression(node.position)
        if node.length is not None:
            self.lower_expression(node.length)
            self.emit(
                "call string {0}::MidStr(string, int32, int32)".format(_RUNTIME)
            )
        else:
            self.emit("call string {0}::MidStr(string, int32)".format(_RUNTIME))

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
        elif isinstance(target, (IntegerOwlType, ByteOwlType, AddressOwlType)):
            # Addresses and bytes are int32-sized on the CIL stack.
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
        elif isinstance(owl_type, (IntegerOwlType, ByteOwlType)):
            arg = "int32"
        elif isinstance(owl_type, FloatOwlType):
            arg = "float64"
        else:
            # Fall back to the static node shape when the type is unresolved.
            arg = _arg_from_node(item)
        return "call void {0}::Print({1})".format(_RUNTIME, arg)


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
