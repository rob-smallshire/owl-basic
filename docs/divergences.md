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
| 8 | `LOCAL ERROR` / `RESTORE ERROR` (BASIC V) | push/pop the error context on the BASIC stack, so a `RESTORE ERROR` mid-PROC reinstates the caller's handler for the rest of the routine | no-op: the saved/restored context is the per-method dispatch, so the caller's handler is back in effect once the PROC returns, but a mid-PROC `RESTORE ERROR` does *not* switch handlers before then | OWL emits error dispatch per method, which already gives the save-on-entry / restore-on-return behaviour these directives request; a true savable handler stack would cost a push/pop with no real-program benefit | `tests/test_on_error.py` |
| 9 | `TRACE ON` / `TRACE OFF` / `TRACE <line>` | the interpreter prints each line number as it is executed | no-op (parses, emits nothing) | Interactive line tracing has no meaning for a compiled program | `tests/test_trace.py` |
| 10 | `CHAIN` | loads the file over the program at `PAGE` and runs it in place, preserving `@%`/`A%`-`Z%`, `HIMEM` and reserved memory | launches `<name>.dll` (the chained program's own compiled assembly) as a fresh process, carrying `@%`/`A%`-`Z%` across via `OWL_BASIC_RESIDENT_*` environment variables; named variables don't cross (faithful), but `HIMEM`-reserved memory doesn't either | The fresh process gives the "clear all dynamic vars" semantics for free, and the resident-integer channel is exactly the data BBC carries over; `HIMEM` blocks are machine-code territory (already out of scope) | `tests/test_chain.py`, `tests/test_resident_integers.py` |
| 11 | A constant computation that overflows (e.g. `100000*80500` into a `%`) | "Number too big" raised at run time, when that line executes | rejected at compile time (the constant folder evaluates it and the narrow-on-store check fails) | The value always overflows, so catching it at compile time is earlier and harmless; constant propagation extends this from literals to variables holding a single constant | `tests/test_wide_integers.py` (the runtime case uses `INPUT` operands), `docs/constant-propagation.md` |
| 12 | `PRINT#`/`BPUT#` string-record character set | a string's bytes are the BBC character set (e.g. `£` is byte `&60`) | a string's bytes are the .NET string's code units truncated to 8 bits (ISO-8859-1: `£` U+00A3 is byte `&A3`, and byte `&60` decodes to a backtick) | OWL strings are .NET strings, not BBC-charset byte strings; for ASCII (the overwhelming majority of data-file content) the bytes are identical, so files interoperate -- only the handful of glyphs the BBC remaps (notably `£` at `&60`) differ | `tests/test_print_input_file.py` (ASCII round-trips byte-for-byte against oaknut-basic) |
| 13 | Dynamically-correlated `FOR`/`REPEAT` loops | `NEXT`/`UNTIL` match the innermost open loop on a runtime stack: `NEXT var` pops loops until it finds `var` (so crossed nesting `FOR a:FOR b:NEXT a:NEXT b` and early `GOTO` out of a loop "work"), and a jump that lands between a `FOR` and its `NEXT` is fine because the frame is on the stack | rejected at compile time -- loops are compiled to static structured constructs, so a `NEXT`/`UNTIL` with no statically-matchable opener (crossed nesting, a `GOTO`/`THEN <line>` out of a `FOR`, a point reachable both inside and outside a loop by path) cannot be correlated and is an error | A runtime loop stack would amount to re-implementing the interpreter, defeating the purpose of a compiler; such programs are rare and frequently type-in typos (e.g. `NEXT J` for `FOR K`) | the loop-correlation errors in `correlation_visitor` ("`NEXT ... has no FOR loop to close`", "`UNTIL ... has no REPEAT loop to close`", "control flow ... inside different loops depending on the path") |

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
- **#8 / #9** keep BASIC V programs that sprinkle these directives compiling and
  running; both fall out of decisions already made (#8 from the per-method
  dispatch behind #3, #9 from compiling rather than interpreting).
- **#10** the resident integers are the *only* state BBC CHAIN carries over (plus
  `HIMEM`-reserved memory), so the environment channel is faithful to the data a
  program can pass; the fresh process is how a compiled target gives "replace the
  program and clear its dynamic world". The name-resolution (`<name>.dll`) and
  process launch live in the runtime, so another target can do the right thing
  differently.

- **#13** is a deliberate stance, not a trade: OWL is a *compiler*, and BBC's
  loop matching is a run-time stack operation. Supporting it faithfully would
  mean carrying that stack at run time -- re-creating the interpreter -- so OWL
  rejects the un-correlatable cases cleanly instead. In practice they are rare
  and usually program bugs.

Out of scope here (these are *limitations*, not divergences -- OWL rejects
cleanly rather than behaving differently): inline assembler (`[ ... ]`, rejected
by the backend; see `docs/inline-assembler.md`), `USR`/`SYS`/`CALL` to machine
code, `EVAL` of a runtime-dynamic string.
