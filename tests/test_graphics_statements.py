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
