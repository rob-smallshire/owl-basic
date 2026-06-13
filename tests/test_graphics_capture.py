"""Windowless SkiaSharp graphics capture (OWL_CAPTURE_GRAPHICS -> PNG), the
first slice of the graphics port. A graphics MODE renders the line primitives
with SkiaSharp into an off-screen surface and writes a PNG on exit; these tests
assert on the rendered pixels.

BBC graphics use a 1280x1024 logical space with the origin bottom-left (y up);
the capture flips y, so a line drawn from BBC (0,0) runs from the bottom-left of
the image.
"""
from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse


def _reddish(pixel):
    r, g, b, _ = pixel
    return r > 200 and g < 70 and b < 70


def _whitish(pixel):
    r, g, b, _ = pixel
    return r > 200 and g > 200 and b > 200


def _yellowish(pixel):
    r, g, b, _ = pixel
    return r > 200 and g > 200 and b < 70


@requires_dotnet_toolchain
def test_capture_is_the_logical_size(compile_and_capture_graphics):
    image = compile_and_capture_graphics(analyse(
        'MODE 1\nMOVE 0,0\nDRAW 100,100\nEND\n', name="gsize"))
    assert image.size == (1280, 1024)


@requires_dotnet_toolchain
def test_draws_a_coloured_line(compile_and_capture_graphics):
    # GCOL 0,1 is red in MODE 1; the diagonal passes through the centre. A point
    # well off the line stays the black background.
    image = compile_and_capture_graphics(analyse(
        'MODE 1\nGCOL 0,1\nMOVE 0,0\nDRAW 1279,1023\nEND\n', name="gline"))
    assert _reddish(image.getpixel((640, 512)))            # on the diagonal
    assert image.getpixel((50, 50))[:3] == (0, 0, 0)       # background


@requires_dotnet_toolchain
def test_gcol_selects_the_palette_colour(compile_and_capture_graphics):
    # A horizontal red line low on screen and a white one high on screen; check
    # each lands in its colour. BBC y=100 is near the bottom of the image,
    # y=900 near the top.
    image = compile_and_capture_graphics(analyse(
        'MODE 1\n'
        'GCOL 0,1\nMOVE 0,100\nDRAW 1279,100\n'
        'GCOL 0,3\nMOVE 0,900\nDRAW 1279,900\n'
        'END\n', name="gpal"))
    assert _reddish(image.getpixel((640, 1024 - 100)))     # red line, low
    assert _whitish(image.getpixel((640, 1024 - 900)))     # white line, high


@requires_dotnet_toolchain
def test_plot_three_argument_form(compile_and_capture_graphics):
    # PLOT mode,x,y: a horizontal yellow datum line across the middle. Regression
    # for the grammar that scrambled the three PLOT arguments.
    image = compile_and_capture_graphics(analyse(
        'MODE 1\nGCOL 0,2\nMOVE 0,512\nPLOT 21,1280,512\nEND\n', name="gplot3"))
    assert _yellowish(image.getpixel((640, 512)))


@requires_dotnet_toolchain
def test_text_renders_in_a_graphics_mode(compile_and_capture_graphics):
    # PRINT in a graphics mode draws the text in the current text colour
    # (COLOUR 2 is yellow); look for a yellow glyph pixel in the cell band.
    image = compile_and_capture_graphics(analyse(
        'MODE 1\nCOLOUR 2\nPRINT TAB(2,2);"HI"\nEND\n', name="gtext"))
    band = [image.getpixel((x, y)) for y in range(64, 96) for x in range(64, 160)]
    assert any(_yellowish(p) for p in band)
