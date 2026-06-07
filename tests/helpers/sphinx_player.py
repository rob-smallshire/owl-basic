"""Drive a compiled Sphinx Adventure and play it under program control.

A published walkthrough lists the treasure route but omits the reactive
"housekeeping" a live player must do as the game's pseudo-random events occur --
killing the dwarf that starts following you, and refuelling the lamp before it
dies. This driver feeds the walkthrough one command at a time, but watches the
game's output and injects those reactions when needed (without consuming a
walkthrough command).

Because BBC BASIC's RND is deterministic from its cold seed and Sphinx never
re-seeds, a cold-started run is fully reproducible -- so a playthrough makes a
reliable, non-flaky test.

Uses select() on the child's stdout to detect when the game has gone quiet and
is waiting for input, so it needs a POSIX platform.
"""

import os
import re
import select
import subprocess


def play(dll_filepath, walkthrough, *, seed=None, max_commands=400,
         idle_seconds=0.3, dwarf_command="THROW SWORD",
         lamp_command="RUB LAMP"):
    """Play a compiled Sphinx assembly through *walkthrough*.

    *seed* None uses the faithful BBC cold seed (deterministic). An int sets
    OWL_RANDOM_SEED to reseed the generator instead. Returns a result dict.
    """
    env = dict(os.environ)
    if seed is None:
        env.pop("OWL_RANDOM_SEED", None)
    else:
        env["OWL_RANDOM_SEED"] = str(seed)

    proc = subprocess.Popen(
        ["dotnet", str(dll_filepath)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=env,
    )

    transcript = []
    rooms = set()
    index = sent = dwarf_kills = lamp_rubs = max_score = 0
    died = crashed = won = False
    # Combat state. The sword kills a dwarf outright but, like any thrown weapon,
    # lands on the floor -- so it is re-collected after each throw. The sword
    # melts when it kills the ogre; after that the axe (60% per throw) is the only
    # option, re-collected each throw (the dwarf keeps dropping fresh ones).
    have_sword = sword_gone = have_axe = need_resword = need_reaxe = False

    def scan(chunk):
        nonlocal dwarf_kills, max_score, won
        dwarf_kills += chunk.count("You killed a dwarf")
        for value in re.findall(r"scored (\d+)", chunk):
            max_score = max(max_score, int(value))
        for line in chunk.splitlines():
            if line.startswith("You are "):
                rooms.add(line.strip())
        low = chunk.lower()
        if "well done" in low and ("solved" in low or "puzzle" in low):
            won = True

    try:
        while sent < max_commands and index < len(walkthrough):
            chunk = _read_until_idle(proc, idle_seconds)
            transcript.append(chunk)
            scan(chunk)
            low = chunk.lower()
            if "you get the sword" in low or "you take the sword" in low:
                have_sword = True
                need_resword = False
            if "melts away" in low:
                have_sword = False
                sword_gone = True
            if "you get the axe" in low or "you take the axe" in low:
                have_axe = True
            if won or "reincarnated" in chunk:    # solved, or an in-game death
                died = "reincarnated" in chunk
                break
            if proc.poll() is not None:           # process exited unexpectedly
                crashed = True
                break
            if "There is a dwarf here" in chunk:
                if have_sword:
                    command = "THROW SWORD"
                    have_sword = False
                    need_resword = True
                elif not sword_gone:
                    command = "GET SWORD"
                elif have_axe:
                    command = "THROW AXE"
                    have_axe = False
                    need_reaxe = True
                else:
                    command = "GET AXE"
            elif need_resword and not sword_gone:
                command = "GET SWORD"
            elif need_reaxe and sword_gone and not have_axe:
                command = "GET AXE"
                need_reaxe = False
            elif "lamp is getting dim" in chunk or "lamp has run out" in chunk:
                command = lamp_command
                lamp_rubs += 1
            else:
                command = walkthrough[index]
                index += 1
            try:
                proc.stdin.write((command + "\n").encode())
                proc.stdin.flush()
            except BrokenPipeError:
                crashed = True
                break
            sent += 1
        # Read the response to the final command (e.g. the winning WAVE WAND),
        # which the loop would otherwise leave unread.
        if not crashed:
            tail = _read_until_idle(proc, idle_seconds)
            transcript.append(tail)
            scan(tail)
        stderr = proc.stderr.read().decode("latin-1") if crashed else ""
    finally:
        proc.kill()
        proc.wait()

    return {
        "transcript": "".join(transcript),
        "commands_used": index,
        "commands_sent": sent,
        "dwarf_kills": dwarf_kills,
        "lamp_rubs": lamp_rubs,
        "rooms_seen": len(rooms),
        "max_score": max_score,
        "won": won,
        "died": died,
        "crashed": crashed,
        "stderr": stderr,
    }


def load_walkthrough(filepath):
    """A solution file (comma/newline separated commands) as a list."""
    text = open(filepath).read().replace("\n", ",")
    return [c.strip() for c in text.split(",") if c.strip()]


def _read_until_idle(proc, idle_seconds):
    """Read stdout until the game stops producing output (blocked on input)."""
    chunks = []
    while True:
        ready, _, _ = select.select([proc.stdout], [], [], idle_seconds)
        if not ready:
            break                                 # quiet -> waiting for input
        data = os.read(proc.stdout.fileno(), 4096)
        if not data:
            break                                 # EOF
        chunks.append(data.decode("latin-1"))
    return "".join(chunks)
