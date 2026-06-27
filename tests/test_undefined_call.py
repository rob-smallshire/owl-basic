"""A call to an undefined PROC/FN is diagnosed -- even with no arguments.

The "Call to undefined ..." diagnostic used to live only on the argument-checking
path, so a *no-argument* call to a missing routine (PROCclock, FNfoo) was never
flagged: it passed analysis and the backend then emitted a call to a method that
does not exist (ilasm: "unresolved global member ref"). Now every call is
checked, so an incomplete program (e.g. an overlay whose helpers live elsewhere)
is rejected cleanly instead of producing invalid IL. Surfaced by Acorn User
Tau87-b/AUG87.JJ5 (calls an undefined PROCclock).
"""
import pytest

from owl_basic.analysis import analyse
from owl_basic.exceptions import OwlBasicError


def _undefined_diagnostics(source):
    program = analyse(source, name="t")
    return [d for d in (getattr(program, "diagnostics", None) or [])
            if "undefined" in d.lower()]


def test_undefined_no_arg_procedure_is_diagnosed():
    diags = _undefined_diagnostics("PROCclock\nEND\n")
    assert any("PROCclock" in d for d in diags)


def test_undefined_no_arg_function_is_diagnosed():
    diags = _undefined_diagnostics("x=FNfoo\nEND\n")
    assert any("FNfoo" in d for d in diags)


def test_undefined_procedure_with_args_still_diagnosed():
    diags = _undefined_diagnostics('PROCsave("x")\nEND\n')
    assert any("PROCsave" in d for d in diags)


def test_undefined_no_arg_call_refuses_codegen(dotnet_backend):
    # The point: a missing routine is a clean compile error, not invalid IL.
    with pytest.raises(OwlBasicError):
        dotnet_backend.emit_il(analyse("PROCclock\nEND\n", name="t"))


def test_defined_no_arg_procedure_compiles(dotnet_backend):
    # A defined no-argument PROC is unaffected -- no false positive.
    il = dotnet_backend.emit_il(analyse(
        'PROCgo\nEND\nDEFPROCgo\nPRINT "hi"\nENDPROC\n', name="t"))
    assert il
