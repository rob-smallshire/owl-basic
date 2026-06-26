# Statically compiling EVAL

## What EVAL supports today

A quick reference to what the EVAL lowering currently compiles, and what it
still rejects. The rest of this document is the design and rationale behind it;
the authoritative, executable specification is `tests/test_eval_static.py` (with
the constant evaluator pinned in `tests/test_constant_evaluator.py` and the
runtime hex/`VAL` semantics in `OwlRuntime/OwlRuntime.Tests/`). If this table
and the tests ever disagree, the tests win -- update this table.

### Compiles

| Construct | Compiles to | Example | Tests (`tests/test_eval_static.py`) |
|---|---|---|---|
| Constant arithmetic | folded literal | `EVAL("1+2")` → `3` | `test_eval_constant_arithmetic_runs`, `test_eval_constant_string_leaves_no_eval_node` |
| Pure function of constants | folded literal | `EVAL("SIN(RAD(30))")` → `0.5` | `test_eval_constant_function_folds_and_runs` |
| Constant string by concatenation | folded literal | `EVAL("2"+"+"+"3")` → `5` | `test_eval_constant_string_concatenation_runs` |
| Constant skeleton naming runtime variables | spliced expression (vars read at run time) | `EVAL("a%*2-1")` | `test_constant_skeleton_with_runtime_variable_runs` |
| Nested EVAL | recursively lowered | `EVAL("EVAL(""1+2"")")` → `3` | `test_nested_eval_runs` |
| Digit-slice idiom | `VAL(...)` | `EVAL(MID$("13264",K,1))` | `test_digit_idiom_runs_correctly`, `test_eval_of_left_str_digits_runs` |
| Hex-to-int idiom | runtime hex parse (`EvalHex`) | `EVAL("&"+h$)` | `test_hex_idiom_runs`, `test_hex_idiom_lowers_to_evalhex_not_eval` |
| `STR$` value-hole | each `STR$(e)` → `VAL(STR$(e))`, spliced | `EVAL(STR$(n)+"+1")` | `test_str_template_runs`, `test_str_template_lowers_to_val_of_str` |
| Function-by-name dispatch | `IF`-chain helper over the program's `DEF FN`s | `EVAL("FN"+cmd$+"(arg)")` | `test_dispatch_with_named_argument_runs`, `test_dispatch_with_chr34_string_value_hole_runs`, `test_dispatch_with_staged_literal_argument_runs`, `test_dispatch_reads_local_argument_dynamically` |
| Constant *variable* (via propagation) | propagated to its literal, then lowered as above | `f$="user1+area" : EVAL(f$)` | `tests/test_eval_constant_propagation.py` |
| Constant argument unblocking a dispatch (via propagation) | the constant argument becomes a literal, so the runtime-name dispatch applies | `p$="7" : EVAL("FN"+c$+"("+p$+")")` | `tests/test_eval_constant_propagation.py` |
| Constant set up in one routine, EVAL'd in another (via inter-procedural propagation) | the cross-method constant is propagated, then lowered as above | `DEFPROCsetup … f$="user1+area" … DEFPROCuse … =EVAL(f$)` | `test_cross_method_constant_string_eval_runs` |

The last three are not EVAL features: constant propagation runs *before* EVAL
lowering (see `docs/constant-propagation.md`), so a scalar that holds a single
constant is already a literal by the time EVAL is lowered. The propagation is
inter-procedural -- a constant assigned in one PROC and EVAL'd in another is
connected through the call graph, provided the setup routine is always called
before the use (the Acorn User `ImageP` "user formula" program is this
cross-method shape, and its `EVAL`s now lower). The residual rejections below are
for values that really are unknown until run time.

Two run-time behaviours that are *correct compilation*, not rejection:

- A dispatch on a **name no `DEF FN` matches** compiles, and faults `No such
  FN/PROC` at run time exactly as the interpreter's EVAL does
  (`test_dispatch_unknown_name_faults_at_runtime`).
- The hex idiom faults **`Bad hex`** at run time on a missing/invalid leading
  digit, e.g. `EVAL("&ff")` (`test_hex_idiom_bad_hex_faults_at_runtime`).

### Rejected (the honest residual)

Each is rejected at compile time naming EVAL -- never a crash or silent
mis-compile.

