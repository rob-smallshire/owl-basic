"""Array initialiser lists, and the MOUSE ON/OFF (pointer) / ELLIPSE stubs.

* ``A() = e0, e1, ...`` (BASIC V) assigns successive elements A(0)=e0, A(1)=e1,
  ... -- now lowered (it was a codegen gap).
* MOUSE ON/OFF (the mouse pointer) and ELLIPSE are graphics statements with no
  backend lowering; like the other graphics statements they lower to a loud
  deferred runtime stub, so the program compiles and only fails if the op runs.

Surfaced by Acorn User (RR1/RR6/Smooth use MOUSE ON/OFF, AlienTr uses ELLIPSE).
"""
import pytest

from conftest import requires_dotnet_toolchain

from owl_basic.analysis import analyse


# -- array initialiser list ------------------------------------------------

def test_array_initialiser_list_compiles(dotnet_backend):
    il = dotnet_backend.emit_il(analyse("DIM A(3)\nA() = 10, 20, 30\nEND\n", name="t"))
    assert il
    assert "NotImplemented" not in il          # it is lowered, not deferred


@requires_dotnet_toolchain
def test_array_initialiser_list_assigns_successive_elements(compile_and_run):
    out = compile_and_run(analyse(
        "DIM A(3)\nA() = 11, 22, 33\nPRINT A(0);\" \";A(1);\" \";A(2)\n", name="t"))
    assert out.split() == ["11", "22", "33"]


@requires_dotnet_toolchain
def test_string_array_initialiser_list(compile_and_run):
    out = compile_and_run(analyse(
        'DIM A$(3)\nA$() = "a", "b", "c"\nPRINT A$(0);A$(1);A$(2)\n', name="t"))
    assert out.strip() == "abc"


def test_whole_array_fill_still_works(dotnet_backend):
    # The single-RHS forms (fill / copy) are unaffected by the list case.
    assert dotnet_backend.emit_il(analyse("DIM A(3)\nA() = 0\nEND\n", name="t"))


# -- MOUSE ON/OFF (pointer) / ELLIPSE deferred stubs -----------------------

def test_mouse_on_compiles_as_deferred(dotnet_backend):
    il = dotnet_backend.emit_il(analyse("MOUSE ON\nEND\n", name="t"))
    assert "NotImplemented" in il


def test_mouse_off_compiles_as_deferred(dotnet_backend):
    il = dotnet_backend.emit_il(analyse("MOUSE OFF\nEND\n", name="t"))
    assert "NotImplemented" in il


def test_ellipse_compiles_as_deferred(dotnet_backend):
    il = dotnet_backend.emit_il(analyse("ELLIPSE 100,100,50,20\nEND\n", name="t"))
    assert "NotImplemented" in il


@requires_dotnet_toolchain
def test_graphics_stub_compiles_and_fails_only_when_reached(compile_and_run):
    out = compile_and_run(analyse('PRINT "ok"\nIF FALSE THEN MOUSE ON\n', name="t"))
    assert out.strip() == "ok"
