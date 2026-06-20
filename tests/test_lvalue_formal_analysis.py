"""Analysis (not just parsing) must cope with lvalue formals and LOCALs.

An indirection (?A, $A) or array-element (A(i)) formal/LOCAL introduces no named
variable -- it is a window onto existing storage that codegen saves and restores
-- so symbol-table construction must skip it rather than assume a ``.identifier``.
"""
from owl_basic.analysis import analyse
from owl_basic.codegen.backend import Program


def test_analyse_string_indirection_formal():
    # The rheolism case: DEF FNd(X, $@%) -- X is a named formal, $@% is not.
    assert isinstance(analyse("DEFFNd(X,$@%)=1\n", name="d"), Program)


def test_analyse_byte_indirection_local():
    assert isinstance(
        analyse("DEFPROCp:LOCAL?A:?A=5:ENDPROC\n", name="p"), Program
    )


def test_analyse_array_element_formal():
    assert isinstance(
        analyse("DIMb(9):DEFFNg(b(3))=1\n", name="g"), Program
    )


def test_analyse_simple_variable_formal_still_works():
    assert isinstance(analyse("DEFFNs(A)=A\n", name="s"), Program)
