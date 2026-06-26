# Constant propagation

## Why

Several front-end capabilities want to see a *literal* where the source wrote a
*variable* that only ever holds one constant value:

- **EVAL** of a constant-string variable: `f$="user1+area" … EVAL(f$)`. The EVAL
  lowering (`docs/eval-static-compilation.md`) already compiles a constant-string
  EVAL by re-parsing it; it just needs `f$` to *be* the string `"user1+area"`.
- `DIM` sizes, `FOR` limits, and other places where a constant in a variable
  could feed constant folding or static checks.

The point of constant propagation is to make this a *general* capability rather
than an EVAL special case: replace each read of a provably-constant scalar with
its literal, and every downstream pass benefits unchanged.

It also feeds the **function-by-name dispatch** path (`_lower_dispatch` in
`eval_lowering.py`). That path already compiles `EVAL("FN" + name + "(args)")`
for a runtime `name` over the program's DEF FNs, but rejects the EVAL when an
*argument* is a runtime structure rather than a literal:

| EVAL | Today |
|---|---|
| `EVAL("FN"+c$+"(1,2)")` (literal args) | compiles |
| `EVAL("FN"+c$+"("+p$+")")`, with `p$="7"` | rejected |

The second is rejected only because `p$` is not known to be constant; propagate
it and the EVAL becomes the first form, which compiles. So the dispatch's
"runtime argument structure" wall is partly an artefact of not knowing which
"runtime" parts are actually constant. (Two related gaps are *not* propagation: a
`STR$(e)` value-hole argument should reuse the `STR$(e)->VAL(STR$(e))` reduction
the value-hole path already has, and resolving an array-element *name* like
`sorts$(sort)` needs array-constant propagation.)

## The trap: a conservative no-dataflow rule is unsound

The tempting cheap rule — *"a scalar with exactly one assignment, whose RHS is a
constant and which is not written anywhere else, is that constant"* — is **not
sound**, because "assigned once" does not imply "the assignment reaches every
read". A read can execute *before* the single assignment.

The repository's own RUN test (`test_dotnet_emitter.py::
test_run_clears_variables_and_restarts`) is exactly this case:

```basic
10 PRINT n%      : REM n% is 0 here -- read before it is assigned
20 n% = 42
30 INPUT cmd$
40 IF cmd$ = "q" THEN END
50 RUN           : REM restart at line 10, with variables cleared
```

`n%` has one constant assignment (`n%=42`, not conditional), so the cheap rule
would rewrite the line-10 read to `42` — but `n%` is genuinely `0` at line 10,
both on the first pass and after `RUN`. Constant propagation must not change that
output.

Source-line order cannot rescue the rule, either: in the motivating EVAL program
(`Tau90-b/AUG90.ImageP`) the constant string is assigned at line 2500 (in a setup
PROC) and read at line 1910, so "definition precedes use textually" is false for
a perfectly valid case.

So there is no sound constant-propagation rule that avoids dataflow.

## The sound design (reaching definitions)

A read of variable `V` may be replaced by constant `C` **iff every definition of
`V` that reaches that read assigns the same constant `C`** (and there is at least
one — `V` is not live-on-entry with an unknown value at the read).

This is the classic *reaching-definitions* / sparse-conditional-constant analysis
over the control-flow graph:

1. Build the CFG (OWL already does — `createForwardControlFlowGraph`, and the
   per-method graphs after subroutine conversion).
2. For each variable, compute the set of definitions reaching each use. A
   definition is any write — `isLValue` marks them all (`ScalarAssignment`,
   `FOR`, `INPUT`/`READ`, `+=`, `LOCAL`, formal parameters).
3. A use is a *constant use* when all reaching definitions are assignments of the
   same foldable constant. Replace it with that literal (reusing the leaf-swap
   substitution: find the slot via `parent.findChild`, `setProperty` the
   literal). Iterate to a fixpoint so chains (`a=5 : b=a`) resolve.

### Pipeline placement

The CFG is built *after* `eval_lowering` runs (`analysis._run_pipeline`). So a
sound propagation that also feeds EVAL must either:

- run after the forward CFG is built, then **re-run `eval_lowering`** on the
  (now literal-bearing) tree — `eval_lowering` operates on the AST and can run
  again, but the splices it makes must be re-reflected into the CFG; or
- be expressed as a CFG-aware analysis whose results `eval_lowering` consults,
  rather than a tree rewrite before it.

The cleanest option is to compute reaching-definition constants once the forward
CFG exists, substitute, and re-run the AST-level rewrites (`eval_lowering`, then
re-parent / re-flow) — accepting one extra flow rebuild. This is the work item;
the substitution machinery itself is trivial (it is the leaf swap above).

### Scope and limits

- Scalars only. Array elements and indirection cells are not propagated.
- `@%` and the resident integers (`A%`–`Z%`) are global, lifecycle-preserved
  state; treat their definitions like any other (they are ordinary writes).
- A definition inside a routine reaches a use only along call paths; the
  intraprocedural CFG plus the PROC-call edges OWL already models cover this, but
  a first cut may restrict to within-routine reaching definitions and leave
  cross-PROC constants for later.

## Status

**Implemented** in `src/owl_basic/constant_propagation.py`
(`tests/test_constant_propagation.py`, `tests/test_eval_constant_propagation.py`).
The shipped pass uses the *uniform-constant + definite-assignment* form rather
than full reaching definitions: a scalar is a candidate only when every write of
it is a `ScalarAssignment` of the same folded constant, and the per-method
"must be defined" dataflow (entry IN forced empty) then propagates it to the uses
it dominates. `%%`/`&` scalars and `@%` are skipped (width/narrowing/print-format
subtleties); substitution is iterated to a fixpoint for chains. General reaching
definitions (mixing different constants, cross-PROC) remains the future
generalisation.

Pipeline: the pass runs after `orderBasicBlocks`; `eval_lowering` then runs a
second time so EVAL benefits (`analysis._build_flow` is re-run only when a
newly-enabled dispatch appends helper statements). The folder also reads the
shift width from the operand's type, and was hardened so `-"string"` /
`ABS("string")` fold to "not constant" rather than crashing. See
`docs/eval-static-compilation.md` for the EVAL consumer.
