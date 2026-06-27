# Backend-specific constructs: CALL, USR, SYS and inline assembler

Some BBC BASIC constructs are *target-specific*: what they mean, whether they
can be compiled, and even the syntax of their arguments depend on the machine
being compiled for, not on the language. Four of them:

| Construct | BBC meaning |
|---|---|
| `[ ... ]` | inline assembler (6502 on the Model B, ARM on the Archimedes) |
| `CALL addr[, params]` | enter a machine-code routine at an address |
| `USR(addr)` | call a machine-code routine, returning a value |
| `SYS swi[, in...] [TO out...]` | a system call (a RISC OS SWI on the Archimedes) |

## The principle

> "Can this be compiled?", "what does it lower to?", and "what do its arguments
> mean?" are **backend** questions for a target-specific construct, never
> **frontend** ones.

The frontend parses each into a neutral AST node, capturing its operands as
generic expressions (or, for assembler, opaque text) without committing to their
meaning. It **never rejects one for being target-specific**. Each backend then
owns the decision: lower the construct in its own dialect, or raise a clean
`CompileError` *naming itself* — never the generic "cannot lower" fallback, and
never a frontend refusal that bakes one backend's limitation into the language.

This is the same division already documented for inline assembler in
[`inline-assembler.md`](inline-assembler.md); that is the worked example, and
`CALL`/`USR`/`SYS` follow the identical contract.

### Why it matters

- A future `bbc-micro-6502` backend compiles **all four** natively. The `dotnet`
  backend cannot run 6502/ARM machine code, so it rejects `CALL`, `USR` and
  inline assembler — but that is a property of the *(program, backend)* pair,
  not of the program. Hardcoding the rejection in the frontend would foreclose
  the 6502 backend.
- The **argument syntax is itself target-specific**: a `SYS`'s SWI number and
  its in/out register lists mean nothing to .NET, whereas a `.NET` backend would
  read the same slot as a managed method signature. So argument *interpretation*
  (and any validation beyond a generic parse) is delegated to the backend too.

### `SYS` as a .NET FFI (future)

`SYS` is a system-call gateway, which makes it the natural place for a managed
foreign-function interface on the `dotnet` backend: `SYS "Type.Method", args TO
result` could invoke a .NET method by name. The same node a 6502 backend maps to
an OS SWI, the .NET backend maps to a managed call — one frontend construct, two
backend meanings. This is why `SYS` should be repurposed rather than closed off.

## Current state

| Construct | Frontend | `dotnet` backend |
|---|---|---|
| inline assembler | parses to `InlineAssembler` (opaque text) ✓ | clean rejection at codegen ✓ |
| `CALL` | parses to `Call` ✓ | clean rejection at codegen ✓ |
| `SYS` | parses to `Sys` ✓ | **TODO** — currently the generic "cannot lower"; should be a clean backend rejection (and, later, the FFI) |
| `USR` | **TODO** — no grammar production, so it fails at parse | — (cannot reach the backend yet) |

The remaining gaps are: `USR` needs a neutral node so it parses and reaches the
backend; the `dotnet` backend should reject `SYS`/`USR` with an honest,
self-naming message (as `CALL` and assembler already do). The frontend's
parse-failure diagnostics that name `USR`/assembler (`analysis.py`) are a
courtesy message on a failed parse, not the design — once `USR` parses they fall
away.

## Corpus accounting

In the corpus harness "out of scope" means **not compilable by the prevailing
(`dotnet`) backend**, not universally uncompilable. A `bbc-micro-6502` backend
would move the `assembler` / `machine-code` (`CALL`/`USR`) / `os-call` (`SYS`)
programs into the should-compile set without any frontend change.
