"""@% print-format control: numeric (packed control word) and string (printf
-style) forms, wired from the BASIC @% pseudo-variable to the runtime's
PrintManager format state.

@% is a 4-byte word: byte 4 = STR$ switch, byte 3 = format (0=G, 1=E, 2=F),
byte 2 = precision/digit count, byte 1 = field width. The string form is
[+]A x.y, where x/y are field-width/digits in G and E, and swap (decimals/
field-width) in F.
"""
from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse


# --- numeric (packed control word) form -----------------------------------

@requires_dotnet_toolchain
def test_general_format_precision(compile_and_run):
    # Byte 2 is the significant-figure count in G (general) format.
    out = compile_and_run(analyse(
        "@% = &00000305\nPRINT 1/3\n@% = &00000605\nPRINT 1/3\nEND\n", name="atg"))
    assert out.splitlines() == ["0.333", "0.333333"]


@requires_dotnet_toolchain
def test_fixed_format_decimal_places(compile_and_run):
    # Byte 3 = 2 selects fixed-point; byte 2 is the number of decimal places.
    out = compile_and_run(analyse(
        "@% = &00020200\nPRINT 3.14159\nPRINT 2.5\nEND\n", name="atf"))
    assert out.splitlines() == ["3.14", "2.50"]


@requires_dotnet_toolchain
def test_reads_back_the_control_word(compile_and_run):
    # Reading @% returns the packed word; here &00020200 = 131584. (Restore a
    # plain format before printing it, so @% does not reformat its own value.)
    out = compile_and_run(analyse(
        "@% = &00020200\nA% = @%\n@% = &0000090A\nPRINT A%\nEND\n", name="atrd"))
    assert out.splitlines() == ["131584"]


# --- string (printf-style) form -------------------------------------------

@requires_dotnet_toolchain
def test_string_form_general(compile_and_run):
    # @% = "Gx.y": x = field width, y = significant figures.
    out = compile_and_run(analyse(
        '@% = "G3.6"\nPRINT 1/3\nEND\n', name="ats_g"))
    assert out.splitlines() == ["0.333333"]


@requires_dotnet_toolchain
def test_string_form_fixed(compile_and_run):
    # @% = "Fx.y": in F the fields swap -- x = decimal places, y = field width.
    out = compile_and_run(analyse(
        '@% = "F2.5"\nPRINT 3.14159\nEND\n', name="ats_f"))
    assert out.splitlines() == ["3.14"]


# --- wiring (emitter) -----------------------------------------------------

def test_emit_il_routes_at_percent_to_runtime(dotnet_backend):
    il = dotnet_backend.emit_il(analyse("@% = &90A\nA% = @%\nEND\n", name="atil"))
    assert "set_AtPercent(int32)" in il
    assert "get_AtPercent()" in il
