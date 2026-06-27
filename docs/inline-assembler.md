# Inline assembler: division of responsibilities

> This is the worked example of a general principle. `CALL`, `USR` and `SYS` are
> target-specific in the same way and follow the identical frontend-parses /
> backend-decides contract — see
> [`backend-specific-constructs.md`](backend-specific-constructs.md).


BBC BASIC lets a program drop into a machine-code assembler between `[` and
`]`. The dialect inside the brackets is target-specific (6502 on the Model B,
ARM on the Archimedes) and is *not* portable between machines -- a program's
`[ ... ]` block only means anything to the CPU it was written for.

OWL targets .NET CIL and cannot run 6502 or ARM machine code, so it cannot
compile these blocks. But "can this be compiled?" is a **backend** question, not
a **frontend** one: a hypothetical `bbc-micro-6502` backend *would* compile a
6502 block, and the existing `dotnet` backend could in principle accept a block
of inline CIL (OWL already emits textual CIL and assembles it with `ilasm`). So
the frontend must not reject assembler out of hand -- that would bake one
backend's limitation into the language.

## The decision

The contents of a `[ ... ]` block are treated as **opaque text** by the
frontend. The frontend recognises the block and captures it verbatim; it does
*not* tokenise, validate, or understand what is inside. Whether (and how) a
block compiles is decided by the backend at code generation.

### Frontend (backend-agnostic)

- Recognise `[ ... ]` and capture its contents verbatim (the lexer's
  `t_ASSEMBLER` rule grabs the whole block, across line boundaries, to the
  closing `]`). The closing `]` is the first one **not inside a quoted
  string**: confirmed against the BBC BASIC ROM, the terminator is only
  recognised at the start of a statement, and a string operand such as
  `EQUS "Contains]"` is read whole, so a `]` between quotes is string data, not
  the terminator.
- Produce one generic `InlineAssembler` statement node carrying that raw text.
  It flows through analysis like any opaque statement; it has no operands or
  type the frontend reasons about.
- **Never reject the block.** A program containing assembler is a valid parse.
- A backend that wants help may call back into the frontend's existing services
  (e.g. "parse this fragment as a BASIC expression") -- the frontend offers,
  the backend decides whether to use them. The frontend never drives assembler
  parsing itself.

### Backend (at code generation)

- Owns the capability decision and the dialect. On meeting an `InlineAssembler`
  node a backend either lowers it (its own assembler, an external assembler, or
  inline CIL) or raises a clean `CompileError` naming itself.
- The `dotnet` backend has no assembler dialect, so its emitter rejects the
  node: *"the dotnet backend does not support inline assembler at line N"*.
  This is an ordinary `_stmt_InlineAssembler` handler, not the generic
  "Cannot lower" fallback.

### Explicitly out of scope

The assembler *harness* -- `P%`/`O%` (program counter / output pointer), the
two-pass `FOR pass% = 0 TO 2 ... NEXT` loop, runtime assemble-then-`CALL` -- is
ordinary BASIC the program supplies, interpreted by the backend's dialect per
its own contract. None of it has to be portable, because the assembler it
serves is not portable either.

## What this buys us now

The `dotnet` backend still cannot run machine code, so assembler programs are
still rejected -- but at the right layer, with an honest message, and the rest
of each program now parses and analyses cleanly. Across the Acorn User corpus
this turns ~467 "Syntax error at `[`" frontend failures (which read like a
compiler bug) into a clear backend limitation, and a future `bbc-micro-6502`
backend slots in without touching the frontend.

## Implementation note

OWL's strict per-line parse gate (`analyse_numbered_lines`) checks each line
independently, so it cannot see a block whose `[` and `]` are on different
lines. The gate therefore skips lines that lie within an assembler span
(`_assembler_block_numbers`, which scans string-aware to match the lexer); the
whole-program parse then captures the block as a single `ASSEMBLER` token. The
executable specification is `tests/test_inline_assembler.py`.
