"""The l-value-parameter catalogue from the BBC BASIC II annotation docs
(acornaeology bbc-basic/docs/analysis/basic-2/indirection-lvalue-parameters.md),
run through OWL against the ROM-accurate golden output recorded there.

Each program sets a location to a "before" value, calls a function whose formal
parameter *is* that location, observes the argument inside the body, then sees
the location restored afterwards. They double as committed corpus fixtures
(lvalue_param_*.bbctxt), to be cross-checked against an emulator in due course.
"""
from conftest import requires_dotnet_toolchain
from helpers import analyse_fixture


@requires_dotnet_toolchain
def test_scalar_parameter(compile_and_run):
    out = compile_and_run(analyse_fixture("lvalue_param_scalar.bbctxt"))
    assert out.split("\n")[:1] == ["49"]


@requires_dotnet_toolchain
def test_array_element_parameter(compile_and_run):
    out = compile_and_run(analyse_fixture("lvalue_param_array_element.bbctxt"))
    assert out.split("\n")[:3] == ["before: 10 20 30", "inside: 10 99 30", "after:  10 20 30"]


@requires_dotnet_toolchain
def test_byte_indirection_parameter(compile_and_run):
    out = compile_and_run(analyse_fixture("lvalue_param_byte_indirection.bbctxt"))
    assert out.split("\n")[:2] == ["inside ?buf% = 65", "after  ?buf% = 99"]


@requires_dotnet_toolchain
def test_string_indirection_parameter(compile_and_run):
    out = compile_and_run(analyse_fixture("lvalue_param_string_indirection.bbctxt"))
    assert out.split("\n")[:3] == ["inside = WORLD", "length = 5", "after  = hello"]


@requires_dotnet_toolchain
def test_word_indirection_parameter(compile_and_run):
    out = compile_and_run(analyse_fixture("lvalue_param_word_indirection.bbctxt"))
    assert out.split("\n")[:2] == ["inside !buf% = AABBCCDD", "after  !buf% = 12345678"]
