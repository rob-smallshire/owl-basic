"""Pure-logic tests for the shared Sphinx driving logic (helpers/sphinx_events).

Emulator-free and OWL-free, so they run everywhere (no dotnet, no Beebium).
Screen text uses the real MODE 7 wording captured from Sphinx Adventure.
"""
from helpers.sphinx_events import (
    Policy, diff_against_transcript, joined, visible_lines,
)

ROWS = 25


def screen(*lines):
    """A 25-row snapshot with `lines` bottom-anchored (as MODE 7 fills/scrolls)."""
    lines = list(lines)
    assert len(lines) <= ROWS
    return [""] * (ROWS - len(lines)) + lines


# --- transcript reconstruction -------------------------------------------------

def test_fill_in_then_scroll_recovers_each_new_block():
    seen = []
    s1 = screen("You are on the top of a mountain.",
                "There are exits north, south, east and west.", "?")
    assert diff_against_transcript(seen, s1) == [
        "You are on the top of a mountain.",
        "There are exits north, south, east and west.", "?"]
    s2 = screen("There are exits north, south, east and west.", "?N",
                "You are walking along a road.", "There is an exit east.", "?")
    # The echoed prompt ("?N") collapses to "?" and anchors the overlap, so only
    # the genuinely new room text comes back.
    assert diff_against_transcript(seen, s2) == [
        "You are walking along a road.", "There is an exit east.", "?"]


def test_no_change_yields_no_new_lines():
    seen = []
    s = screen("You are in a cave.", "?")
    diff_against_transcript(seen, s)
    assert diff_against_transcript(seen, list(s)) == []


def test_screen_clear_or_big_jump_treats_all_as_new():
    seen = ["something old", "and older"]
    s = screen("Totally different content.", "?")
    assert diff_against_transcript(seen, s) == ["Totally different content.", "?"]


def test_changing_prompt_echo_is_not_re_emitted():
    seen = []
    diff_against_transcript(seen, screen("You are in a cell.", "?"))
    assert diff_against_transcript(seen, screen("You are in a cell.", "?GET KEY")) == []


def test_joined_stitches_wrapped_message():
    wrapped = ["There is a dwarf here. He throws an axe", "at you, it gets you!"]
    assert "there is a dwarf here. he throws an axe at you, it gets you!" in joined(wrapped)


def test_visible_lines_drops_blanks():
    assert visible_lines(["", "a", "", "b ", ""]) == ["a", "b"]


def test_visible_lines_collapses_echoed_prompt_but_keeps_questions():
    assert visible_lines(["?TAKE LAMP", "What with?"]) == ["?", "What with?"]


# --- reactive policy: priority ordering (death-avoidance first) ----------------

def test_dwarf_is_fought_even_when_the_lamp_is_dim():
    p = Policy(have_sword=True)
    text = joined(["There is a dwarf here.", "Your lamp is getting dim.", "?"])
    p.observe(text)
    cmd, idx = p.decide(text, ["N"], 0)
    assert cmd == "THROW SWORD"        # combat beats refuelling
    assert p.rubs == 0 and idx == 0


def test_dwarf_is_fought_even_when_the_lamp_has_run_out():
    p = Policy(have_sword=True)
    text = joined(["It is dark.", "Your lamp has run out.",
                   "There is a dwarf here.", "?"])
    p.observe(text)
    cmd, _ = p.decide(text, ["N"], 0)
    assert cmd == "THROW SWORD"        # the dwarf can kill this turn; lamp can wait


def test_rearming_beats_refuelling():
    # Just threw the sword (no dwarf this turn) AND the lamp is dim: re-arm first
    # so we can fight the dwarf that follows, then rub next turn.
    p = Policy(need_resword=True)
    text = joined(["You are in a hall.", "Your lamp is getting dim.", "?"])
    p.observe(text)
    cmd, _ = p.decide(text, ["N"], 0)
    assert cmd == "GET SWORD"


# --- reactive policy: the lamp (when nothing more urgent) ----------------------

def test_rubs_lamp_on_the_next_command_when_dim_and_safe():
    p = Policy()
    walk = ["N", "E"]
    cmd, idx = p.decide(joined(["You are in a field.", "?"]), walk, 0)
    assert cmd == "N"
    text = joined(["You are in a dark passage.", "Your lamp is getting dim.", "?"])
    p.observe(text)
    cmd, idx = p.decide(text, walk, idx)
    assert cmd == "RUB LAMP" and idx == 1 and p.rubs == 1   # walk did not advance
    cmd, idx = p.decide(joined(["The lamp is now bright.", "?"]), walk, idx)
    assert cmd == "E"


def test_rubs_lamp_when_run_out_and_no_dwarf():
    p = Policy()
    text = joined(["It is dark.", "Your lamp has run out.", "?"])
    p.observe(text)
    cmd, _ = p.decide(text, ["N"], 0)
    assert cmd == "RUB LAMP"


# --- reactive policy: the dwarf -----------------------------------------------

def test_dwarf_fight_with_sword_then_rearm():
    p = Policy(have_sword=True)
    text = joined(["There is a dwarf here. He throws an axe", "at you, it misses.", "?"])
    p.observe(text)
    cmd, idx = p.decide(text, ["N"], 0)
    assert cmd == "THROW SWORD" and p.need_resword and idx == 0
    cmd, idx = p.decide(joined(["You are in a hall.", "?"]), ["N"], 0)
    assert cmd == "GET SWORD"          # re-collect when the dwarf is gone
    p.observe(joined(["You take the sword.", "?"]))
    assert p.have_sword and not p.need_resword


def test_after_ogre_dwarf_is_fought_with_the_axe():
    p = Policy()
    p.observe(joined(["The sword melts away.", "?"]))     # ogre killed
    assert p.sword_gone
    p.have_axe = True
    text = joined(["There is a dwarf here.", "?"])
    p.observe(text)
    cmd, _ = p.decide(text, ["N"], 0)
    assert cmd == "THROW AXE" and p.need_reaxe


def test_dwarf_with_no_weapon_yet_collects_one():
    p = Policy()
    text = joined(["There is a dwarf here.", "?"])
    cmd, _ = p.decide(text, ["N"], 0)
    assert cmd == "GET SWORD"


# --- reactive policy: terminal + ordinary -------------------------------------

def test_normal_turn_advances_the_walkthrough():
    p = Policy()
    walk = ["TAKE LAMP", "S", "E"]
    cmd, idx = p.decide(joined(["A small building.", "?"]), walk, 0)
    assert cmd == "TAKE LAMP" and idx == 1


def test_terminal_states_stop_the_driver():
    p = Policy()
    p.observe(joined(["You've solved the puzzle!", "?"]))
    assert p.outcome == "WON"
    assert p.decide("anything", ["N"], 0) == (None, 0)

    q = Policy()
    q.observe(joined(["You have been killed !", "Do you want to be reincarnated", "?"]))
    assert q.outcome == "DIED"


def test_kill_counter_accumulates():
    p = Policy()
    p.observe(joined(["You killed a dwarf!", "?"]))
    p.observe(joined(["You killed a dwarf!", "?"]))
    assert p.kills == 2
