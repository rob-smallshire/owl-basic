# Deliberate divergences from BBC BASIC

OWL aims to be a faithful BBC BASIC compiler, but in a few places it knowingly
behaves differently -- almost always to keep the *common* path fast or simple,
to match the realities of a .NET target, or because the faithful behaviour costs
far more than any real program needs. This is the catalogue of those choices,
collected for the eventual compiler documentation.

Each entry names the BBC behaviour, OWL's behaviour, the reason, and the
authoritative test/doc (the tests are the real specification -- if this table
and a test ever disagree, the test wins). **When you introduce a deliberate
divergence, add it here.** Divergences that are bugs to be fixed do not belong
here; only intentional ones.

| # | Area | BBC | OWL | Why | Authority |
|---|---|---|---|---|---|
| 1 | Float division by zero | `1/0` raises "Division by zero" (error 18) | `1/0` = `+Infinity`, no error | A zero-check on every `/` is too costly on the hot path for a rare case (`DIV`/`MOD` by zero still error -- the CLR throws those for free) | `tests/test_division_by_zero.py` |
| 2 | `ERL` (error line) | the line where the last error occurred | `0` (not tracked) | Per-line tracking would tax every line run; a zero-cost `.line`/PDB approach is planned | `docs/on-error-erl.md`, `tests/test_on_error.py` |
| 3 | `ON ERROR` (non-LOCAL) inside a PROC | resets the BASIC stack to the top and runs the handler there | caught within the PROC, like `ON ERROR LOCAL` | The dispatch is per method, which gives correct `LOCAL` semantics for free; the non-LOCAL-in-a-PROC form is rare and absent from the corpus | `_stmt_OnError` comment, `tests/test_on_error.py` |
| 4 | `LOCAL` scope | positional -- localises from the `LOCAL` statement onward | whole-routine -- localised for the entire body | A read *before* the `LOCAL` sees the fresh `0`, not the caller's value; positional save/restore would need a runtime stack and a push/pop per `LOCAL` | `docs/local-semantics.md` |
| 5 | `LOCAL` with no PROC/FN frame | saves-and-zeroes the variable (and leaks it) | no-op | Follows from save-on-entry/restore-on-exit; unobservable in practice (the variable is assigned right after) | `docs/local-semantics.md` |
| 6 | Hex `EVAL`/literals, 9-16 digits | the ROM wraps to the low 32 bits (`&1FFFFFFFF` -> `-1`) | superset: folds to 64 bits, matching OWL's own hex-literal lexer | OWL's numeric model is 64-bit internally; the 8-digit (32-bit) case is unchanged | `docs/eval-static-compilation.md`, `tests/test_eval_static.py` |
| 7 | `<value> TOP` as a `FOR` limit (residual) | always splits `TOP` after a value | one un-listed value-ending token *type* could leave `TOP` glued as the pseudo-variable | Keys on the previous token type rather than re-parsing; the set covers every value-ender in practice -- extend it if the corpus surfaces a miss | `docs/bbc-tokeniser-to-top.md` |

## Notes

- **#1 / #2** are performance trades and align with OWL's general stance: lean on
  the CLR's own checks and the exceptional path, don't put checks on the hot
  path. #2 additionally has a concrete zero-cost plan (`docs/on-error-erl.md`).
- **#3** is a small semantic gap, not a trade -- worth revisiting if a program
  ever relies on a non-LOCAL handler-in-a-PROC unwinding to the top.
- **#6** is a *superset* (OWL is more permissive), not a loss of fidelity on any
  input a real BBC accepts.
- **#7** is a residual parsing gap with a clear fix (extend the token set) rather
  than a permanent choice.

Out of scope here (these are *limitations*, not divergences -- OWL rejects
cleanly rather than behaving differently): inline assembler (`[ ... ]`, rejected
by the backend; see `docs/inline-assembler.md`), `USR`/`SYS`/`CALL` to machine
code, `CHAIN`, `EVAL` of a runtime-dynamic string.
