"""Division by zero: a deliberate speed-for-fidelity divergence from BBC BASIC.

On a real BBC, ``1/0``, ``1 DIV 0`` and ``1 MOD 0`` all raise "Division by zero".
OWL keeps that for the *integer* operators -- ``DIV`` and ``MOD`` lower to raw
CIL ``div``/``rem``, which throw ``System.DivideByZeroException`` (caught by
ON ERROR; see ``test_on_error.py::test_on_error_catches_a_clr_division_by_zero``)
-- but deliberately NOT for floating-point ``/``. ``/`` lowers to CIL float
division, which returns Infinity, and a zero-check on *every* division was
judged too costly. So ``1/0`` yields Infinity rather than erroring.

This is intentional. The test pins it so it is not "fixed" by accident.
It is catalogued in docs/divergences.md (entry 1).
"""
from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse


@requires_dotnet_toolchain
def test_float_division_by_zero_yields_infinity_not_an_error(compile_and_run):
    # `/` is floating-point division; 1/0 -> +Infinity, no error, so the program
    # runs straight on to print "ok". (A real BBC would stop with "Division by
    # zero" here -- OWL trades that fidelity for not checking every division.)
    out = compile_and_run(analyse('A = 1/0\nPRINT "ok"\nEND\n', name="fdz"))
    assert out.splitlines()[-1] == "ok"
