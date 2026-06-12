"""The grid-capturing text screen mode (GridTextScreenMode), reached via the
compile_and_capture_screen fixture. Unlike the streamed console output, this
honours TAB(x,y) cursor positioning, scrolling and carriage return, so the
laid-out text screen can be asserted on -- an aid for checking text formatting.
"""
from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse


@requires_dotnet_toolchain
def test_tab_lays_out_text_on_the_grid(compile_and_capture_screen):
    # TAB(x,y) places text at column x, row y -- not flattened to print order.
    screen = compile_and_capture_screen(analyse(
        'PRINT TAB(0,0);"top"\nPRINT TAB(10,2);"HELLO"\nPRINT TAB(4,4);"down"\nEND\n',
        name="cap_tab"))
    rows = screen.split("\n")
    assert rows[0] == "top"
    assert rows[2] == " " * 10 + "HELLO"
    assert rows[4] == " " * 4 + "down"


@requires_dotnet_toolchain
def test_scrolling_keeps_the_tail(compile_and_capture_screen):
    # Printing past the bottom of the 25-row screen scrolls; the grid keeps the
    # final tail, with the earliest lines scrolled off the top.
    screen = compile_and_capture_screen(analyse(
        'FOR I% = 1 TO 30\nPRINT "line ";I%\nNEXT\nEND\n', name="cap_scroll"))
    rows = [r for r in screen.split("\n") if r]
    assert rows[-1] == "line 30"
    assert len(rows) <= 25
    assert "line 1" not in rows          # scrolled off the top


@requires_dotnet_toolchain
def test_carriage_return_overwrites_in_place(compile_and_capture_screen):
    # A bare CR returns to column 0 without moving down, so the following text
    # overwrites: "abcde" + CR + "XY" -> "XYcde".
    screen = compile_and_capture_screen(analyse(
        'PRINT "abcde";CHR$(13);"XY"\nEND\n', name="cap_cr"))
    assert screen.split("\n")[0] == "XYcde"


@requires_dotnet_toolchain
def test_mode_command_resizes_the_screen(compile_and_capture_screen):
    # The default is MODE 7 (40x25); MODE 1 is 40x32, so row 30 becomes
    # reachable. The program's own MODE command drives the geometry.
    screen = compile_and_capture_screen(analyse(
        'MODE 1\nPRINT TAB(0,30);"low"\nEND\n', name="cap_mode"))
    assert screen.split("\n")[30] == "low"


@requires_dotnet_toolchain
def test_screen_size_env_sets_initial_geometry(compile_and_capture_screen):
    # OWL_SCREEN_SIZE sets the initial size as WxH, so column 70 is reachable.
    screen = compile_and_capture_screen(analyse(
        'PRINT TAB(70,0);"X"\nEND\n', name="cap_env"), screen_size="80x40")
    assert screen.split("\n")[0] == " " * 70 + "X"


@requires_dotnet_toolchain
def test_screen_size_env_accepts_mode_form(compile_and_capture_screen):
    # OWL_SCREEN_SIZE may also name a mode: MODE 0 is 80x32.
    screen = compile_and_capture_screen(analyse(
        'PRINT TAB(60,0);"Y"\nEND\n', name="cap_envmode"), screen_size="MODE0")
    assert screen.split("\n")[0] == " " * 60 + "Y"
