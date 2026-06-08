"""Drive a live, watchable cold-boot Sphinx Adventure playthrough on a Beebium
emulator, reacting to the dwarf and the lamp via the (unit-tested) pure logic in
tools/sphinx_screen.py.

Design notes learned the hard way (see tests/data/SPHINX_ADVENTURE.md and the
beebium issues):

* The emulator FREE-RUNS in real time (it already runs after launch); we only
  inject keys and read the screen via side-effect-free peeks. We never drive it
  through the debugger -- stepping the CPU fights a watching viewer and stops the
  machine, so there is nothing smooth to watch.
* One command at a time: type cmd+RETURN, wait_for_typing() so the BBC actually
  consumes the keys, then wait for the screen to settle before the next command.
  No keystroke pile-up (piling up drops commands and looks stuck).
* Typing is paced reliably by the server (beebium#49, fixed in 5f4aa7e): there is
  no client-side timing knob and no need for verify/retry -- the default pace is
  reliable by construction. We still drain the queue (wait_for_typing) before
  reading the screen back.
* Delta extraction and the reactive policy are the tested pure functions.

Usage:
    # launch our own advertised server and wait for the user to attach + signal:
    uv run python tools/sphinx_beebium_player.py
    # or drive a server that is already running (do not launch / shut it down):
    uv run python tools/sphinx_beebium_player.py --connect localhost:48875
The launch form waits for the signal file (default /tmp/beeb_go) before playing.
"""
import argparse
import re
import sys
import time
from pathlib import Path

from beebium.client import Beebium
from beebium.screen import dump_screen, read_mode7_screen, screen_contains

# The reactive policy and MODE 7 reconstruction live with the OWL autoplayer so
# both drivers share one reviewed, unit-tested implementation. Import the module
# directly (it is self-contained, stdlib-only) rather than via the `helpers`
# package, whose __init__ pulls in owl_basic -- absent in the Beebium venv.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tests" / "helpers"))
from sphinx_events import (  # noqa: E402
    Policy, diff_against_transcript, joined, load_walkthrough,
)

BEEBIUM_REPO = Path("/Users/rjs/Code/beebium")
ROMS = BEEBIUM_REPO / "roms"
DISC = BEEBIUM_REPO / "discs" / "games" / "Disc999-SphinxAdventureFIN.ssd"
SOLUTION = Path(__file__).resolve().parent.parent / "tests" / "data" / "sphinx_solution4.txt"


def _close(a, b):
    """Two screen snapshots differ by at most a couple of cells (cursor flicker)."""
    return sum(1 for x, y in zip("".join(a), "".join(b)) if x != y) <= 2


def _last_text_line(rows):
    """The last non-blank line of a snapshot, right-stripped ('' if none)."""
    for r in reversed(rows):
        if r.rstrip():
            return r.rstrip()
    return ""


def settle(bbc, timeout=3.0, quantum=0.2):
    """Wait (wall-clock) until the scroll-corrected screen stops changing."""
    a = read_mode7_screen(bbc)
    waited = 0.0
    while waited < timeout:
        time.sleep(quantum)
        waited += quantum
        b = read_mode7_screen(bbc)
        if _close(a, b):
            return b
        a = b
    return read_mode7_screen(bbc)


def wait_for_input_prompt(bbc, timeout=12.0, quantum=0.15):
    """Block until the game is blocked in INPUT, ready for a command -- i.e. the
    bottom-most text line ENDS in '?' and the screen has settled.

    Keying on a trailing '?' (not a bare '?' line) is what makes the non-standard
    combat prompts fast: `What with? Your bare hands?`, the follow-up `What with
    then?`, `Do you want to be reincarnated?` etc. all end in '?', so we answer
    them as soon as they appear instead of waiting out the timeout. The stability
    check (`_close`) provides the short settle that covers a prompt printed in
    two parts (e.g. two question marks across lines).

    This -- not "the screen stopped changing" -- is the signal the game has
    finished processing; typing only when it holds prevents one command's keys
    landing on the previous command's still-open input line (the
    `?TAKE STAKERUB LAMP` merge). Returns the settled rows (best-effort on
    timeout)."""
    a = read_mode7_screen(bbc)
    waited = 0.0
    while waited < timeout:
        time.sleep(quantum)
        waited += quantum
        b = read_mode7_screen(bbc)
        if _last_text_line(b).endswith("?") and _close(a, b):
            return b
        a = b
    return read_mode7_screen(bbc)


def send(bbc, cmd):
    """Type one command only when the game is ready, and wait until it is ready
    again (a fresh '?' prompt) before returning."""
    wait_for_input_prompt(bbc)             # don't type into a busy game
    bbc.keyboard.type(cmd + "\r")          # server-paced; no timing knob
    bbc.keyboard.wait_for_typing()         # keys delivered to the matrix
    return wait_for_input_prompt(bbc)      # command processed; ready for the next


