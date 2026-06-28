# Corpus testing: measuring OWL against real BBC BASIC

OWL is validated not only by its unit tests but against large collections of
**real, published BBC BASIC programs** — thousands of them, from the 1980s
home-computing press and the modern BBC Micro Bot community. This document
describes those corpora, how they are obtained and run, the results to date, and
the conclusion reached.

> The corpus *programs* are not part of this repository and are not
> redistributed (see [Provenance and licensing](#provenance-and-licensing)).
> Only the **fetch/extract/run scripts** are committed. Everything below can be
> reproduced from those scripts.

## Why a corpus

Unit tests prove individual features; a corpus answers a different question: *of
all the BBC BASIC people actually wrote, how much does OWL compile?* It surfaces
real-world idioms, dialect quirks and edge cases no hand-written test would
think of, and it gives a single honest number to track over time. Several real
compiler fixes were driven directly by corpus findings (see
[Fixes driven by the corpus](#fixes-driven-by-the-corpus)).

A guiding principle (see [docs/divergences.md](divergences.md) and the project's
test-outcome discipline): **a clean rejection of a broken or unsupported program
is a passing outcome**, not a failure. The goal is to compile every *valid,
in-scope* program and to *gracefully reject* everything else — never to crash and
never to emit invalid IL.

## The corpora

| Corpus                | Origin                                                   | Form                                   | Programs |
|-----------------------|----------------------------------------------------------|----------------------------------------|----------|
| BBC Micro Bot / Owlet | `mattgodbolt/owlet-editor` examples + `bbcmic.ro` shares | one-screen modern listings (`.bbctxt`) | 534      |
| Acorn User            | monthly discs, 1985–94 (BBC Micro/Master era)            | ADFS old-map `.adl` images (`Tau*`)    | 1946     |
| The Micro User        | 8bs.com cover discs (`/pool/tmu`)                        | Acorn DFS `.ssd` images                | 1833     |
| A & B Computing       | 8bs.com cover discs (`/pool/aab`)                        | Acorn DFS `.ssd` images                | 688      |

The Micro User and A & B Computing corpora are monthly cover discs preserved by
the 8-Bit Software (8bs.com) archive: each magazine has a catalogue page (e.g.
`https://8bs.com/catalogue/a&b.htm`) linking one zip per cover disc, each zip
holding one or more DFS `.ssd`/`.dsd` images. The Acorn User corpus is a separate
set of ADFS `.adl` monthly-disc images (640 KB, BBC Micro/Master era — BASIC II,
some BASIC IV, no Archimedes BASIC V), obtained outside 8bs and placed in its
directory directly. The BBC Micro Bot corpus is short, single-tweet-sized
programs from the present-day community.

Each corpus lives under `local-corpus/<name>/` and shares the same harness:

- `fetch_*.py` — download the cover-disc zips (cached under `zips/`) and unpack
  the disc images. Present for the 8bs corpora (`fetch_tmu.py`, `fetch_aab.py`)
  and the bot corpus (`fetch_corpus.py` at the `local-corpus/` root); the Acorn
  User images were sourced separately, so that directory has no fetch script.
- `extract_basic.py` — export every file from each image, classify which are BBC
  BASIC, and write a parallel tree under `extracted/` with, per program, the
  tokenised `.bbc` (ground truth), a detokenised `.bas`, and the `.inf` sidecar.
- `run_corpus.py` — drive every extracted program through OWL and bucket the
  outcomes.

## How the pipeline works

```
disc image  --oaknut-disc export-->  files + .inf      (.ssd DFS / .adl ADFS)
   each file --bbcbasic_detect-->    is it BBC BASIC?  (structural test)
   each BASIC --oaknut-basic-->      detokenised source text
   each program --OWL analyse/codegen--> outcome bucket
```

- **oaknut-disc** reads Acorn DFS images; **oaknut-basic** is the canonical
  ROM-faithful (de)tokeniser (OWL delegates all (de)tokenisation to it — there is
  no second token table). The Acorn text codec (`£` etc.) is handled by
  `owl_basic.acorn_encoding`.
- `bbcbasic_detect.py` classifies a file as BASIC by *structure* (line-record
  framing, ascending line numbers, sane lengths) rather than guessing from a
  filename.
- Some images are cassette-audio rips or are damaged; those are skipped or
  contribute only their valid prefix, never aborting the run.

### In scope vs out of scope

`run_corpus.py` first splits the BASIC programs into **in-scope** (programs OWL
*should* be able to compile) and **out-of-scope** (constructs OWL deliberately
does not target). Out-of-scope reasons include inline 6502 **assembler** (`[ ]`),
embedded **machine code**, OS-call-dependent programs, and genuinely dynamic
`EVAL`. Pass rates are measured over the **in-scope** set only — compiling a
machine-code loader was never a goal. (Backend-specific constructs such as
`CALL`/`USR`/`SYS` are a backend decision, not a frontend rejection; see
[docs/backend-specific-constructs.md](backend-specific-constructs.md).)

### Stages and outcomes

Each in-scope program is run through, and bucketed by, the compiler's own stages:

- **parse** — detokenise → lex → parse (front end).
- **analyse** — flow graph, type check, symbol tables.
- **codegen** — emit textual CIL and assemble it with `ilasm` (only with
  `--codegen`; one subprocess per program).

An outcome is recorded as `ok`, a clean `OwlBasicError` (the compiler diagnosing
the program — a *good* outcome), or an unexpected exception / `ilasm` failure (a
real compiler gap to fix).

## Results

Point-in-time snapshot, June 2026 (rates over the in-scope set; the magazine
figures are the `--codegen` "compiles to .NET" numbers):

| Corpus                | BASIC progs | in scope            | compiles            | rate | crashes |
|-----------------------|-------------|---------------------|---------------------|------|---------|
| BBC Micro Bot / Owlet | 534         | — (mostly in scope) | 448 analyse cleanly | 84%  | 0       |
| Acorn User            | 1946        | 783                 | 737                 | 94%  | 0       |
| The Micro User        | 1833        | 1002                | ~897                | 89%  | 0       |
| A & B Computing       | 688         | 397                 | 332                 | 83%  | 0       |

Across the three magazine corpora: **~4,467 BASIC programs, ~2,182 in scope,
~1,966 compiling to .NET (~90% of in-scope), with zero compiler crashes and zero
invalid-IL failures.**

### What the remaining in-scope failures are

A systematic survey (parse, analyse and codegen/type diagnostics) found the
remaining in-scope failures are **overwhelmingly correct rejections**, not
compiler gaps:

- **Incomplete fragments.** Magazine programs were often printed as several
  numbered "listings" typed in together, or as overlays loaded by a main
  program. A fragment run in isolation is missing the `DIM`s and definitions in
  its siblings (e.g. Acorn User `M+W5` uses `vertex()`, which `M+W2` DIMs; the
  `UPORT2`/`SPARE2` overlays start at high line numbers). OWL correctly reports
  it as incomplete.
- **Genuine source typos** a real BBC also errors on: `ASC(X%)` for `ASC(X$)`,
  `MID$(D%,…)` for `MID$(D$,…)`, `IF code<>"UL"` for `code$`, a dropped `?`
  turning byte indirection `Cy%?(…)` into the array reference `Cy%(…)` (BBC
  `Array` error — see [docs/arrays-and-byte-blocks.md](arrays-and-byte-blocks.md)),
  and missing closing quotes.
- **Deliberate divergences**: the dynamic loop stack (see
  [docs/divergences.md](divergences.md)), computed `GOTO`/`GOSUB`, and inline
  assembler / machine code (out of scope by design).

At the codegen stage, **0 of ~1,970 analysing programs failed `emit_il`** — every
program that type-checks also generates IL.

The honest remaining lever is **corpus scope refinement** — reclassifying
multi-listing fragments and overlays as out-of-scope so the in-scope rate
reflects reality (it is somewhat higher than measured). That is a measurement
improvement, not a compiler change.

## Fixes driven by the corpus

A sample of real compiler improvements the corpus surfaced:

- **Array fields declared at their intrinsic `DIM` rank** — a multidimensional
  array used before its `DIM` (in emission order) could be declared 1-D and
  referenced 2-D, producing invalid IL that `ilasm` rejected (Acorn User
  `JigArc`). Now the rank is settled program-wide from the `DIM` first.
- **BASIC V keywords as BASIC II variable names** — `SUM`, `WAIT`, `SWAP` and
  `POINT` were not keywords in BASIC II, so older listings use them as variables
  (`WAIT$`, `SUMX`, `POINTER$`). Given a conditional-keyword lexer guard, matching
  the ROM's own conditional-flag keywords.
- **Byte-block-vs-array diagnostic** — distinguishing `DIM b% 100 : b%(5)` (a
  byte block indexed as an array → BBC `Array` error) from a genuinely
  undimensioned array.
- **Undimensioned-array / rank-mismatch diagnostics** — reject statically
  rather than emit invalid IL (Acorn User `STRUM`).
- **EVAL static lowering**, **block IF/CASE detection**, and others recorded in
  their own docs and the divergences catalogue.

## Provenance and licensing

The corpus programs are **not committed and not redistributed**. `local-corpus/`
is git-ignored. The magazine programs are 1980s cover-disc material (The Micro
User and A & B Computing via the 8bs.com archive; Acorn User from a separate
preservation of ADFS discs); OWL processes them on demand for local measurement
only and does not re-host them. The 8bs corpora are fetched on demand by their
scripts; the Acorn User images are placed in the directory by hand. The BBC Micro
Bot corpus is fetched from sanctioned sources (`owlet-editor`'s `examples.yaml`
and opt-in `bbcmic.ro` shares), not by scraping.
Fetchers identify themselves politely (a project User-Agent, with rate limiting)
and cache downloads so a re-run only fetches what is missing.

Only the **scripts** that fetch, extract and measure are under version control,
so the results are reproducible by anyone who runs them, without this repository
carrying third-party program data.

## Reproducing

From a corpus directory (e.g. `local-corpus/a-and-b/`):

```sh
uv run python fetch_aab.py        # or fetch_tmu.py / fetch_corpus.py
uv run python extract_basic.py    # export + classify -> extracted/
uv run python run_corpus.py            # analysis only (fast)
uv run python run_corpus.py --codegen  # also assemble with ilasm (slower)
```

`run_corpus.py` writes `corpus-run/results.tsv` (one row per program: stage,
kind, category, exception type, message) and a `summary.txt` with the counts.
The BBC Micro Bot corpus uses `pytest local-corpus/test_corpus.py` instead.

## Status

As of June 2026, the corpora are considered **well into diminishing returns**.
The compiler compiles the large majority of in-scope programs across four
independent corpora with no crashes and no invalid IL; the residual failures are
predominantly correct rejections of incomplete fragments, genuinely broken
listings, and deliberately out-of-scope constructs. Further pass-rate gains would
come mainly from scope refinement (a measurement change) rather than new compiler
capability.
