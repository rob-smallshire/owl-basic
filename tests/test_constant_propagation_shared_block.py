"""Definite-assignment tolerates a predecessor outside the method's block list.

Block identification assigns a block reachable from two entry points to just one
method's list, yet that block's in-edges can cross from a block on another
method's list. The per-method definite-assignment then looks the predecessor up
in its own ``defined_out`` and used to raise ``KeyError``. Such a cross-method
predecessor must instead contribute nothing (a MUST analysis stays sound by
under-, never over-, propagating). Surfaced by The Micro User MUNCH / WHODUNN /
TYCOON1, whose shared GOSUB blocks crashed constant propagation.
"""
from owl_basic.constant_propagation import _definite_assignment
from owl_basic.flow.basic_block import BasicBlock


def test_predecessor_not_in_method_does_not_crash():
    foreign = BasicBlock()                 # a block on another method's list
    entry = BasicBlock()
    body = BasicBlock()
    entry.addOutEdge(body)
    body.addInEdge(entry)
    body.addInEdge(foreign)                # cross-method in-edge -- not in `blocks`

    blocks = [entry, body]                 # note: `foreign` is deliberately absent
    di = _definite_assignment(blocks, constants=set(), must_define={}, entry_seed=set())

    # No KeyError, and the foreign predecessor contributes nothing, so the body
    # has no definitely-assigned constants on entry.
    assert di[id(body)] == set()
