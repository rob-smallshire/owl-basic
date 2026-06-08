"""Drive a compiled Sphinx Adventure and play it under program control.

A published walkthrough lists the treasure route but omits the reactive
"housekeeping" a live player must do as the game's pseudo-random events occur --
killing the dwarf that starts following you, and refuelling the lamp before it
dies. This driver feeds the walkthrough one command at a time, but watches the
game's output and injects those reactions when needed (without consuming a
walkthrough command). The reaction logic itself is the shared, unit-tested
``Policy`` in helpers/sphinx_events.py -- the same policy the Beebium screen
driver uses.

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

from .sphinx_events import Policy, joined, load_walkthrough


def play(dll_filepath, walkthrough, *, seed=None, max_commands=400,
         idle_seconds=0.3):
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
    index = sent = max_score = 0
    crashed = False
    policy = Policy()

    def scan(chunk):
        nonlocal max_score
        for value in re.findall(r"scored (\d+)", chunk):
            max_score = max(max_score, int(value))
        for line in chunk.splitlines():
            if line.startswith("You are "):
                rooms.add(line.strip())

    try:
        while sent < max_commands and index < len(walkthrough):
            chunk = _read_until_idle(proc, idle_seconds)
            transcript.append(chunk)
            scan(chunk)
            text = joined(chunk.splitlines())
            policy.observe(text)
            if policy.outcome:                    # solved, or an in-game death
                break
            if proc.poll() is not None:           # process exited unexpectedly
                crashed = True
                break
            command, index = policy.decide(text, walkthrough, index)
            if command is None:
                break
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
            policy.observe(joined(tail.splitlines()))
        stderr = proc.stderr.read().decode("latin-1") if crashed else ""
    finally:
        proc.kill()
        proc.wait()

    return {
        "transcript": "".join(transcript),
        "commands_used": index,
        "commands_sent": sent,
        "dwarf_kills": policy.kills,
        "lamp_rubs": policy.rubs,
        "rooms_seen": len(rooms),
        "max_score": max_score,
        "won": policy.outcome == "WON",
        "died": policy.outcome == "DIED",
        "crashed": crashed,
        "stderr": stderr,
    }


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
