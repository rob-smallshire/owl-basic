"""Symbol-table pass over MOUSE, whose visit method was copy-pasted from
visitInput without renaming the node.

``visitMouse(self, mouse)`` referred in its body to a non-existent ``statement``
(NameError) and added the optional (possibly None) ``time`` target
unconditionally. Every MOUSE x,y,b thus crashed the front end once the CFG was
walked -- surfaced across ~7 Acorn User Archimedes type-ins (Henon, Rope, ...)
once BASIC V detokenisation let them through.
"""
from helpers import analyse


def test_mouse_three_argument_analyses():
    program = analyse('MOUSE x%, y%, b%\nEND\n', name="mse")
    assert program is not None


def test_mouse_four_argument_analyses():
    program = analyse('MOUSE x%, y%, b%, t%\nEND\n', name="mse4")
    assert program is not None