| Construct | Why | Example | Test |
|---|---|---|---|
| Open structure / referents | needs a run-time evaluator (Category 6) | `EVAL(A$)`, `A$` not constant | `test_eval_of_runtime_string_still_rejected` |
| Malformed constant string | not a valid BASIC expression | `EVAL("1+")` | `test_eval_of_malformed_constant_string_is_rejected_naming_it` |
| Slice of a non-digit string | `EVAL` ≠ `VAL` in general | `EVAL(MID$(A$,1,1))` | `test_eval_of_slice_of_non_digit_string_still_rejected` |
| Runtime argument *structure* | selecting the callee is not enough; the arg is itself general EVAL | `EVAL("FN"+cmd$+"("+arg$+")")` | `test_dispatch_runtime_argument_structure_is_rejected` |
| Runtime structure after a hex string | structure beyond the hex run is runtime | `EVAL("&"+h$+"+1")` | `test_hex_with_runtime_trailing_structure_stays_rejected` |
| Variable-by-name / reflective write | `RETURN` (by-reference) argument selected by a string | `EVAL("FNassign2("+a$+","+CHR$34+b$+CHR$34+")")` | `test_variable_by_name_reflective_write_stays_rejected` |

Each of these is rejected only when the operand is *genuinely* run-time. A scalar
that holds a single constant is propagated to its literal first, so `EVAL(A$)`,
`EVAL(MID$(A$,1,1))` or the runtime-argument dispatch all compile when the
variable is constant -- the residual rejection is for values that really are
unknown until run time (`INPUT`, `READ`, a reassigned variable, memory).

A `STR$` value-hole that *lexically fuses* with adjacent text stays rejected
(e.g. `EVAL(STR$(n)+"0")` would read `"50"`, not the `STR$`-formatted number):
`test_str_template_lexical_merge_stays_rejected`.

## Why this exists

`EVAL` takes a string and evaluates it as a BASIC expression at run time. The
easy reaction is "a static compiler can't do that" -- and OWL has, until now,
rejected every program using `EVAL` with that justification.

That reaction is wrong, or at least far too broad. `EVAL` only forces a run-time
evaluator when the *structure* of the evaluated expression, or the *set of
program entities (variables, functions) it can refer to*, is not statically
determinable. A large and common class of `EVAL` uses are statically
determinable, and for those `EVAL` compiles to ordinary code.

This document describes how, and lays out the increments.

## The core model: EVAL is partial evaluation of a parsed template

A reducible `EVAL` string is a *function literal in disguise*. Compiling it has
two halves:

- the **static skeleton becomes code** (an expression, spliced in place), and
- the **runtime parts become its inputs**.

Concretely, `EVAL(STR$(n%) + "+1")` has the skeleton `_ + 1` with one runtime
value hole. It compiles to exactly `n% + 1` -- the `STR$ -> EVAL` round-trip is
identity on the value, the hole `n%` is the input. The string is gone; what
remains is ordinary code applied to ordinary values.

So the compilability test is crisp:

> **EVAL is compilable exactly when its function body can be written down at
> compile time.** Free variables and value holes are always fine -- they are
> inputs. What cannot be an input is the *body itself*.

### Two kinds of "referent", both just inputs

- **Value holes** -- spliced in via `STR$`/`MID$`/concatenation. Passed as
  arguments (captured by value at the `EVAL` site).
- **Named free variables** -- names appearing *in* the skeleton text, e.g. `a%`
  in `EVAL("a%*2-1")`. Read directly from their backing storage at the `EVAL`
  site.

### Three mechanisms, by what is runtime

1. **Body fixed, referents are inputs** -> splice an expression (or, where holes
   need naming, a synthesized function). Categories 0-3 below.
2. **Body fixed except a choice of callee/operator from a statically known set**
   -> a *dispatch* (a `CASE` over the known set selected by the runtime string).
   Categories 4-5. This is "select code by value", not "pass a value" -- a
   different mechanism, even though the candidate set is fully static.
3. **Body itself is runtime** -> no static function exists; needs an embedded
   run-time expression evaluator. Category 6. Out of scope; stays rejected.

## The compilability spectrum

