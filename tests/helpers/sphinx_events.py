"""Shared, emulator-free logic for driving Sphinx Adventure.

Two concerns, both pure (no subprocess, no emulator) so they can be unit-tested
directly (see tests/test_sphinx_events.py) and reused by both drivers:

* the reactive **Policy** -- given the game's latest output, decide the next
  command, handling the pseudo-random events a walkthrough omits (the dwarf, the
  lamp). Shared by the OWL transcript autoplayer (helpers/sphinx_player.py) and
  the Beebium screen driver (tools/sphinx_beebium_player.py).

* **MODE 7 viewport reconstruction** -- turn a sequence of 25-row screen
  snapshots from a scrolling MODE 7 display into an append-only transcript,
  recovering exactly the lines new since the last snapshot. Used only by the
  Beebium driver (the OWL player gets clean line-buffered text from a pipe).

See tests/data/SPHINX_ADVENTURE.md for the game mechanics behind the policy.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


# --- message vocabulary (lower case; matched as substrings of the latest text) -

DWARF = "there is a dwarf here"
SWORD_GOT = ("you take the sword", "you get the sword")
AXE_GOT = ("you take the axe", "you get the axe")
SWORD_MELTS = "melts away"            # the sword is destroyed killing the ogre
DWARF_KILLED = "you killed a dwarf"
LAMP_DIM = "lamp is getting dim"
LAMP_OUT = "lamp has run out"
WON = "solved the puzzle"
DIED = ("you have been killed", "reincarnat")

_WS = re.compile(r"\s+")


def joined(lines: list[str]) -> str:
    """Lower-cased, whitespace-collapsed join, for substring matching.

    Joining with spaces stitches a message that wrapped across lines back into
    one searchable string.
    """
    return _WS.sub(" ", " ".join(lines)).strip().lower()


# --- reactive policy (shared by both drivers) ---------------------------------

@dataclass
class Policy:
    """Reactive combat/lamp policy layered over the solution walkthrough.

    Priorities, highest first. The ordering encodes "avoid the most immediate
    death first": a *present dwarf* can kill you this very turn (a ~10% instant
    roll each turn it is here, and a guaranteed kill once it has thrown 7 times),
    so fighting it -- and re-arming so we *can* fight it -- outranks the lamp. A
    dead/dim lamp only kills you if you then *move* in the dark; rubbing and
    fighting do not move you, so the lamp can safely wait a turn or two behind
    combat.

      1. terminal (won / died)         -> stop
      2. a dwarf is present            -> fight it (throw/re-collect sword, then
                                          axe once the sword has melted)
      3. re-arm after a throw          -> pick the weapon back off the floor
                                          (the dwarf follows; be ready next turn)
      4. lamp is dim or has run out    -> RUB LAMP (before any ordinary move)
      5. otherwise                     -> the next walkthrough command
    """
    have_sword: bool = False
    sword_gone: bool = False        # melted on the ogre; only the axe remains
    have_axe: bool = False
    need_resword: bool = False      # threw the sword; it's on the floor
    need_reaxe: bool = False        # threw the axe; it's on the floor
    kills: int = 0
    rubs: int = 0
    outcome: str = ""               # "WON" / "DIED" once terminal

    def observe(self, text: str) -> None:
        """Fold the latest output text (lower-cased) into combat/lamp state."""
        if any(s in text for s in SWORD_GOT):
            self.have_sword = True
            self.need_resword = False
        if any(s in text for s in AXE_GOT):
            self.have_axe = True
            self.need_reaxe = False
        if SWORD_MELTS in text:
            self.have_sword = False
            self.sword_gone = True
        self.kills += text.count(DWARF_KILLED)
        if WON in text:
            self.outcome = "WON"
        elif any(s in text for s in DIED):
            self.outcome = "DIED"

    def decide(self, text: str, walk: list[str], idx: int) -> tuple[str | None, int]:
        """Return (command, next_idx); command is None once terminal/exhausted."""
        if self.outcome:
            return None, idx
        # 2. dwarf present -> fight (the most immediate threat).
        if DWARF in text:
            if self.have_sword:
                self.have_sword = False
                self.need_resword = True
                return "THROW SWORD", idx
            if not self.sword_gone:
                return "GET SWORD", idx
            if self.have_axe:
                self.have_axe = False
                self.need_reaxe = True
                return "THROW AXE", idx
            return "GET AXE", idx
        # 3. re-arm after a throw (no dwarf this turn, but it will be back).
        if self.need_resword and not self.sword_gone:
            return "GET SWORD", idx
        if self.need_reaxe and self.sword_gone and not self.have_axe:
            self.need_reaxe = False
            return "GET AXE", idx
        # 4. lamp dim or out -> refuel before moving on (behind combat/re-arm).
        if LAMP_DIM in text or LAMP_OUT in text:
            self.rubs += 1
            return "RUB LAMP", idx
        # 5. otherwise advance the walkthrough.
        if idx < len(walk):
            return walk[idx], idx + 1
        return None, idx


def load_walkthrough(filepath: str) -> list[str]:
    """A solution file (comma/newline separated commands) as a flat list."""
    raw = open(filepath).read().replace("\n", ",")
    return [c.strip() for c in raw.split(",") if c.strip()]


# --- MODE 7 viewport reconstruction (Beebium screen driver only) --------------

def visible_lines(rows: list[str]) -> list[str]:
    """The non-blank text lines of a screen snapshot, top to bottom.

    Blank rows carry no information for overlap matching (MODE 7 layout puts
    variable blank gaps between messages), so we match on text lines only.

    Input-prompt lines (those starting with ``?``) are collapsed to a bare
    ``?``: the BASIC ``INPUT`` prompt accretes the echoed command (``?`` ->
    ``?N`` -> ``?TAKE LAMP``), so without this the prompt line would never match
    between snapshots and already-seen lines above it would re-appear as "new".
    Echoed input carries no game event, so collapsing it loses nothing. Game
    questions like ``What with?`` do not start with ``?`` and are preserved.
    """
    out: list[str] = []
    for r in rows:
        s = r.rstrip()
        if not s:
            continue
        out.append("?" if s.lstrip().startswith("?") else s)
    return out


def diff_against_transcript(seen: list[str], rows: list[str]) -> list[str]:
    """Append the snapshot's new bottom lines to ``seen`` and return them.

    ``seen`` is the running transcript (mutated in place). We find the largest
    ``k`` such that the last ``k`` logged lines equal the first ``k`` currently
    visible lines; everything visible below that overlap is new. ``k == 0`` (no
    overlap -- a screen clear, or a jump of more than a screenful) treats the
    whole visible text as new.
    """
    cur = visible_lines(rows)
    max_k = min(len(seen), len(cur))
    k = 0
    for kk in range(max_k, 0, -1):                 # prefer the maximal overlap
        if seen[-kk:] == cur[:kk]:
            k = kk
            break
    new = cur[k:]
    seen.extend(new)
    return new
