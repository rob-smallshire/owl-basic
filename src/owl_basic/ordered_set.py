"""An insertion-ordered set.

The compiler's control-flow analyses traverse each vertex's edge collections
(out-edges, in-edges, loop edges). Backed by plain ``set``s, the iteration
order varied from one process to the next (hash randomisation of the vertex
objects), and some analyses -- notably subroutine-entry detection -- reached a
different result depending on that order, so compiling the same program twice
could give different outcomes.

Backing the collection with a ``dict`` (insertion-ordered since Python 3.7)
makes every traversal follow the order edges were added, which is program
order, so compilation is deterministic. Set semantics (no duplicate edges) are
preserved by the dict keys.

Only the small slice of the set protocol the CFG edge collections use is
provided directly (``add``/``discard``/``update`` plus the membership, length
and iteration dunders); ``MutableSet`` supplies ``remove``/``clear``/``pop``
and the in-place operators on top.
"""

from collections.abc import MutableSet


class OrderedSet(MutableSet):
    def __init__(self, iterable=()):
        self._items = dict.fromkeys(iterable)

    def add(self, value):
        self._items[value] = None

    def discard(self, value):
        self._items.pop(value, None)

    def update(self, iterable):
        for value in iterable:
            self._items[value] = None

    def __contains__(self, value):
        return value in self._items

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, list(self._items))
