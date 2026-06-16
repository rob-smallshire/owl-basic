"""Shared routine-identity helpers for the program graph sources.

Flow analysis records a statement's routine membership as a set of *entry-point
tags* on the statement. These helpers map between those tags, the
``entry_points`` dict keys, and the user-facing routine names the ``visualise``
command accepts, and resolve a requested routine to its canonical key.

Membership is intentionally many-valued: a statement shared between routines
carries several tags, which is how the call graph detects entanglement and how
a scoped view still shows shared code under each routine it belongs to.
"""

from owl_basic.exceptions import OwlBasicError
from owl_basic.syntax.ast import DefineFunction, DefineProcedure

_MAIN = "__owl__main"


def display_name(name: str) -> str:
    """The user-facing name for an entry-point key (``__owl__main`` -> MAIN)."""
    return "MAIN" if name == _MAIN else name


def routine_kind(name: str) -> str:
    """The node kind for a routine, by its entry-point key."""
    if name == _MAIN:
        return "main"
    if name.startswith("FN"):
        return "fn"
    if name.startswith("PROCSub"):
        return "sub"
    return "proc"


def routine_tag(name: str, node) -> str:
    """The entry-point tag flow analysis stamps on a routine's statements.

    Derived from the routine's identity exactly as ``flow_analysis.tagSuccessors``
    does -- NOT read off the entry point's own ``entryPoints`` set, which can be
    polluted by foreign tags where routines share code.
    """
    if name == _MAIN:
        return "MAIN"
    if isinstance(node, DefineFunction):
        return "FN" + node.name
    if isinstance(node, DefineProcedure):
        return "PROC" + node.name
    # A subroutine entry point not converted to a procedure; fall back to its
    # own single tag.
    return next(iter(node.entryPoints), name)


def tag_to_name(program) -> dict:
    """A mapping of each routine's statement tag to its entry-point key."""
    return {routine_tag(name, node): name
            for name, node in program.entry_points.items()}


def _names_from_tags(tags, mapping) -> set:
    return {mapping[tag] for tag in tags if tag in mapping}


def routines_of(statement, mapping) -> set:
    """The entry-point keys a statement belongs to (>1 means shared code).

    A statement that inherited no tag -- e.g. a GOSUB freshly rewritten to a
    procedure call -- is attributed via its CFG neighbours so it is still placed
    in its enclosing routine.
    """
    names = _names_from_tags(statement.entryPoints, mapping)
    if not names:
        for neighbour in statement.outEdges:
            names |= _names_from_tags(neighbour.entryPoints, mapping)
    if not names:
        for neighbour in statement.inEdges:
            names |= _names_from_tags(neighbour.entryPoints, mapping)
    return names


def resolve_routine(program, requested):
    """Resolve a user-supplied routine name to its canonical entry-point key.

    Accepts ``MAIN`` (or ``__owl__main``) and any entry-point key, matched
    case-insensitively. Returns ``None`` when *requested* is ``None`` (no
    scoping). Raises :class:`OwlBasicError` listing the routines when no match.
    """
    if requested is None:
        return None
    candidates = {}
    for key in program.entry_points:
        candidates[key.lower()] = key
        candidates[display_name(key).lower()] = key
    target = candidates.get(requested.lower())
    if target is None:
        available = ", ".join(sorted(display_name(k) for k in program.entry_points))
        raise OwlBasicError(
            "No routine %r. Available routines: %s" % (requested, available)
        )
    return target


def routine_option(options):
    """The requested routine from a source's *options*, or ``None``."""
    if options is None:
        return None
    if isinstance(options, dict):
        return options.get("routine")
    return getattr(options, "routine", None)
