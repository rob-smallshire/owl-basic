"""Static lowering of EVAL whose argument is statically known.

Constant-string EVAL: when EVAL's argument folds to a constant string, that
string is a BASIC expression known at compile time. Re-parse it and splice the
resulting expression in place of the EVAL; downstream constant folding then
reduces it -- EVAL("1+2") -> 3, EVAL("SIN(RAD(30))") -> 0.5. Nested EVAL falls
out by re-lowering: parsing EVAL("EVAL(""1+2"")") yields another EvalFunc, which
the next pass over the tree lowers in turn.

An EVAL whose argument is not statically a constant string is left in place for
later increments (value-hole templates, function-by-name dispatch) or, failing
those, the honest "needs a run-time evaluator" rejection.

See docs/eval-static-compilation.md.
"""
import itertools
import re

from owl_basic.constant_folding import fold_constant
from owl_basic.exceptions import CompileError
from owl_basic.parent_visitor import ParentVisitor
from owl_basic.syntax import parser as syntax_parser
from owl_basic.syntax import grammar as _grammar
from owl_basic.syntax.ast import (ActualArgList, Concatenate, EvalHexFunc,
                                  LiteralString, Raise, UserFunc, ValFunc,
                                  Variable)


def lower_eval(parse_tree, options, helper_serial=None):
    """Lower every statically determinable EVAL in *parse_tree*.

    Three mechanisms, by what is runtime (see docs/eval-static-compilation.md):

    * a *constant-string* EVAL is re-parsed and spliced in place (its skeleton is
      code, there are no inputs);
    * the *digit idiom* (EVAL of a slice of a digit-only literal) becomes VAL;
    * a *function-by-name dispatch* -- EVAL of a call whose skeleton begins with
      the literal ``"FN"`` with a runtime name and staged value arguments -- is
      replaced by a call to a synthesised helper that dispatches on the runtime
      name string over the program's DEF FNs of compatible signature.

    Iterates to a fixpoint so a nested EVAL exposed by lowering an outer one is
    lowered too. Parent references on the spliced subtrees are re-established as we
    go, so a freshly exposed inner EVAL can itself be spliced.
    """
    # A shared serial can be passed so a second lowering pass (after constant
    # propagation) keeps numbering helpers where the first left off, rather than
    # colliding on FN_eval_dispatch_0.
    if helper_serial is None:
        helper_serial = itertools.count()
    while _lower_once(parse_tree, options, helper_serial):
        pass
    return helper_serial


def _lower_once(parse_tree, options, helper_serial):
    progressed = False
    for eval_node in _collect_evals(parse_tree):
        source = _constant_string(eval_node.factor)
        if source is not None:
            # Constant-string EVAL: re-parse the string and splice it.
            expression = _parse_expression(source, eval_node.lineNum, options)
            _splice(eval_node, expression)
            progressed = True
        elif _is_provably_decimal_string(eval_node.factor):
            # Digit idiom: EVAL of a string provably containing only decimal
            # digits (a slice of a digit-only literal) is EVAL == VAL. Rewrite to
            # VAL of the same argument -- no run-time evaluator needed.
            _splice(eval_node, ValFunc(factor=eval_node.factor))
            progressed = True
        elif _lower_hex(eval_node):
            # Hex-to-int idiom EVAL("&" + h$): rewrite to a runtime hex parse.
            progressed = True
        elif _lower_dispatch(eval_node, parse_tree, options, helper_serial):
            # Function-by-name dispatch: replaced by a call to a synthesised
            # helper appended to the program (see _lower_dispatch).
            progressed = True
        elif _lower_str_template(eval_node, options):
            # STR$ value-hole: EVAL(STR$(e)+...) -> the spliced expression with
            # each STR$(e) reduced to VAL(STR$(e)) (see _lower_str_template).
            progressed = True
        # Anything else stays an EvalFunc for _reject_unsupported_constructs to
        # reject honestly -- only Category 6 (open structure/referents) reaches it.
    return progressed


def _collect_evals(parse_tree):
    found = []

    def visit(node):
        if node is None:
            return
        if type(node).__name__ == "EvalFunc":
            found.append(node)
        node.forEachChild(visit)

    visit(parse_tree)
    return found


def _constant_string(node):
    value = fold_constant(node)
    return value if isinstance(value, str) else None


def _is_provably_decimal_string(node):
    """Whether *node* always yields a string of decimal digits at run time.

    A slice (MID$/LEFT$/RIGHT$) of a digit-only string literal is such a string,
    whatever the runtime index: every character is a digit, so EVAL of it parses
    the same plain numeral that VAL does. (A constant digit string is handled by
    the constant-string path instead.)
    """
    name = type(node).__name__
    if name in ("MidStrFunc", "LeftStrFunc", "RightStrFunc"):
        return _is_digit_literal(node.source)
    return False


