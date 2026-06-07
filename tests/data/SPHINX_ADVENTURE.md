# Sphinx Adventure: replay, determinism, and faithfulness notes

This document records what we learned while compiling Acornsoft's **Sphinx
Adventure** (`SPHINX2`, BBC BASIC) with OWL BASIC and driving it to completion
with an automated player. It sits alongside the solution transcripts used by the
playthrough test (`tests/test_sphinx_playthrough.py`) and the driver
(`tests/helpers/sphinx_player.py`).

## The solution files

| File | Source | Notes |
|------|--------|-------|
| `sphinx_solution.txt` | solutionarchive.com id 20885 | The route used by the playthrough test. Comma/newline separated. |
| `sphinx_solution2.txt` | solutionarchive.com id 712 | Faithful re-transcription (see "Interpretation" below). |
| `sphinx_solution3.txt` | hand transcription of id 712 | One command per line; expands the `(AXE)` note to `TAKE AXE`. |

All three are the *treasure route* — the sequence of commands that collects and
delivers the treasure. They are **not** complete input scripts: they omit the
reactive "housekeeping" a live player must perform (see "What the walkthroughs
leave out").

### Interpretation — a walkthrough is not a literal command list

Published walkthroughs need intelligence to become real game input. Splitting on
commas/newlines is not enough:

- **Compound lists**: `Drop the rug, gold, silver, ...` is one instruction
  meaning `DROP` mapped over each item — `DROP RUG`, `DROP GOLD`, `DROP SILVER`,
  … A naive split turns "gold", "silver", … into bogus standalone commands.
- **Prompt responses, not commands**: `KILL OGRE` / `NO` / `SWORD` is one logical
  action. `KILL OGRE` triggers "What with? Your bare hands"; `NO` answers it, then
  "What with then"; `SWORD` answers that. Likewise `KILL DRAGON` / `YES` (bare
  hands) and `KILL VAMPIRE` / `NO` / `STAKE`. They only work as a group — removing
  the `KILL` means removing its responses too.
- **Two words maximum**: the parser only looks at two words (line 204), so
  `Drop the rug` must become `DROP RUG`.
- **Exact vocabulary**: nouns must match the game's word list — `DROP SAPPHIRE`
  fails; it is `SAPPHIRES`.

## What the walkthroughs leave out: the autoplayer's reactive policy

The driver (`sphinx_player.py`) feeds a solution but reacts to two pseudo-random
events the route omits:

- **The dwarf** — once a dwarf has thrown an axe at you (`D<>0`), `PROCL` line
  284 (`IF D<>0 O?31=L`) makes it follow you into every room, so it cannot be
  outrun; it must be killed. Each turn it is present there is a ~10% instant-kill
  roll (`RND(1)>.9`, line 194) plus a guaranteed kill once it has thrown 7 times
  (`D>6`). The driver kills it with:
  - `THROW SWORD` (100% kill, line 394) before the ogre, re-collecting the sword
    after each throw (throwing *drops* the weapon — `PROCG(W2,1,L)` moves it to
    the floor);
  - `THROW AXE` (60% kill, line 383) afterwards, since the sword melts on the ogre.
- **The lamp** — `LF` (lamp fuel) starts at 50 and drops by 1 each lit turn;
  at 0 it is dark and you can fall in a pit. The driver issues `RUB LAMP` when it
  reads "lamp is getting dim"/"has run out" (line 415 refuels `LF` to 150).

### Weapons against the dwarf — why the post-ogre axe is the weak point

- The **sword** is never consumed by dwarves (you re-collect it after every
  throw); it is destroyed *only* when it kills the **ogre** (line 394 sets
  `O?2=0`, "melts away"). Killing the ogre is mandatory to pass.
- The **axe** (object 1) is never placed in any room — it starts at room 0
  (nowhere) and the *only* way to obtain one is to pick up an axe a dwarf threw
  and missed with (line 193: `IF O?1<>1 O?1=L`). This is what the `(AXE)`
  annotation in solution 712 means: at that point a dwarf has dropped an axe;
  `TAKE AXE`. It is seed-dependent (a dwarf must actually appear there).
- So after the ogre, dwarves can only be fought with the 60%-per-throw axe, which
  drops on each throw. A dwarf can therefore take several turns to kill, and if
  its 3 reachable throws all miss (before `D>6`) it kills you. **This is what
  makes some seeds unwinnable with this route.**

## Determinism: the game is reproducible per power-on

BBC BASIC's `RND` is a 33-bit LFSR (primitive trinomial (33,20,0)) seeded from a
fixed power-on value, and **Sphinx never re-seeds it** (it uses only `RND(1)`,
`RND(5)`, `RND(10)` — no `RND(-n)`). Confirmed from the BASIC II ROM disassembly:
the seed bytes `&0D-&11` are written in only three places —

1. language entry (`&8059`): the cold seed bytes "ARW" (`&575241`), **and only if
   the seed area is zero**;
2. `RND(-n)` (unused by Sphinx);
3. the LFSR shift itself.

Consequences:

- From a **cold boot** the RNG starts at "ARW" and the entire "random" sequence
  (when the dwarf appears, whether the axe hits, …) is **identical every run**.
- `RUN`, `CHAIN`, and the game's own "R to restart" (line 232) do **not** reseed.
  Neither does `BREAK` unless memory was cleared (a true cold start). So the seed
  **persists and advances** across restarts: die and restart-without-reset and
  you get a *different* deterministic game — the seed has moved along the LFSR.

This is why a memorised walkthrough works at all, and why the published routes
solve the game from *some* state — the author was almost certainly not playing
from the pristine cold seed.

## Result: cold boot is unwinnable first-try; winnable by rerolling

With this route and reactive combat:

- **The cold seed dies** — deterministically at solution index ~339 (score 530),
  to a post-ogre dwarf whose axe throws miss (`D>6`). This is genuine BBC
  behaviour, reproduced on the real machine (see Faithfulness).
- **Seed 1 wins 800/800** (delivering every treasure), and seed 4 reaches 740.
  `OWL_RANDOM_SEED=1` is what `test_solves_the_whole_game` asserts.
- **The reroll loop wins from cold**: play; on death `reincarnate` → `QUIT` → `R`
  (a `RUN` that keeps the advanced RNG); retry. From the cold seed this won
  800/800 on the 9th attempt — exactly how a real player rerolls until the dice
  cooperate.

So "winning from the cold seed" means: start at "ARW", and if you die,
restart-without-reset to advance the never-reseeded RNG and retry, until the
route lands on a survivable configuration.

## Faithfulness: OWL BASIC matches the real BBC

Validated against **Beebium**, a high-fidelity BBC Micro emulator running the
real ROMs and the original `SPHINX2` from disc:

- **The cold-boot RND state is byte-exact.** At the first prompt the emulator's
  seed is `0x750FBE70` (overflow 1) — exactly OWL's cold seed `0x00575241`
  stepped once by the LFSR (Sphinx calls `RND` once, at line 192, before the
  first prompt).
- **RND consumption matches move-for-move.** Counting RND calls via a debugger
  breakpoint on the LFSR routine (`&AF87`) shows OWL and the real BBC make the
  same number of calls per turn (one, from line 192).
- **`AND`/`OR` are evaluated eagerly** in OWL, matching BBC's non-short-circuit
  bitwise operators (so a side-effecting `RND` in either operand is always
  called). `OWL_RND_TRACE=1` dumps OWL's RND state at each prompt for this kind
  of differential.

A caution learned the hard way: the emulator's MODE 7 screen is a **wrapping text
window that overwrites in place**, and the MOS flashing cursor toggles screen
RAM; the zero-page seed bytes are also reused as scratch. Naive screen scraping
and arbitrary seed reads are therefore unreliable and produced a *phantom*
"drift" that turned out to be a measurement artifact, not a real divergence. The
clean signals are the LFSR-breakpoint call count and the byte-exact start.

## Practical notes for re-running

- Build the game: `uv run python tools/build_sphinx.py build/sphinx`.
- Deterministic seed override for tests: `OWL_RANDOM_SEED=<int>` (behaves like a
  `RND(-n)` reseed; unset = the faithful cold seed).
- The autoplayer is POSIX-only (it uses `select` on a pipe).
- A bare walkthrough replayed without the reactive combat/lamp policy dies at the
  first dwarf or when the lamp runs out.
