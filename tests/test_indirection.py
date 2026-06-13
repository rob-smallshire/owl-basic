"""Indirection operators used as r-values (in expressions), not just as
assignment targets. The unary forms (?addr, !addr) parsed only as l-values;
reading them in an expression -- as ragged-num.bbctxt does heavily, e.g.
IF ?(text% + p%) <> spc% -- failed to parse. One focused test per construct.
"""
from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse


@requires_dotnet_toolchain
def test_unary_byte_indirection_as_rvalue(compile_and_run):
    # ?addr read back in an expression (here straight into PRINT).
    out = compile_and_run(analyse(
        "DIM B% 8\n?B% = 65\nPRINT ?B%\nEND\n", name="ind_qr"))
    assert out.splitlines() == ["65"]


@requires_dotnet_toolchain
def test_unary_byte_indirection_of_expression_as_rvalue(compile_and_run):
    # The address may be a parenthesised expression: ?(base + offset).
    out = compile_and_run(analyse(
        "DIM B% 8\n?(B% + 3) = 200\nPRINT ?(B% + 3)\nEND\n", name="ind_qexpr"))
    assert out.splitlines() == ["200"]