def boot_to_opening_room(bbc):
    """Free-run from power-on to the first room ('top of a mountain')."""
    try:
        if not bbc.debugger.is_running:
            bbc.debugger.run()
    except Exception:
        pass
    for _ in range(80):
        if screen_contains(bbc, "A classic adventure") or screen_contains(bbc, "top of a mountain"):
            break
        time.sleep(0.5)
    if not screen_contains(bbc, "top of a mountain"):
        bbc.keyboard.press_escape()
        for _ in range(80):
            if screen_contains(bbc, "top of a mountain"):
                break
            time.sleep(0.5)
    bbc.keyboard.wait_for_typing()


def reroll(bbc, timeout=20.0):
    """From the death prompt ("Do you want to be reincarnated?"), reincarnate and
    then full-restart, keeping the never-reseeded RNG advanced:

        YES  -> reincarnate (consumes RND(5); back at a live game prompt)
        QUIT -> word 20 -> "Press C to continue or R to restart."
        R    -> RUN (re-runs from line 1 without touching the RND seed)

    Leaves the game at the fresh opening room. RUN shows no intro (that lives in
    the loader), so it drops straight to the mountain."""
    bbc.keyboard.type("YES\r")               # reincarnate -> respawn at a '?' prompt
    bbc.keyboard.wait_for_typing()
    wait_for_input_prompt(bbc)
    bbc.keyboard.type("QUIT\r")              # -> the continue/restart prompt
    bbc.keyboard.wait_for_typing()
    waited = 0.0
    while waited < timeout:                   # this prompt does not end in '?'
        if screen_contains(bbc, "restart"):
            break
        time.sleep(0.2)
        waited += 0.2
    bbc.keyboard.type("R")                    # GET reads one key -> RUN (no RETURN)
    bbc.keyboard.wait_for_typing()
    boot_to_opening_room(bbc)                 # wait for the fresh 'top of a mountain'


def play(bbc, walk, max_commands=800, progress_every=15, transcript_filepath=None):
    """Drive the walkthrough with the reactive policy; return a result dict.

    If *transcript_filepath* is given, write an interleaved command/response log
    there incrementally (flushed each turn, so it survives a death/crash) for
    review -- each turn is `> COMMAND` followed by the game's reply, making
    illegal moves ("You can't go that way") easy to find before they scroll off.
    """
    seen: list[str] = []
    policy = Policy()
    transcript_file = open(transcript_filepath, "w") if transcript_filepath else None

    def record(label, lines):
        if transcript_file is None:
            return
        body = [ln for ln in lines if ln.strip() != "?"]   # drop bare input prompts
        transcript_file.write(label + "\n")
        if body:
            transcript_file.write("\n".join(body) + "\n")
        transcript_file.write("\n")
        transcript_file.flush()

    try:
        rows = wait_for_input_prompt(bbc)
        opening = diff_against_transcript(seen, rows)        # opening room
        record("[opening room]", opening)
        text = joined(opening)
        idx = sent = max_score = 0
        while sent < max_commands:
            policy.observe(text)
            if policy.outcome:
                break
            cmd, idx = policy.decide(text, walk, idx)
            if cmd is None:
                break
            new = diff_against_transcript(seen, send(bbc, cmd))
            record(f"> {cmd}", new)
            text = joined(new)
            for hit in re.findall(r"scored (\d+)", text):    # "You have scored N out of 800"
                max_score = max(max_score, int(hit))
            sent += 1
            if sent % progress_every == 0:
                print(f"  ...sent {sent}, idx {idx}/{len(walk)}, "
                      f"kills {policy.kills}, rubs {policy.rubs}", flush=True)
        policy.observe(text)
        for hit in re.findall(r"scored (\d+)", text):
            max_score = max(max_score, int(hit))
    finally:
        if transcript_file is not None:
            transcript_file.close()
    return {"outcome": policy.outcome or "end", "idx": idx, "len": len(walk),
            "sent": sent, "kills": policy.kills, "rubs": policy.rubs,
            "max_score": max_score, "transcript": seen,
            "transcript_filepath": transcript_filepath}


def _report(bbc, result):
    print(f"\nBEEBIUM COLD BOOT (solution4, live on {bbc.target}): "
          f"outcome={result['outcome']} idx={result['idx']}/{result['len']} "
          f"sent={result['sent']} dwarf_kills={result['kills']} lamp_rubs={result['rubs']}",
          flush=True)
    if result.get("transcript_filepath"):
        print(f"interleaved transcript written to {result['transcript_filepath']}", flush=True)
    print(dump_screen(bbc), flush=True)


