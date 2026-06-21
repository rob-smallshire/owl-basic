# `LOCAL` and `PRIVATE` semantics in OWL BASIC

This note records how OWL compiles `LOCAL` (and its `PRIVATE` sibling), how that
differs from the BBC BASIC interpreter, and why. It is intended to seed the
eventual user documentation; the behaviours here are pinned by
`tests/test_local_scope.py`.

## BBC BASIC: dynamic scoping

In BBC BASIC every variable is global. `LOCAL X` does not create a new variable —
it **saves** the current value of the global `X` onto a stack and gives `X` a
fresh value (0, or `""` for a string) for the duration of the enclosing
procedure or function. The matching `ENDPROC` / `=` **restores** the saved value.
A called routine therefore sees, and can modify, the caller's variables unless it
declares them `LOCAL` — this is *dynamic* scoping, not the lexical scoping of most
modern languages.

Two consequences matter:

* `LOCAL` takes effect **at the point the statement runs** (it is positional): a
  read of `X` *before* the `LOCAL X` in the same procedure sees the caller's
  value; a read after sees the fresh local.
* The save/restore is tied to the procedure's stack frame. Leaving a procedure by
  any route other than `ENDPROC`/`=` (a `GOTO` out of it, say) never restores the
  saved value — the frame **leaks** until control returns to the prompt.

## OWL's model: whole-function dynamic scoping

OWL keeps BBC's "every variable is a global" model — each variable is a single
static field. `LOCAL`/`PRIVATE` compile to a **save on entry / restore on exit**
around a procedure or function, generated once per routine:

* the routine's prologue saves each localised global into a temporary and resets
  it to its default;
* the routine's epilogue (`ENDPROC` / `=`) restores it.

The `LOCAL` *statement itself emits no code* — it only records, for the symbol
table and the prologue scan, that the named variables are localised by the
routine that contains it. Several `LOCAL`s accumulate, so `LOCAL A : LOCAL B` is
equivalent to `LOCAL A, B`.

### Attribution: which routine owns a `LOCAL`

A `LOCAL` is owned by every PROC/FN **frame** whose control can flow through it —
the frame whose `ENDPROC`/`=` would restore it. OWL computes this from the
control-flow graph (the routines that reach the statement). The main program is
**not** a frame: it has no `ENDPROC` and nothing to restore. So:

| What reaches the `LOCAL`                | OWL's treatment                                  |
|-----------------------------------------|--------------------------------------------------|
| one PROC/FN                             | save/restore within that routine                 |
| several PROC/FN (e.g. a shared `GOSUB`) | save/restore within each                         |
| also the main program (unstructured flow) | save/restore within the PROC/FN; **no-op** on the main-program path |
| only the main program (a top-level `LOCAL`) | **no-op** — the variable stays a plain global |

The guiding rule: **a `LOCAL` is a save/restore in each owning frame, and a no-op
wherever no frame is active.** Because variables are globals, "no frame" means
"use the global directly," which is a no-op — so OWL never has to reject a
program because a `LOCAL`'s scope looks path-dependent. (A `GOTO` that makes a
procedure's code reachable from the main program used to force a rejection; under
this rule the main-program path is simply the no-op.)

## Divergences from BBC BASIC

OWL is deliberately stricter/simpler than the interpreter in two ways. Both are
vanishingly rare in real programs (almost every `LOCAL` is a plain declaration at
the top of a procedure, followed by assignments to the localised variables).

1. **Whole-function, not positional.** OWL localises a variable for the *entire*
   body of its owning routine, not from the `LOCAL` statement onward. A read
   before the `LOCAL` sees the fresh local (0), where BBC would see the caller's
   value.

   ```basic
   X=5 : PROCp : END
   DEF PROCp : PRINT X : LOCAL X : ENDPROC
   ```
   BBC prints `5`; OWL prints `0`.

2. **No-op where there is no frame.** A `LOCAL` with no owning PROC/FN frame does
   nothing, where BBC would still save-and-zero the variable (and leak it). In
   practice the variable is assigned right after the `LOCAL`, so the difference is
   unobservable.

These follow from the save-on-entry/restore-on-exit implementation; reproducing
BBC's positional, per-statement dynamic save/restore would need a runtime value
stack and a push/pop per `LOCAL`, paying a cost on every program to match
behaviour no real program relies on. If one ever turns up, the cheap whole-
function path can stay for the common case and only that program escalate.

## Behaviours that *do* match BBC

* **Save/restore around a procedure**, including nesting — each level restores the
  enclosing value:

  ```basic
  G=1 : PROCa : PRINT G : END
  DEF PROCa : LOCAL G : G=2 : PROCb : PRINT G : ENDPROC
  DEF PROCb : LOCAL G : G=3 : PRINT G : ENDPROC
  ```
  prints `3`, `2`, `1`.

* **Leaking on an unstructured exit.** A `GOTO` out of a procedure bypasses its
  `ENDPROC`, so the `LOCAL` is never restored and the global keeps the local
  value — exactly as BBC leaks the frame:

  ```basic
  10 G=5 : 20 PROCp : 30 PRINT G : 40 END
  50 DEF PROCp : 60 LOCAL G : 70 G=99 : 80 GOTO 30 : 90 ENDPROC
  ```
  prints `99`.

## l-value `LOCAL`s

`LOCAL ?A`, `LOCAL !A`, `LOCAL $A`, `LOCAL A(i)` localise an *existing* storage
cell (a byte/word/string indirection or an array element), not a named variable.
These name no symbol; codegen saves and restores the addressed cell directly. The
attribution rule above is unchanged.

## Where this lives

* Attribution and scope: `owl_basic/symbol_table_visitor.py`
  (`visitLocal`/`visitPrivate`, `_owning_routine`, `checkPredecessorsAndRefer`).
* Save/restore codegen: the per-routine prologue/epilogue in
  `owl_basic/ext/backends/dotnet/emitter.py`; the `LOCAL` statement itself
  (`_stmt_Local`) is a no-op.
* Tests: `tests/test_local_scope.py`.