def _is_digit_literal(node):
    return (type(node).__name__ == "LiteralString"
            and len(node.value) > 0 and node.value.isdigit())


def _parse_expression(source, line_num, options):
    """Parse *source* as a BASIC expression node, or raise naming the bad EVAL."""
    del _grammar.syntax_errors[:]
    tree = syntax_parser.parse("X=" + source + "\n", options)
    if _grammar.syntax_errors or tree is None:
        raise CompileError(
            "EVAL at line %d evaluates the string %r, which is not a valid BASIC "
            "expression." % (line_num, source))
    found = []

    def visit(node):
        if node is None:
            return
        if type(node).__name__ == "ScalarAssignment":
            found.append(node.rValue)
        node.forEachChild(visit)

    visit(tree)
    if not found:
        raise CompileError(
            "EVAL at line %d evaluates the string %r, which is not a BASIC "
            "expression." % (line_num, source))
    return found[0]


def _splice(eval_node, expression):
    """Replace *eval_node* with *expression* in the tree, fixing up references."""
    expression.parent = eval_node.parent
    expression.parent_property = eval_node.parent_property
    expression.parent_index = eval_node.parent_index
    eval_node.parent.setProperty(
        expression, eval_node.parent_property, eval_node.parent_index)
    _set_line_num(expression, eval_node.lineNum)
    # Parent the spliced subtree's own descendants so a nested EVAL inside it can
    # be spliced on the next pass; expression.parent itself is set above.
    expression.accept(ParentVisitor())


def _set_line_num(node, line_num):
    node.lineNum = line_num
    node.forEachChild(lambda child: _set_line_num(child, line_num) if child else None)


# --- function-by-name dispatch -------------------------------------------
# EVAL("FN" + cmd$ + "(arg)") selects a function by a runtime name from a set the
# compiler can fully enumerate -- every DEF FN in the program. That is not "pass
# a value" but "select code by value", so it lowers not to a spliced expression
# but to a synthesised helper that CASEs (here, an IF-chain the backend supports)
# on the runtime name over the DEF FNs of compatible signature. See the "Increment
# #9 in detail" section of docs/eval-static-compilation.md.

_STRING_CONCAT = ("Plus", "Concatenate")


_HEX_DIGITS = frozenset("0123456789ABCDEFabcdef")


def _lower_hex(eval_node):
    """Lower the hex-to-int idiom EVAL("&" + h$ ...), or return False to leave it.

    EVAL of "&" followed by a runtime string is BBC's standard hex-to-integer
    conversion -- VAL is decimal-only, so this is the only way to read a hex
    string. (In the ROM, VAL runs the decimal literal reader, while EVAL runs the
    full expression evaluator, whose factor dispatcher alone handles the "&" hex
    reader -- which is exactly why VAL cannot do this and EVAL can.)

    The operand must be "&" followed by a hex string built from runtime holes and
    constant *hex-digit* text, in any combination: EVAL("&"+h$), EVAL("&0"+h$)
    (constant digits after the &), EVAL("&"+a$+b$) (several runtime parts). It
    lowers to EvalHexFunc over the concatenated content, which at run time reads
    the leading hex run as a &-literal does and faults "Bad hex" on a
    missing/invalid leading digit, as EVAL does. Constant text that is not all hex
    digits (e.g. "&"+h$+"+1") is structure -- general EVAL again -- so it stays
    residue. At least one hole is required; an all-constant operand is left to
    constant folding.
    """
    segments = _string_segments(eval_node.factor)
    if not segments:
        return False
    first_kind, first_value = segments[0]
    if first_kind != "lit" or not first_value.startswith("&"):
        return False

    # Collect the hex content after the leading "&": constant runs must be hex
    # digits; runtime holes are taken as hex (the documented approximation -- the
    # run-time reader stops at the first non-hex character).
    def _literal(text):
        node = LiteralString(value=text)
        _set_line_num(node, eval_node.lineNum)
        return node

    content = []
    head = first_value[1:]
    if head:
        if any(character not in _HEX_DIGITS for character in head):
            return False
        content.append(_literal(head))
    has_hole = False
    for kind, value in segments[1:]:
        if kind == "lit":
            if any(character not in _HEX_DIGITS for character in value):
                return False
            content.append(_literal(value))
        else:
            has_hole = True
            content.append(value)
    if not has_hole:
        return False                 # all constant: leave to constant folding

    factor = content[0]
    for node in content[1:]:
        factor = Concatenate(lhs=factor, rhs=node)
        _set_line_num(factor, eval_node.lineNum)
    _splice(eval_node, EvalHexFunc(factor=factor))
    return True


