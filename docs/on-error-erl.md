# ERL: recovering the error line without a hot-path cost

> Catalogued in [docs/divergences.md](divergences.md) (entry 2).


`ERL` is the line number at which the last error occurred. `ERR` (number) and
`REPORT`/`REPORT$` (message) are easy -- the catch's `RecordError` reads them
straight off the caught exception, on the error path only, so they cost nothing
in normal execution. `ERL` is harder: the error is thrown deep in runtime code
(`Sqr`, integer `div`, ...) which has no idea which BASIC line it is serving,
and the throw unwinds the CLR stack, so a PROC's "current line" held in a local
is gone by the time Main's `catch` runs.

## What we do today (the stub)

`ERL` returns `0`. `RecordError` sets `errorLine = 0`; nothing tracks the line.
This keeps normal execution free of any per-line overhead. Handlers that only
use `ERL` for a cosmetic `"... at line "; ERL` still run; they just print line
`0`. (Pinned by `tests/test_on_error.py`.)

## Why not just track the line per line

The obvious implementation -- emit `ldc.i4 <n> : stsfld currentLine` at the top
of every line, and have `RecordError` snapshot it -- puts two instructions and a
static-field write on **every line executed**. For a tight numeric loop that is
a large, permanent tax on the common case to serve a rare, mostly-cosmetic
feature. Rejected on those grounds (it also clashes with the project's
"no hot-path checks; pay on the exceptional path" stance).

## The planned approach: debug line info + stack-trace recovery

Recover the line from .NET debug information, paying **nothing** until an error
is actually caught:

1. **Emit `.line` directives.** When lowering each statement (or each line's
   first statement), emit an ILASM `.line <logical-line> '<name>.bas'`
   directive ahead of it. These are debug *metadata*, not executable
   instructions -- the JIT-compiled code is byte-for-byte unchanged, so there is
   zero runtime cost on the normal path. The source-position data is already
   available (`SourceDebuggingVisitor`, and `start_line`/`startPos` on each
   statement).

2. **Assemble with a PDB.** Run `ilasm` with `/debug` (portable PDB) so the line
   table ships alongside the assembly, and copy the `.pdb` into the output
   directory next to the `.dll` (as we already do for `OwlRuntime.dll`).

3. **Read the line on catch.** In `RecordError(Exception ex)`, walk
   `new StackTrace(ex, true)` from the throw site outward, find the first frame
   in the compiled program assembly (Main or a `PROC`/`FN` method -- skip the
   `OwlRuntime` frames where the exception was actually raised), and read
   `frame.GetFileLineNumber()`. That is the BASIC line of the erroring
   statement. Store it in `errorLine`.

### Cost

- Normal path: zero (the directives generate no code; the PDB is only read on
  demand).
- Error path: one stack-trace materialisation and walk -- cheap, and errors are
  rare.
- Build: slightly larger output (the `.pdb`) and the directives in the `.il`.

### Caveats / things to verify when implementing

- Confirm the line actually survives to the runtime stack trace: assemble a
  tiny program with `.line` directives and `/debug`, throw, and check
  `new StackTrace(ex, true).GetFrame(i).GetFileLineNumber()` reports it. JIT
  optimisation can blur line precision; if a frame reports 0, fall back to the
  nearest frame that has a line.
- The `.pdb` must be deployed with the `.dll`; without it `GetFileLineNumber()`
  returns 0, which is exactly today's stub -- a safe degradation.
- This same `.line`/PDB groundwork enables real source-level debugging (stepping
  a BASIC program in a .NET debugger) later, so the work is reusable.
