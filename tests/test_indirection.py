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


@requires_dotnet_toolchain
def test_dyadic_byte_indirection_agrees_with_unary_of_sum(compile_and_run):
    # The dyadic byte operator is defined as base?offset == ?(base + offset):
    # the two spellings must address the same byte. Cross them over so a write
    # through one form is read back through the other, in both directions.
    out = compile_and_run(analyse(
        "DIM B% 16\n"
        "B%?3 = 200\n"           # write dyadic
        "PRINT ?(B% + 3)\n"      # read unary-of-sum -> 200
        "?(B% + 7) = 123\n"      # write unary-of-sum
        "PRINT B%?7\n"           # read dyadic -> 123
        "END\n", name="ind_equiv"))
    assert out.splitlines() == ["200", "123"]