def run_reroll(bbc, walk, max_attempts, transcript_dirpath):
    """Play from cold; on each death reincarnate + RUN (keeping the advanced,
    never-reseeded RNG) and replay, until a win or max_attempts. Returns the
    per-attempt result dicts; each attempt's transcript is saved separately."""
    summary = []
    for attempt in range(1, max_attempts + 1):
        tpath = (str(Path(transcript_dirpath) / f"attempt_{attempt:02d}.txt")
                 if transcript_dirpath else None)
        print(f"\n===== ATTEMPT {attempt}/{max_attempts} =====", flush=True)
        res = play(bbc, walk, transcript_filepath=tpath)
        res["attempt"] = attempt
        summary.append(res)
        print(f"ATTEMPT {attempt}: outcome={res['outcome']} score={res['max_score']} "
              f"idx={res['idx']}/{res['len']} sent={res['sent']} "
              f"kills={res['kills']} rubs={res['rubs']}"
              + (f"  -> {tpath}" if tpath else ""), flush=True)
        if res["outcome"] == "WON":
            print(f"\n*** WON on attempt {attempt} (score {res['max_score']}) ***", flush=True)
            break
        if res["outcome"] != "DIED":
            print(f"unexpected outcome {res['outcome']!r}; stopping reroll", flush=True)
            break
        if attempt < max_attempts:
            reroll(bbc)
    print("\n===== REROLL SUMMARY =====", flush=True)
    for r in summary:
        print(f"  attempt {r['attempt']:2d}: {r['outcome']:4s} "
              f"score {r['max_score']:3d}  idx {r['idx']}/{r['len']}  "
              f"sent {r['sent']}  kills {r['kills']}  rubs {r['rubs']}", flush=True)
    won = next((r for r in summary if r["outcome"] == "WON"), None)
    print(f"\nRESULT: {'WON on attempt ' + str(won['attempt']) if won else 'no win in ' + str(len(summary)) + ' attempts'}",
          flush=True)
    return summary


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--connect", metavar="TARGET",
                    help="drive an already-running server (e.g. localhost:48875) "
                         "instead of launching one")
    ap.add_argument("--port", type=int, default=48875)
    ap.add_argument("--solution", default=str(SOLUTION),
                    help="solution file to play (default: sphinx_solution4.txt)")
    ap.add_argument("--reroll", action="store_true",
                    help="loop: on death, reincarnate+RUN (advancing the RNG) and "
                         "replay until a win; count attempts, save each transcript")
    ap.add_argument("--max-attempts", type=int, default=15)
    ap.add_argument("--transcript-dir", default="/tmp/sphinx_reroll",
                    help="directory for per-attempt transcripts (reroll mode)")
    ap.add_argument("--go-file", default="/tmp/beeb_go",
                    help="when launching, wait for this file before playing")
    ap.add_argument("--transcript", default="/tmp/sphinx_transcript.txt",
                    help="single-run interleaved command/response log "
                         "(empty string disables)")
    ap.add_argument("--hold", type=float, default=180.0,
                    help="seconds to hold the final screen (launch mode)")
    args = ap.parse_args()
    walk = load_walkthrough(args.solution)
    transcript_filepath = args.transcript or None
    if args.reroll and args.transcript_dir:
        Path(args.transcript_dir).mkdir(parents=True, exist_ok=True)

    if args.connect:
        bbc = Beebium.connect(target=args.connect)
        try:
            bbc.keyboard.wait_for_typing()
            _report(bbc, play(bbc, walk, transcript_filepath=transcript_filepath))
        finally:
            bbc.close()   # connect() owns no server; this only drops the connection
        return

    with Beebium.launch(
        mos_filepath=ROMS / "acorn-mos_1_20.rom",
        basic_filepath=ROMS / "bbc-basic_2.rom",
        extra_args=["--advertise", "--fdc", "acorn-1770",
                    "--sideways", f"14:rom:{ROMS / 'acorn-dfs_2_26.rom'}",
                    "--auto-boot", "--floppy", f"0:{DISC}"],
        port=args.port, startup_timeout=20.0,
    ) as bbc:
        boot_to_opening_room(bbc)
        settle(bbc)
        if args.reroll:
            print(f"REROLL: advertised + free-running on {bbc.target}; attach your "
                  f"viewer any time. Playing from cold, reincarnating on death until "
                  f"a win (max {args.max_attempts}); transcripts in {args.transcript_dir}.",
                  flush=True)
            run_reroll(bbc, walk, args.max_attempts, args.transcript_dir)
            _report(bbc, {"outcome": "reroll-done", "idx": 0, "len": len(walk),
                          "sent": 0, "kills": 0, "rubs": 0})
            print(f"Holding final screen for {args.hold:.0f}s...", flush=True)
            time.sleep(args.hold)
            return
        go = Path(args.go_file)
        print(f"READY: advertised + free-running at the opening room on {bbc.target}. "
              f"opening_room={screen_contains(bbc, 'top of a mountain')}.\n"
              f"Attach your viewer; create {go} to start.", flush=True)
        while not go.exists():
            time.sleep(1.0)
        print("GO received -- playing cold-boot solution4 live.", flush=True)
        _report(bbc, play(bbc, walk, transcript_filepath=transcript_filepath))
        print(f"Holding final screen for {args.hold:.0f}s...", flush=True)
        time.sleep(args.hold)


if __name__ == "__main__":
    main()
