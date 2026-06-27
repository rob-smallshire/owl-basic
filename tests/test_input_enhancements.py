"""INPUT with array-element targets and cursor-positioning prompt items.

INPUT lowering handled only plain scalar targets and string/manipulator prompts,
so the common forms INPUT A(i) (read into an array element) and INPUT TAB(x,y)
"prompt" var (position the cursor first, as PRINT does) could not be compiled.
Both are now supported, reusing the array-element store and PRINT's TAB/SPC
lowering.
"""
from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse


@requires_dotnet_toolchain
def test_input_into_numeric_array_element(compile_and_run):
    out = compile_and_run(analyse('DIM A(5)\nINPUT A(2)\nPRINT A(2)\n', name="t"),
                          stdin="42\n")
    assert out.rstrip().endswith("42")


@requires_dotnet_toolchain
def test_input_into_string_array_element(compile_and_run):
    out = compile_and_run(analyse('DIM N$(5)\nINPUT N$(3)\nPRINT N$(3)\n', name="t"),
                          stdin="Bob\n")
    assert out.rstrip().endswith("Bob")


@requires_dotnet_toolchain
def test_input_two_dim_array_element(compile_and_run):
    out = compile_and_run(analyse('DIM G(3,3)\nINPUT G(1,2)\nPRINT G(1,2)\n', name="t"),
                          stdin="7\n")
    assert out.rstrip().endswith("7")


@requires_dotnet_toolchain
def test_input_run_of_array_elements(compile_and_run):
    out = compile_and_run(
        analyse('DIM A(3)\nINPUT A(1),A(2)\nPRINT A(1)+A(2)\n', name="t"),
        stdin="3,4\n")
    assert out.rstrip().endswith("7")


@requires_dotnet_toolchain
def test_input_tab_xy_positions_then_reads(compile_and_run):
    out = compile_and_run(analyse('INPUT TAB(5,5)a$\nPRINT a$\n', name="t"),
                          stdin="hi\n")
    assert out.rstrip().endswith("hi")


@requires_dotnet_toolchain
def test_input_tab_h_positions_then_reads(compile_and_run):
    out = compile_and_run(analyse('INPUT TAB(8)n%\nPRINT n%\n', name="t"),
                          stdin="9\n")
    assert out.rstrip().endswith("9")


@requires_dotnet_toolchain
def test_input_spc_then_reads(compile_and_run):
    out = compile_and_run(analyse('INPUT SPC(4)n%\nPRINT n%\n', name="t"),
                          stdin="5\n")
    assert out.rstrip().endswith("5")