| # | Example | What unlocks it | Compiles to |
|---|---------|-----------------|-------------|
| 0 | `EVAL("1+2")` | constant operand | `3` (fold) |
| 1 | `EVAL("a%*2-1")` | constant skeleton, known var | `a%*2-1` |
| 2 | `EVAL(STR$(n%)+"+1")`, `EVAL(MID$("13264",K,1))` | static skeleton, value holes | `n%+1`; `VAL(MID$(...))` |
| 3 | `EVAL("FN"+"area")` | constant-foldable name | `FNarea` |
| 4 | `EVAL(op$+"(t)")`, `op$` in `{"FNsin","FNsind"}` | name from bounded finite set | `CASE op$ ... ` |
| 5 | `EVAL("FN"+cmd$+"(arg)")` | callee from the program's known `DEF FN`s | dispatch over all `DEF FN`s |
| 6 | `INPUT e$ : PRINT EVAL(e$)` | nothing -- structure & referents open | (rejected: needs run-time evaluator) |

The interesting boundary is **5 vs 6**: in 5 we cannot predict *which* function,
but we can enumerate *every function it could be* (the compiler knows all
`DEF FN`s), so a static dispatch suffices. In 6 the referent set is unbounded.

## Foundation: a general constant-expression evaluator

The single most important realisation: **EVAL constant-folding is not an EVAL
feature.** `EVAL("SIN(RAD(30))")` should fold to `0.5` for exactly the same
reason that `SIN(RAD(30))` *written literally* should. So the foundation is a
reusable constant evaluator, valuable in its own right (it improves every
program, not just `EVAL` users).

**Status: built and broad** -- `owl_basic.constant_folding.fold_constant`. It is
recursive (`SIN(RAD(30))` folds because `RAD(30)` folds, then `SIN` of that) and
covers everything pure:

- arithmetic `+ - * / ^`, unary `+`/`-`;
- integer `DIV`/`MOD`, bitwise `AND OR EOR NOT`, and the shifts `<< >> >>>`
  (integer operands only, so BBC's float->int coercion is never second-guessed;
  `>>` arithmetic, `>>>` logical, with an out-of-range count shifting everything
  out as in BBC BASIC V on ARM -- emulator-checked, not CIL's modulo masking --
  and the folded value kept equal to the runtime helpers);
- the relational operators (numeric operands -> BBC `-1`/`0`);
- `PI TRUE FALSE`;
- `ABS INT SGN` and the transcendentals `SIN COS TAN ASN ACS ATN RAD DEG SQR EXP
  LN LOG`;
- string functions over constant strings: `CHR$ LEN ASC LEFT$ RIGHT$ MID$
  STRING$ INSTR VAL`, each mirroring its OwlRuntime implementation op-for-op.

Impure functions (`RND GET INKEY TIME`, file/screen I/O, `READ`, user functions,
...) are never folded. `STR$` is excluded too: it formats per the runtime `@%`
variable (see the STR$ discussion above). Each folded form is spliced in by the
type checker's `_foldConstant` before codegen, so the optimisation reaches the
emitted IL.

`EVAL` then rides on it; so does ordinary code. The existing integer-only
`_foldConstant` becomes a thin caller of this evaluator.

### Folding must be host-side, and the fidelity question splits cleanly

The folder evaluates constant subtrees **in the host** (interpret the AST in
Python). It must *not* fold by compiling a snippet to target code and executing
it: that would require a runnable target and break cross-compilation (compiling
on a host that cannot run the target). Re-running the *front end* (`parse`) on
an `EVAL` string is fine -- that is host-side and produces an AST; only
*executing target code* is disallowed.

With host-side evaluation, fidelity versus the run-time splits in two:

- **Exact under IEEE-754** -- integer arithmetic, float `+ - * /`, and `SQR`
  (correctly-rounded is mandated). Host (CPython float64) and .NET produce
  bit-identical results, **provided the folder mirrors the target's exact
  operation order and types**. This is a real discipline: CPython's
  `math.radians(x)` computes `x*(pi/180)` while OWL lowers `RAD` as `x*PI/180`
  -- a different last ULP -- so the folder must replicate the target's formula
  op-by-op, never call the host library's near-equivalent. No cross-compile
  issue here, just faithful replication.
- **Library transcendentals** -- `SIN COS TAN ASN ACS ATN EXP LN LOG` and `^`
  (`pow`). Not correctly-rounded-mandated, so host libm and .NET `System.Math`
  may differ by ~1 ULP. This is the *only* place where bit-exact folding would
  require running on the target, and thus the only place cross-compilation
  constrains us.

