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
    died = crashed = False
    try:
        while sent < max_commands and index < len(walkthrough):
            chunk = _read_until_idle(proc, idle_seconds)
            transcript.append(chunk)
            dwarf_kills += chunk.count("You killed a dwarf")
            for value in re.findall(r"scored (\d+)", chunk):
                max_score = max(max_score, int(value))
            for line in chunk.splitlines():
                if line.startswith("You are "):
                    rooms.add(line.strip())
            if "reincarnated" in chunk:           # an in-game death
                died = True
                break
            if proc.poll() is not None:           # process exited unexpectedly
                crashed = True
                break
            if "There is a dwarf here" in chunk:
                command = dwarf_command
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
