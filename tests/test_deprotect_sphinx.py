"""The Sphinx de-protector's byte-poke restoration.

Sphinx's line 363 has an anti-listing poke: the ``(`` in ``PROCR(6)`` was
overwritten with the PROC token, so a PROC token is immediately followed by a
digit (never valid). The de-protector restores it.
"""

import importlib.util
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_TOOL = os.path.join(_HERE, "..", "tools", "deprotect_sphinx.py")
_spec = importlib.util.spec_from_file_location("deprotect_sphinx", _TOOL)
deprotect_sphinx = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(deprotect_sphinx)


def test_restores_paren_poked_to_proc():
    # PROC(0xF2) R ( 6 )  with the '(' poked to a PROC token.
    poked = bytes([0xF2, 0x52, 0xF2, 0x36, 0x29])     # PROC R PROC 6 )
    restored, count = deprotect_sphinx._restore_paren_pokes(poked)
    assert count == 1
    assert restored == bytes([0xF2, 0x52, 0x28, 0x36, 0x29])  # PROC R ( 6 )


def test_leaves_genuine_proc_calls_and_strings_alone():
    # A real PROC call (PROC followed by a name) and a digit inside a string
    # must not be touched.
    proc_call = bytes([0xF2, 0x52, 0x28, 0x36, 0x29])         # PROCR(6) already
    in_string = bytes([0x22, 0xF2, 0x36, 0x22])              # "<F2>6"
    assert deprotect_sphinx._restore_paren_pokes(proc_call) == (proc_call, 0)
    assert deprotect_sphinx._restore_paren_pokes(in_string) == (in_string, 0)
