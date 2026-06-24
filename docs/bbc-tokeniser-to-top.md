# `TO`, `TOP`, and keyword adjacency in the BBC tokeniser

This note records how the BBC BASIC II ROM tokenises keywords that abut the
following text — in particular the `TO` / `TOP` case — and how OWL reproduces the
observable result. The behaviours here are pinned by
`tests/test_keyword_adjacency.py`. Findings below are from the 6502 BASIC II
disassembly annotation; OWL is a text-front-end compiler, so it must match what
the ROM *observably* does with a (de)tokenised text listing.

## `TOP` is not a token

The keyword table holds **only `TO`** (token `&B8`, flag `&00`). There is no
table entry beginning `TOP`. The letters `TOP` therefore always crunch to two
bytes: the `TO` token `&B8` followed by a **literal ASCII `P` (`&50`)** left in
the line as ordinary text.

`TOP` (the top-of-program pseudo-variable) is detected at **evaluation time**,
not by re-reading the letters `T-O-P`. The action-table slot for `&B8` routes a
`TO` token, when the expression evaluator needs a *factor*, to `fn_to` (`&AEDC`).
`fn_to` peeks the immediately following byte: if it is `P` (`&50`) it consumes it
and returns `zp_top` (top of program); anything else is a syntax error. So by the
time `TOP` is recognised, the `TO` is already a single token and only the `P` is
a raw letter, read by `fn_to`.

## What distinguishes `PRINT TOP` from `… TO P`

It is the **tokenise-vs-runtime split**, not the surrounding characters. Both
forms tokenise to identical bytes: `[TO &B8] [P &50]`. The meaning is fixed at
runtime by the grammatical role the `TO` token plays:

* `TO` reached where a **factor/operand** is expected → factor dispatch → `fn_to`
  → it reads the contiguous `P` → **`TOP`** (e.g. `PRINT TOP`; or as a `FOR`
  limit, `FOR I=0 TO TOP`).
* `TO` reached as the structural **`FOR` separator** → consumed by `stmt_for`
  (which matches `&B8` directly), not by `fn_to` → the following `P` then begins
  the limit expression.

So in `FOR I=…+2 TO P+98` (byte-saved `…+2TOP+98`) the `P+98` is the limit; in
`PRINT TOP` the `TO` is in value position, so `fn_to` glues the `P`. A bare `TO`
in operand position *not* followed by `P` — e.g. `PRINT TO+1` — is a syntax error.

## When does `TO` crunch at all? — the name-run rule

`TO` is tokenised only at the **start of a name-run**. A *name character* is
exactly `0-9 A-Z a-z _` (and, incidentally, backtick); the ROM's `is_alphanumeric`
test explicitly excludes `% $ # ( ) [ ] ^` and all operators. A run-start is any
position **not** mid-name: right after any non-name character, after a completed
number literal, or after an emitted token.

So `TO` crunches after **every value terminator**, and all of these glue:

| Source        | After   | Tokenises as      |
| ------------- | ------- | ----------------- |
| `FNf(0)TOP+1` | `)`     | `… ) [TO] P + 1`  |
| `I%TOP`       | `%`     | `I% [TO] P`       |
| `A$TOP`       | `$`     | `A$ [TO] P`       |
| `)]TOP`       | `]`     | `… ] [TO] P`      |
| `0TOPI`       | digit   | `0 [TO] PI`       |
| `2TOP+98`     | digit   | `2 [TO] P + 98`   |

The only time `TO` does **not** crunch is when it continues an identifier — i.e.
immediately preceded by a name character that is part of the *same* name:
`XTOP`, `A1TOP`, `T0TAL` keep the `TO` buried and the whole run is one variable.
(Note the digit nuance: a digit ending a *number* yields a run-start, so `0TOP`
splits; a digit *inside a name* like `X9TOP` keeps `TO` buried.)

## How OWL reproduces this

OWL keeps a dedicated `TOP` token and a grammar rule (`top_func : TOP`) for the
pseudo-variable, rather than splitting universally and reconstructing `TOP` in the
parser. The lexer therefore approximates the ROM's grammatical operand-position
test with the **previous token's type**, which is exact for realistic listings:

* `t_TOP` matches `TOP` only when **not** followed by a name char (so `TOPI`
  falls through to `TO` + `PI`, matching the name-run rule).
* When the **previous token completes a value** — a literal, a variable (`ID`),
  `)`, `]`, or a nullary value pseudo-variable (`PAGE`, `TIME`, `PI`, `TOP`, …) —
  the `TO` cannot start a fresh operand abutting that value, so it is the `FOR`
  separator: the lexer emits `TO` and leaves the `P` to re-lex. This is the byte
  saver, whether glued (`P+2TOP`) or spaced (`P+2 TOP`).
* Otherwise (the previous token is an operator, `=`, `(`, `,`, `TO`/`STEP`, a
  statement keyword, or there is none — line start — i.e. operand position) the
  `TOP` token stands as the pseudo-variable.

Keying on the previous *token*, not the preceding *character*, is essential: in
both `P+2 TOP` and `PRINT TOP` the character before `TOP` is a space; only the
previous token (a literal vs the `PRINT` keyword) distinguishes the loop limit
from the pseudo-variable. (The tracking is the same `lexer.last_token_type` that
`t_STAR_COMMAND` already uses.)

Verified on the ROM: `PRINT TOP` prints an address (`6402` in the test machine),
while `FORI=P+2TOP+98` and `FORI=P+2 TOP+98` both run as `FOR I=P+2 TO P+98`.

`STOP` is unaffected: its own four-letter rule consumes the whole word before the
`TOP` rule is ever tried.

### Known residual divergence

Because OWL keys on the previous token rather than fully reconstructing the
pseudo-variable in the grammar, one theoretical gap remains: a value-completing
token *type* not listed in `_TOP_VALUE_ENDERS` would leave a following glued/spaced
`TOP` as the pseudo-variable instead of splitting it, so a `FOR` limit written
`<that value> TOP` would fail to parse. The set covers every value-ending token in
practice; if the corpus ever surfaces a miss, add the token type there. (The
earlier preceding-character approximation also diverged on `&2FTOP` and the spaced
`0 TOP`; keying on the token type fixes both.)

A fully faithful implementation would split `TO`/`P` universally in the lexer and
reconstruct the pseudo-variable in the grammar (a `TO` in operand position
immediately followed by the identifier `P`), mirroring `fn_to`.
