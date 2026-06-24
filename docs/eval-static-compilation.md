# Statically compiling EVAL

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
reason that `SIN(RAD(30))` *written literally* should -- and today OWL folds
neither. `_foldConstant` only folds `+ - *` of two *integer* literals.

So the foundation is a reusable constant evaluator, valuable in its own right
(it improves every program, not just `EVAL` users):

- `fold(node) -> Python value | None` -- returns the constant value of a subtree
  when it is a pure function of constants, else `None`.
- Arithmetic over **int and float** literals: `+ - * / ^ DIV MOD`, unary `-`.
- Pure built-in functions of constant arguments: `SIN COS TAN ASN ACS ATN RAD
  DEG SQR EXP LN LOG ABS INT SGN PI` (and the string ones: `LEN ASC CHR$ STR$
  MID$ LEFT$ RIGHT$ VAL` over constant strings -- needed for template
  reduction).
- Recursive: `SIN(RAD(30))` folds because `RAD(30)` folds to `0.523...` then
  `SIN(0.523...)` folds to `0.5`.

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

1. **Constant folder** (task #6). General `fold(node)`; fold pure functions of
   constants, int+float arithmetic. Folds `SIN(RAD(30))` whether or not `EVAL`
   is involved. Re-base `_foldConstant` on it.
2. **Constant-string EVAL** (task #7). Parse + splice + fold. `EVAL("1+2")`,
   `EVAL("SIN(RAD(30))")`, nested `EVAL`.
3. **Value-hole templates** (task #8). `EVAL(STR$(n%)+"+1")`, the digit idiom.
4. **Function-by-name dispatch** (task #9). `EVAL("FN"+cmd$+"(arg)")`.

Each increment keeps every prior corpus program compiling-or-gracefully-rejected
and ends green. Category 6 keeps the honest rejection throughout.