def _lower_str_template(eval_node, options):
    """Lower a STR$ value-hole template EVAL(STR$(e) + ...), or return False.

    Every runtime part must be a STR$(e): EVAL parses the formatted number back,
    and VAL(STR$(e)) reproduces exactly that number (VAL and the expression
    parser agree on numeric syntax since the VAL exponent fix), so STR$(e)
    reduces soundly to VAL(STR$(e)) -- keeping the round-trip rather than
    cancelling it to e (which would be unsound: STR$ formats per @%). The literal
    text is reparsed as the skeleton of an expression with a placeholder per
    hole; a placeholder that does not survive parsing as a recoverable identifier
    (it fused with adjacent text, e.g. STR$(n)+"0" or STR$(n)+"E2") leaves the
    EVAL as residue, since EVAL would then read a different number.

    Precedence is safe in any position: OWL's unary minus binds tighter than
    every binary operator, so a leading sign in STR$'s output groups as a unit,
    exactly as VAL(STR$(e)) collapses it.
    """
    segments = _string_segments(eval_node.factor)
    if segments is None:
        return False
    holes = [payload for kind, payload in segments if kind == "hole"]
    if not holes or any(type(h).__name__ != "StrStringFunc" for h in holes):
        return False

    pieces = []
    mapping = {}        # placeholder identifier -> the STR$ subtree
    for kind, payload in segments:
        if kind == "lit":
            pieces.append(payload)
        else:
            placeholder = "owlstrhole%d" % len(mapping)
            mapping[placeholder] = payload
            pieces.append(placeholder)

    expression = _parse_skeleton("".join(pieces), options)
    if expression is None:
        return False
    substituted = set()
    expression = _replace_str_placeholders(expression, mapping, substituted)
    if substituted != set(mapping):     # a hole fused with adjacent text: residue
        return False
    _splice(eval_node, expression)
    return True


def _replace_str_placeholders(node, mapping, substituted):
    """Replace each placeholder Variable with VAL(STR$(e)); return the new node."""
    if node is None:
        return None
    if type(node).__name__ == "Variable" and node.identifier in mapping:
        substituted.add(node.identifier)
        return ValFunc(factor=mapping[node.identifier])
    for key, child in list(node.children.items()):
        if isinstance(child, list):
            for index, sub in enumerate(child):
                replacement = _replace_str_placeholders(sub, mapping, substituted)
                if replacement is not sub:
                    child[index] = replacement
        else:
            replacement = _replace_str_placeholders(child, mapping, substituted)
            if replacement is not child:
                node._children[key] = replacement
    return node


