"""OrderedSet: set semantics with deterministic, insertion-ordered iteration.

It backs the CFG edge collections so control-flow traversals follow program
order and compilation is reproducible (see owl_basic.ordered_set).
"""
from owl_basic.ordered_set import OrderedSet


def test_iterates_in_insertion_order():
    s = OrderedSet()
    for value in (30, 10, 20, 10, 40):
        s.add(value)
    assert list(s) == [30, 10, 20, 40]  # deduplicated, first-seen order


def test_membership_len_and_dedup():
    s = OrderedSet([1, 2, 2, 3])
    assert len(s) == 3
    assert 2 in s and 9 not in s


def test_update_extends_in_order():
    s = OrderedSet([1])
    s.update([3, 2, 1])
    assert list(s) == [1, 3, 2]


def test_remove_and_discard():
    s = OrderedSet([1, 2, 3])
    s.discard(2)
    s.discard(99)            # absent -> no error
    s.remove(1)
    assert list(s) == [3]


def test_remove_absent_raises_keyerror():
    s = OrderedSet([1])
    try:
        s.remove(2)
    except KeyError:
        pass
    else:
        raise AssertionError("remove of absent element should raise KeyError")


def test_iteration_order_independent_of_hash():
    # Distinct objects whose set order would otherwise be hash-randomised must
    # still come out in insertion order.
    objects = [object() for _ in range(5)]
    s = OrderedSet(objects)
    assert list(s) == objects