Resolution: host-side evaluation is the portable default. Transcendentals fold
via host libm (accepting the ~1-ULP gap, masked anyway by BBC's ~9-sig-fig
`PRINT`); a bit-exact mode that runs them on the target is **optional**, gated on
the target being executable (host==target or an emulator), and simply falls back
to host libm -- or to not folding transcendentals -- when cross-compiling to a
target that cannot be run. Folding is never *predicated* on executing target
code.

### Future direction: Python as a compiler target

The general version of host-side folding is to make Python a *target language* of
the compiler, then fold by compiling the constant subtree to Python and running
it on the host. That reuses the compiler's own semantics (one source of truth for
how every construct behaves) instead of a second, hand-written evaluator that can
drift -- and Python always runs on the host, so it stays cross-compile-safe. It
is, however, a whole backend. For now we build a small AST evaluator over
representative subtrees; the Python-backend route is the principled generalisation
if the evaluator grows unwieldy or its fidelity to the real semantics becomes hard
to maintain.

## The EVAL lowering pass

A new pass (after parse + simplify, before type-check -- it produces ordinary
AST that type-check and codegen then handle) walks for `EvalFunc` nodes and, for
each:

1. **Fold the operand.** Run the constant evaluator over `EvalFunc.factor`.
   - **Constant string** -> re-invoke `parse()` on it, splice the resulting
     expression AST in place of the `EvalFunc`. The folder then reduces it (so
     `EVAL("1+2")` -> `3`). *No function is emitted for the constant case.*
   - **Not constant** -> attempt template reduction (below).
2. **Template reduction.** Reduce the operand to a static skeleton string with
   holes (`STR$(e)` -> a numeric hole bound to `e`; `MID$(lit,...)` over a
   digit-only literal -> a numeric hole; literal concatenation -> skeleton
   text). Parse the skeleton, substitute the holes' sub-expressions for their
   placeholders. Splice inline, or lift into a synthesized `DEF FN` whose
   parameters are the holes (the lambda-lifted form).

   *Implemented so far -- the digit idiom:* a `MID$`/`LEFT$`/`RIGHT$` slice of a
   digit-only literal always yields a plain decimal numeral, so `EVAL` of it is
   `EVAL == VAL`; it lowers to `VAL` of the same argument. No placeholder
   machinery and no float-precision concern (digits are exact).

   *The `STR$` concatenation template -- compilable, but only with the round-trip
   kept.* It is tempting to reduce `EVAL(STR$(e)+"+1")` to `e+1`, treating
   `STR$(e)` as a numeric hole. That cancellation is **unsound**: `STR$` formats
   its argument according to the runtime `@%` format variable (the same control
   `PRINT` uses), so `STR$(e)` is *not* a lossless representation of `e`. Even at
   the default `@%` it is ~10 significant figures in general format, so
   `STR$(12345678901)` is `"1.23456789E10"` and `EVAL` reads back `12345678900`;
   and `@%` can be set to anything at run time. Substituting the exact expression
   `e` would therefore give a *different* value from what `EVAL` computes. Making
   the cancellation sound would need static `@%` tracking plus value-range
   analysis -- narrow and fragile.

   But the cancellation is the only unsound part. **Keeping** the round-trip is
   exact: `EVAL(STR$(e) + "+1") == VAL(STR$(e)) + 1`, because `EVAL`'s parser reads
   from `STR$(e)` exactly the numeric literal that `VAL` reads -- the same trick
   the digit idiom uses (wrap the hole in `VAL`), for the same reason. This holds
   for any `@%` and needs no range analysis. It does require that `VAL` and the
   expression parser agree on numeric syntax; OWL's `VAL` used to stop at an `E`
   exponent (a bug -- BBC `VAL` scans the same number grammar as the rest of the
   interpreter, so `VAL("1E3")=1000`), which is now fixed, so `VAL(STR$(n))`
   round-trips. The sound `STR$` value-hole (reducing to `VAL(STR$(e))`, not `e`)
   is **implemented** -- `eval_lowering._lower_str_template` reduces each `STR$(e)`
   hole to `VAL(STR$(e))` and splices the reparsed skeleton; a hole that lexically
   fuses with adjacent text stays residue. The digit idiom does not go through
   `STR$` at all (it slices a fixed literal: no formatting, no `@%`), so it stays exact
   regardless.