def _lower_dispatch(eval_node, parse_tree, options, helper_serial):
    """Lower a function-by-name-dispatch EVAL, or return False to leave it.

    Returns True (and replaces *eval_node* with a call to a freshly appended
    helper) when the EVAL argument is statically a function call whose name is a
    runtime string and whose arguments are staged; otherwise returns False so the
    EVAL stays for the honest residual rejection. Raises CompileError only when
    the construct *is* a by-name dispatch but no DEF FN can serve it.
    """
    segments = _string_segments(eval_node.factor)
    if segments is None or not any(kind == "hole" for kind, _ in segments):
        return False
    skeleton, holes = _skeleton(segments)
    call = _parse_skeleton(skeleton, options)
    if call is None or type(call).__name__ != "UserFunc":
        return False    # the skeleton is not statically a function call: residue

    # The "FN" literal prefix names the dispatch: the callee is "FN", an optional
    # fixed prefix, then one bare hole that is the runtime name (a suffix). So
    # EVAL("FN"+n$) has an empty prefix, and EVAL("FNpart"+n$) has prefix "part"
    # selecting among FNpart0, FNpart1, ... The fixed prefix is folded into the
    # runtime name below, reducing both to the same dispatch.
    name_hole = None
    name_prefix = ""
    for hole in holes:
        if (hole["kind"] == "bare" and call.name.startswith("FN")
                and call.name.endswith(hole["placeholder"])
                and len(call.name) > len(hole["placeholder"]) + 1):
            name_hole = hole
            name_prefix = call.name[len("FN"):len(call.name) - len(hole["placeholder"])]
            break
    if name_hole is None:
        return False
    # A bare hole anywhere else is a runtime *argument structure* (general EVAL
    # again): selecting the function is not enough, you would have to evaluate it.
    if any(h["kind"] == "bare" and h is not name_hole for h in holes):
        return False
    value_holes = [h for h in holes if h["kind"] == "value"]

    # The argument template: the skeleton beyond the callee name, with each value
    # hole rewritten to its (string) helper parameter. Named free variables are
    # left verbatim and read the ambient backing field -- LOCAL-correct, since the
    # helper is invoked synchronously at the EVAL site (doc: dynamic scoping).
    rest = skeleton[len(call.name):]
    param_names = []
    for index, hole in enumerate(value_holes):
        hole["param"] = "owlarg%d$" % index
        param_names.append(hole["param"])
        rest = re.sub(r"\b%s\b" % re.escape(hole["placeholder"]), hole["param"], rest)

    arg_sigils = _argument_sigils(call.actualParameters, value_holes)
    if arg_sigils is None:
        return False    # a compound argument expression: cannot match signatures

    candidates = _dispatch_candidates(parse_tree, arg_sigils)
    if not candidates:
        raise CompileError(
            "EVAL at line %d dispatches on a runtime function name, but the program "
            "has no DEF FN with a matching signature (%s) to dispatch to." % (
                eval_node.lineNum,
                "%d argument(s): %s" % (len(arg_sigils),
                                        ", ".join(s or "<real>" for s in arg_sigils))
                if arg_sigils else "no arguments"))

    helper_name = "FN_eval_dispatch_%d" % next(helper_serial)
    for statement in _build_helper(helper_name, param_names, rest, candidates,
                                   eval_node.lineNum, options):
        parse_tree.statements.append(statement)

    # The EVAL becomes a synchronous call to the helper: the runtime name first,
    # then each staged value argument (captured by value at the EVAL site).
    arguments = ActualArgList()
    # The helper matches owlname$ against each candidate's full name (minus "FN"),
    # so a fixed prefix is prepended to the runtime suffix here: EVAL("FNpart"+n$)
    # passes "part"+n$, which matches candidate FNpart<n>.
    name_argument = name_hole["node"]
    if name_prefix:
        literal = LiteralString(value=name_prefix)
        _set_line_num(literal, eval_node.lineNum)
        name_argument = Concatenate(lhs=literal, rhs=name_argument)
        _set_line_num(name_argument, eval_node.lineNum)
    arguments.append(name_argument)
    for hole in value_holes:
        arguments.append(hole["node"])
    _splice(eval_node, UserFunc(name=helper_name, actualParameters=arguments))
    return True


def _flatten_concat(node):
    """The left-to-right leaf operands of a string-concatenation tree."""
    if type(node).__name__ in _STRING_CONCAT:
        return _flatten_concat(node.lhs) + _flatten_concat(node.rhs)
    return [node]


def _string_segments(node):
    """Reduce a concatenation tree to literal-text and runtime-hole segments.

    Each segment is ``("lit", text)`` for a part that folds to a constant string
    or ``("hole", subtree)`` for a runtime part. Returns None if any part folds to
    a non-string constant -- then it is not a string template at all.
    """
    segments = []
    for part in _flatten_concat(node):
        value = fold_constant(part)
        if value is None:
            segments.append(("hole", part))
        elif isinstance(value, str):
            if segments and segments[-1][0] == "lit":
                segments[-1] = ("lit", segments[-1][1] + value)
            else:
                segments.append(("lit", value))
        else:
            return None     # a numeric constant spliced as text: not our template
    return segments


def _skeleton(segments):
    """Build the skeleton string and classify each hole.

    A hole flanked by ``"`` characters in the skeleton is a string-VALUE hole
    (the ``CHR$34 + e$ + CHR$34`` idiom): EVAL parses the quoted literal straight
    back to ``e$``, so it reduces to ``e$`` passed by value. The flanking quotes
    are dropped so the placeholder lexes as the bare argument identifier it
    becomes. (This is exact for any quote-free ``e$`` -- the only sound case the
    doc admits; an embedded ``"`` would unbalance the literal and make the real
    EVAL fault, where passing by value instead delivers the whole string. We
    accept that divergence on the pathological input rather than reject the idiom
    its quote-free uses depend on.) Every other hole is BARE -- the callee name,
    or (in argument position) a runtime argument structure that the caller rejects
    as residue.

    Placeholders lex as plain identifiers and do not begin with a keyword, so
    substituting them is precedence-safe; collisions are harmless as the parse is
    used only to recover structure.
    """
    holes = []
    pieces = []
    for index, (kind, payload) in enumerate(segments):
        if kind == "lit":
            pieces.append(payload)
            continue
        before = segments[index - 1][1] if index > 0 and segments[index - 1][0] == "lit" else ""
        after = segments[index + 1][1] if index + 1 < len(segments) and segments[index + 1][0] == "lit" else ""
        quoted = before.endswith('"') and after.startswith('"')
        placeholder = "owlhole%d" % len(holes)
        holes.append({"placeholder": placeholder, "node": payload,
                      "kind": "value" if quoted else "bare"})
        pieces.append(placeholder)
    skeleton = "".join(pieces)
    for hole in holes:
        if hole["kind"] == "value":
            skeleton = skeleton.replace('"%s"' % hole["placeholder"],
                                        hole["placeholder"], 1)
    return skeleton, holes


