"""Binding semantics for l-value formal parameters and LOCAL items.

An l-value formal/LOCAL (?A, $A, !A, ...) is bound by-reference onto its memory
cell: the cell's contents are saved on entry, the incoming argument (or default)
assigned into it, and the saved contents restored on every exit -- exactly the
BBC dynamic-scoping the simple-variable case already gets, but onto an arbitrary
address. Each program prints the value seen *inside* the call (the assigned
value) and then *after* it (the restored value).
"""
from conftest import requires_dotnet_toolchain
from owl_basic.analysis import analyse

_ADDR = "A%=&1000:"


@requires_dotnet_toolchain
def test_byte_indirection_formal_binds_and_restores(compile_and_run):
    src = _ADDR + "?A%=7:PROCshow(99):PRINT?A%:END\nDEFPROCshow(?A%):PRINT?A%:ENDPROC\n"
    assert compile_and_run(analyse(src, name="t")).split("\n")[:2] == ["99", "7"]


@requires_dotnet_toolchain
def test_string_indirection_formal_binds_and_restores(compile_and_run):
    # The rheolism shape: a string argument written to the address in the formal.
    src = _ADDR + '$A%="OLD":PROCs("NEW"):PRINT$A%:END\nDEFPROCs($A%):PRINT$A%:ENDPROC\n'
    assert compile_and_run(analyse(src, name="t")).split("\n")[:2] == ["NEW", "OLD"]


@requires_dotnet_toolchain
def test_integer_indirection_formal_binds_and_restores(compile_and_run):
    src = _ADDR + "!A%=11:PROCn(2222):PRINT!A%:END\nDEFPROCn(!A%):PRINT!A%:ENDPROC\n"
    assert compile_and_run(analyse(src, name="t")).split("\n")[:2] == ["2222", "11"]


@requires_dotnet_toolchain
def test_byte_indirection_local_saves_and_restores(compile_and_run):
    src = _ADDR + "?A%=5:PROCl:PRINT?A%:END\nDEFPROCl:LOCAL?A%:?A%=99:PRINT?A%:ENDPROC\n"
    assert compile_and_run(analyse(src, name="t")).split("\n")[:2] == ["99", "5"]


@requires_dotnet_toolchain
def test_simple_variable_formal_still_works(compile_and_run):
    # Regression: the cheap field path is unchanged.
    src = "PROCd(21):END\nDEFPROCd(N):PRINTN*2:ENDPROC\n"
    assert compile_and_run(analyse(src, name="t")).strip() == "42"