3. **Dispatch.** If the residual is statically a function call (its skeleton
   begins with the literal `"FN"`) with a runtime name and already-staged
   arguments, generate a `CASE` dispatch over the program's `DEF FN`s of
   compatible signature, `OTHERWISE` a run-time "no such function" fault.
4. **Otherwise reject** -- with the honest "needs a run-time evaluator OWL does
   not provide" message. Only Category 6 reaches here.

### Recursion gives nested EVAL for free

`parse()` builds a fresh lexer per call and the parser is stateless across
calls, so the lowering pass can re-invoke the whole front end on the `EVAL`
string. Parsing `EVAL("EVAL(""1+2"")")`'s operand yields *another* `EvalFunc`,
which the same pass re-enters -> `1+2` -> `3`. Nested `EVAL` is not a special
case; it is the recursion closing.

## LOCAL / dynamic scoping is correct for free

`EVAL` resolves its free variables in the *dynamic* scope live where it runs: an
`EVAL` inside a `PROC` that declared `LOCAL a%` sees the local `a%`.

OWL already implements `LOCAL`/`PRIVATE` as save-on-entry / restore-on-exit of
the *same* backing global field (dynamic scoping). So during the procedure body
that field *holds* the local value, and a compiled `EVAL`-expression that reads
it picks up the local value automatically -- no closure capture, no environment
threading. The dynamic-scoping implementation and `EVAL`'s dynamic name
resolution are the same mechanism.

Rule for the lowering: **value holes become parameters** (fresh synthetic
names); **named free-variable referents read the ambient backing field** (which
is already LOCAL-correct). A lifted helper is invoked synchronously at the
`EVAL` site, so even one reused from several sites sees each caller's locals.

## Soundness boundaries (what stays rejected)

- The **arguments must be staged**, or you recurse. `EVAL("FN"+cmd$+"(arg)")` is
  clean (callee runtime, args staged). `EVAL("FN"+cmd$+"("+argexpr$+")")` with a
  runtime *argument structure* is not -- selecting the function is not enough,
  you would have to evaluate `argexpr$`, which is general `EVAL` again.
- **Dispatch requires compatible signatures.** A `CASE` over `DEF FN`s assumes
  the candidates share the arity/return type at the use site. Real dispatch
  tables do; the compiler must *check* rather than assume, and reject (or
  per-arm coerce) where they diverge.
- **Runtime operators / unbounded variable sets** (`EVAL(x$+op$+y$)`,
  `EVAL(name$)` selecting an arbitrary variable) are analogous dispatch
  primitives keyed off weaker static evidence. Not in the initial scope; the
  `"FN"`-prefix dispatch is the one that shows up in real programs.
- **Category 6** -- structure or referent set genuinely open -> rejected.

## Increments (TDD)