def _parse_skeleton(source, options):
    """Parse the skeleton as an expression, or None if it does not parse."""
    del _grammar.syntax_errors[:]
    tree = syntax_parser.parse("X=" + source + "\n", options)
    if _grammar.syntax_errors or tree is None:
        return None
    found = []

    def visit(node):
        if node is None:
            return
        if type(node).__name__ == "ScalarAssignment":
            found.append(node.rValue)
        node.forEachChild(visit)

    visit(tree)
    return found[0] if found else None


def _sigil(identifier):
    """The BBC type suffix of *identifier* ("" for a real)."""
    if identifier.endswith("%%"):
        return "%%"
    if identifier and identifier[-1] in "$%&~":
        return identifier[-1]
    return ""


def _argument_sigils(actual_arg_list, value_holes):
    """The per-argument type sigils of the recovered call, or None if undecidable.

    A value hole is a string (it came through ``CHR$34``); a named free-variable
    argument takes its identifier's sigil; a staged literal takes its own type. A
    compound argument expression has no single static sigil, so signatures cannot
    be matched soundly -- return None.
    """
    value_placeholders = {hole["placeholder"] for hole in value_holes}
    sigils = []
    arguments = actual_arg_list.arguments if actual_arg_list is not None else []
    for arg in arguments:
        kind = type(arg).__name__
        if kind == "Variable":
            sigils.append("$" if arg.identifier in value_placeholders
                          else _sigil(arg.identifier))
        elif kind == "LiteralString":
            sigils.append("$")
        elif kind in ("LiteralInteger", "LiteralFloat"):
            sigils.append("")       # a numeric literal binds to a real parameter
        else:
            return None             # a compound argument expression: undecidable
    return sigils


def _dispatch_candidates(parse_tree, arg_sigils):
    """Every DEF FN whose formal-parameter signature matches *arg_sigils*."""
    candidates = []

    def visit(node):
        if node is None:
            return
        if type(node).__name__ == "DefineFunction" and _formal_sigils(node) == arg_sigils:
            candidates.append(node)
        node.forEachChild(visit)

    visit(parse_tree)
    return candidates


def _formal_sigils(define_function):
    """The formal-parameter sigils of a DEF FN, or None if it cannot be a target.

    A RETURN (by-reference) parameter is reflective-write territory, out of scope
    for #9, so such a function is never a dispatch candidate.
    """
    formal_list = define_function.formalParameters
    sigils = []
    arguments = formal_list.arguments if formal_list is not None else []
    for formal in arguments:
        if type(formal).__name__ != "FormalArgument":
            return None
        variable = formal.argument
        if type(variable).__name__ != "Variable":
            return None
        sigils.append(_sigil(variable.identifier))
    return sigils


def _build_helper(helper_name, param_names, rest, candidates, line_num, options):
    """Synthesise the dispatch helper's statements (DEF FN, IF arms, fault).

    The body is an IF-chain (the backend lowers IF, not CASE): one arm per
    candidate returns ``FN<name>`` applied to the same argument template, guarded
    by the runtime name. Falling past every arm raises "No such FN/PROC" -- the
    same fault the interpreter's EVAL raises on an unknown name.
    """
    params = ",".join(["owlname$"] + param_names)
    lines = ["DEF %s(%s)" % (helper_name, params)]
    for candidate in candidates:
        runtime_name = candidate.name[2:]      # the name string minus the "FN"
        lines.append('IF owlname$="%s" THEN =%s%s'
                     % (runtime_name, candidate.name, rest))
    helper_source = "\n".join(lines) + "\n"

    del _grammar.syntax_errors[:]
    helper_tree = syntax_parser.parse(helper_source, options)
    if _grammar.syntax_errors or helper_tree is None:
        raise CompileError(
            "EVAL at line %d: could not synthesise a dispatch helper from %r."
            % (line_num, helper_source))

    statements = list(helper_tree.statements.statements)
    statements.append(Raise(type="NoSuchFnProcException",
                            argument=Variable(identifier="owlname$")))
    for statement in statements:
        _set_line_num(statement, line_num)
    return statements
