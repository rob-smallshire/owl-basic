"""Graphics/text VDU statements wired from the compiler to the OwlRuntime VDU
system (issue #3): COLOUR, CLS, and -- as they land -- GCOL, MOVE, DRAW, PLOT,
VDU. In the headless text path colour is a no-op, but the statements must lower
to the runtime calls and the program must run; CLS and cursor effects are
checked against the captured screen grid.
"""
from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse


@requires_dotnet_toolchain
def test_colour_then_print_runs(compile_and_run):
    # COLOUR sets the text colour (a no-op headless); the program still runs.
    out = compile_and_run(analyse('COLOUR 2\nPRINT "hi"\nCOLOUR 1\nPRINT "bye"\nEND\n',
                                  name="col"))
    assert out.splitlines() == ["hi", "bye"]


@requires_dotnet_toolchain
def test_cls_clears_the_screen(compile_and_capture_screen):
    # CLS clears the screen and homes the cursor, so only post-CLS text remains.
    screen = compile_and_capture_screen(analyse(
        'PRINT "before"\nCLS\nPRINT "after"\nEND\n', name="clsg"))
    assert screen.split("\n")[0] == "after"
    assert "before" not in screen


def test_emit_il_lowers_colour_and_cls(dotnet_backend):
    il = dotnet_backend.emit_il(analyse('COLOUR 2\nCLS\nEND\n', name="colil"))
    assert "Colour(int32)" in il
    assert "::Cls()" in il


@requires_dotnet_toolchain
def test_graphics_primitives_run(compile_and_run):
    # GCOL/MOVE/DRAW/PLOT lower and run in the headless path (drawing is a no-op
    # in the text screen modes, but the statements execute cleanly).
    out = compile_and_run(analyse(
        'GCOL 0,2\nMOVE 100,100\nDRAW 200,200\nPLOT 21,300,150\nPRINT "ok"\nEND\n',
        name="gfx"))
    assert out.splitlines() == ["ok"]


@requires_dotnet_toolchain
def test_draw_with_real_coordinates(compile_and_run):
    # DRAW with a real-valued coordinate (i%*dx style) narrows to integer.
    out = compile_and_run(analyse(
        'DX = 12.5\nMOVE 0,0\nDRAW 3*DX, 50\nPRINT "drawn"\nEND\n', name="gfxf"))
    assert out.splitlines() == ["drawn"]


def test_emit_il_lowers_graphics_primitives(dotnet_backend):
    il = dotnet_backend.emit_il(analyse(
        'GCOL 0,2\nMOVE 100,100\nDRAW 200,200\nPLOT 21,300,150\nEND\n', name="gfxil"))
    assert "Gcol(int32, int32)" in il
    assert "Plot(int32, int32, int32)" in il
    assert "ldc.i4 4" in il      # MOVE -> PLOT 4
    assert "ldc.i4 5" in il      # DRAW -> PLOT 5


@requires_dotnet_toolchain
def test_vdu_control_sequence_runs(compile_and_run):
    # VDU 23,1,0;0;0;0; (cursor off): bytes via ',' and 16-bit words via ';'.
    out = compile_and_run(analyse('VDU 23,1,0;0;0;0;\nPRINT "ok"\nEND\n', name="vdu"))
    assert out.splitlines() == ["ok"]


@requires_dotnet_toolchain
def test_vdu_prints_characters(compile_and_capture_screen):
    # VDU n (n >= 32) sends the character to the screen.
    screen = compile_and_capture_screen(analyse('VDU 65,66,67\nEND\n', name="vduc"))
    assert screen.split("\n")[0] == "ABC"


def test_emit_il_lowers_vdu_bytes_and_words(dotnet_backend):
    il = dotnet_backend.emit_il(analyse('VDU 23,1,0;0;0;0;\nEND\n', name="vduil"))
    assert "Vdu(uint8)" in il     # the ',' byte items (23, 1)
    assert "Vdu(int16)" in il      # the ';' word items (0;0;0;0;)
