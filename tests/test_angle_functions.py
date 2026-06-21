"""PI, RAD and DEG -- the angle constant and conversion builtins.

PI is the constant; RAD(x) converts degrees to radians (x * PI / 180) and DEG(x)
the reverse (x * 180 / PI). None had a codegen lowering, so any program using
them failed to compile (e.g. the recursive-fractal corpus programs, which use
RAD). Implemented together since RAD/DEG are defined in terms of PI.
"""
import pytest

from owl_basic.analysis import analyse
from owl_basic.ext.backends.dotnet.emitter import emit_program
from conftest import requires_dotnet_toolchain

PI = 3.141592653589793


def _lowers(source):
    return emit_program(analyse(source, name="t"), "t")


# -- codegen: they lower at all (toolchain-free) ---------------------------

def test_pi_lowers():
    assert "ldc.r8" in _lowers("PRINT PI\n")


def test_rad_lowers():
    _lowers("X=RAD(180)\nEND\n")  # was CodeGenerationError 'RadFunc'


def test_deg_lowers():
    _lowers("X=DEG(3)\nEND\n")  # was CodeGenerationError 'DegFunc'


# -- runtime: correct values ------------------------------------------------

def _value(compile_and_run, expr):
    return float(compile_and_run(analyse("PRINT %s\n" % expr, name="t")).strip())


@requires_dotnet_toolchain
def test_pi_value(compile_and_run):
    assert abs(_value(compile_and_run, "PI") - PI) < 1e-6


@requires_dotnet_toolchain
def test_rad_converts_degrees_to_radians(compile_and_run):
    assert abs(_value(compile_and_run, "RAD(180)") - PI) < 1e-6
    assert abs(_value(compile_and_run, "RAD(90)") - PI / 2) < 1e-6


@requires_dotnet_toolchain
def test_deg_converts_radians_to_degrees(compile_and_run):
    assert abs(_value(compile_and_run, "DEG(PI)") - 180.0) < 1e-4
    assert abs(_value(compile_and_run, "DEG(PI/2)") - 90.0) < 1e-4


@requires_dotnet_toolchain
def test_rad_and_deg_round_trip(compile_and_run):
    assert abs(_value(compile_and_run, "DEG(RAD(57))") - 57.0) < 1e-3