1. **Constant folder** (task #6) -- DONE. General `fold_constant(node)` in
   `owl_basic/constant_folding.py`; folds pure functions of constants and
   int+float arithmetic, so `SIN(RAD(30))` reduces whether or not `EVAL` is
   involved. The type-checker's `_foldConstant` is re-based on it.
2. **Constant-string EVAL** (task #7) -- DONE. The lowering pass
   `owl_basic/eval_lowering.py` parses + splices + folds: `EVAL("1+2")`,
   `EVAL("SIN(RAD(30))")`, nested `EVAL`.
3. **Value-hole digit idiom** (task #8) -- DONE. `EVAL(MID$(digit-literal,...))`
   -> `VAL(...)`. The `STR$` concatenation template was investigated and dropped
   as unsound (`STR$` formats per the runtime `@%` variable; see above).
4. **Function-by-name dispatch** (task #9) -- DONE. `EVAL("FN"+cmd$+"(arg)")` and
   the `CHR$34 + s$ + CHR$34` string-value hole. `eval_lowering._lower_dispatch`
   reduces the operand to a skeleton + holes, recovers the call, and appends a
   synthesised helper `FN_eval_dispatch_N` invoked in place of the `EVAL`. Notes:
   - The helper dispatches with an **IF-chain, not a `CASE`**: the .NET backend
     lowers `IF` but not `CASE`. Each arm `IF name$="x" THEN =FNx(...)` returns
     when the runtime name matches; falling past all arms raises
     `NoSuchFnProcException` -- the interpreter's "No such FN/PROC" fault.
   - **Value holes become parameters** (string-typed -- `CHR$34` wraps strings);
     **named free-variable arguments are left verbatim** and read the ambient
     backing field (LOCAL-correct -- the helper is called synchronously).
   - `fold_constant` learned `CHR$` so `CHR$34` folds to `"` for hole detection.
   - Signature match is by arity + per-argument sigil vs each DEF FN's formals; a
     RETURN (by-reference) formal disqualifies a candidate (reflective write, out
     of scope). No compatible DEF FN is a clear rejection; a runtime *argument
     structure* or a compound argument expression stays the honest residual.
5. **Hex-to-int idiom** -- DONE. `EVAL("&" + h$)` reads a runtime hex string;
   `VAL` is decimal-only, so this is the only conversion for it. (In the ROM, `VAL`
   runs the decimal literal reader `parse_number`, while `EVAL` runs the full
   expression evaluator whose factor dispatcher `eval_factor` alone routes `&` to
   `factor_hex` -- which is exactly why `VAL` cannot do this and `EVAL` can.)
   `eval_lowering._lower_hex` rewrites the operand `"&"` + one runtime string into
   `EvalHexFunc`, lowered to the new `OwlRuntime.BasicCommands.EvalHex`, which
   reads the maximal `[0-9A-F]` run (uppercase only, like `factor_hex`), tolerates
   trailing non-hex (`EVAL("&FG")` = 15), and faults **"Bad hex" (error 28)** when
   no leading hex digit is read (`EVAL("&ff")`, `EVAL("&")`). It folds into a
   32-bit signed pattern for up to 8 digits (`&FFFFFFFF` = -1); OWL deliberately
   supersets the ROM to 64 bits for 9-16 digits (the ROM wraps to the low 32),
   matching OWL's own hex-literal lexer. A trailing runtime *structure* (`"&" +
   h$ + "+1"`) stays the honest residual. The constant form `EVAL("&FF")` already
   folds via the constant-string path. `VAL` itself was also fixed to scan `E`
   exponents (it had stopped at the `E`), so `VAL`/`STR$`/the expression parser
   agree -- which is what makes the `STR$` value-hole (next increment) sound.
6. **`STR$` value-hole** -- DONE. `EVAL(STR$(e) + ...)` reduces each `STR$(e)`
   hole to `VAL(STR$(e))` -- keeping the round-trip, not cancelling it to `e`
   (which is unsound: `STR$` formats per `@%`). `eval_lowering._lower_str_template`
   reparses the literal text as a skeleton with a placeholder per hole, swaps in
   `VAL(STR$(e))`, and splices it. Sound for any `@%` (`VAL(STR$(e))` reproduces
   exactly what `EVAL` reads, now that `VAL` scans exponents) and any position
   (OWL's unary minus binds tighter than every binary operator, so a leading sign
   groups as a unit). A hole that lexically fuses with adjacent text
   (`EVAL(STR$(n)+"0")`) or a non-`STR$` hole stays the honest residual.

Each increment keeps every prior corpus program compiling-or-gracefully-rejected
and ends green. Category 6 keeps the honest rejection throughout.

## Increment #9 in detail: function-by-name dispatch

### Target

An `EVAL` whose argument is statically a *function call* -- its template begins
with the literal `"FN"` -- with a runtime function *name* and already-staged
arguments:

```basic
result = EVAL("FN" + cmd$ + "(arg)")         REM cmd$ runtime, arg an ambient var
y = EVAL("FN" + op$ + "(" + CHR$34 + s$ + CHR$34 + ")")   REM string-value arg
```

Unlike #6-#8 this cannot splice an expression, because the choice of callee is a
*runtime value selecting code*, and a dispatch is a statement. So #9
**synthesises a function**: enumerate the program's `DEF FN`s, and replace the
`EVAL` with a call to a generated helper whose body dispatches on the runtime
name string to the matching `FN`, `OTHERWISE` faulting at run time exactly as the
interpreter's `EVAL` would on an unknown name.

The dispatch is shown below as a `CASE` for clarity, but it is realised as an
`IF`-chain: the .NET backend lowers `IF`, not `CASE`. And `arg` is *not* passed
-- it is a named free-variable referent (literal text in the skeleton), so by the
dynamic-scoping rule above it reads the ambient backing field; only value holes
become parameters. So the realised lowering of the first example is
`FN_eval_dispatch_N(cmd$)` with arms `= FNarea(arg)` reading ambient `arg`:

```basic
REM  EVAL("FN" + cmd$ + "(arg)")  lowers to  FN_eval_dispatch_N(cmd$)
DEF FN_eval_dispatch_N(name$)
  REM realised as: IF name$ = "area" THEN = FNarea(arg)  : etc.
  CASE name$ OF
    WHEN "area"  : = FNarea(arg)     REM arg read from the ambient field
    WHEN "perim" : = FNperim(arg)
    ... one arm per DEF FN of compatible signature ...
    OTHERWISE    : <raise NoSuchFnProcException -- the "No such FN/PROC" fault>
  ENDCASE
```

A *value-hole* argument (the `CHR$34 + s$ + CHR$34` form) *does* become a
parameter: `EVAL("FN" + op$ + "(" + CHR$34 + s$ + CHR$34 + ")")` lowers to
`FN_eval_dispatch_N(op$, s$)` with arms `= FNsize(s$)`.

### Template reduction this needs

#9 needs the literal-parts + holes reduction deferred from #8 (it was the `STR$`
hole that was unsound, not the machinery). Reduce the `EVAL` argument to:

- a **skeleton** string (literal text verbatim) with placeholder identifiers
  where holes go, and
- a **hole map** placeholder -> the runtime sub-expression.

Sound hole kinds:

- `CHR$34 + e$ + CHR$34` (or `CHR$(34)`) -- a **string-value hole**: EVAL parses
  the quoted literal back to `e$`, so it reduces to `e$`. Sound *only when `e$`
  contains no `"`* (an embedded quote unbalances the literal -- the static form
  must either prove no quote or leave it as residue).
- a bare numeric value spliced as a number -- but note the only sound numeric
  string-builder is *not* `STR$` (see the `@%` discussion); a numeric hole has to
  come from something exact. In practice the common case is the function *name*
  and string args, so numeric-arg holes can wait.

Then: parse `"FN" + skeleton + ...` as a function call to recover (name-hole,
arg-holes). The `"FN"` literal prefix is the static evidence that licenses the
dispatch; the name hole is what `CASE` switches on; the arg holes become the
helper's value parameters.

### Substitution is AST-level (precedence-safe)

Placeholders parse as ordinary variable references; substituting the hole's AST
subtree for the placeholder node preserves precedence automatically (the AST is
already structured -- no string-flattening reparenthesisation hazard). Choose
placeholder names that lex as plain identifiers and do not start with a keyword
(e.g. avoid an `EVAL...` prefix); collisions are harmless since the node is
replaced immediately.

### Soundness constraints

- **Arguments must be staged.** `EVAL("FN"+cmd$+"(arg)")` is clean. `EVAL("FN" +
  cmd$ + "(" + argexpr$ + ")")` with a runtime *argument structure* is residue --
  selecting the function is not enough; evaluating `argexpr$` is general `EVAL`.
- **Signature match.** The `CASE` assumes the candidate `DEF FN`s share the
  arity/return type at the use site. Check it; reject (or per-arm coerce) where
  candidates diverge rather than emit a call that will not type.
- **LOCAL / dynamic scope** is automatic (see above): the helper reads ambient
  globals; `RETURN`/reference args are *not* in scope (see the frontier below).

### Explicitly out of scope: variable-by-name and reflective writes

Distinct from callee-by-name. Consider (a real idiom):

```basic
DEF PROCassign(a$, b$)
  unused = EVAL("FNassign2(" + a$ + "," + CHR$34 + b$ + CHR$34 + ")")
ENDPROC
DEF FNassign2(RETURN a$, b$)   : a$ = b$ : = 0
```

Here the callee `FNassign2` is *constant*; the runtime thing is an **argument
that is an l-value selected by the string `a$`**, passed by `RETURN` (reference).
This is the reflective-*write* counterpart of read-by-name. It is compilable in
principle -- dispatch over the program's statically-known string variables, each
arm passing one by reference -- but it is a bigger hammer (a `CASE` over
*variables*, with reference semantics), so it is a separate later frontier, not
part of #9. #9 handles the function *name* being runtime, with value arguments.
