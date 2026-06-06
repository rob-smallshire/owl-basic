"""Regression: simplifying an IF...ELSE must not corrupt the If node class.

simplify_visitor reclassifies an IF's clauses from a single StatementList child
into a list of statements, updating ``child_infos``. ``child_infos`` is a
class-level dict shared by every If instance, so mutating it in place set the
class default for ``falseClause`` to a list. Any subsequently analysed IF
without an ELSE then defaulted ``falseClause`` to ``[]`` instead of ``None`` and
crashed when a visitor tried to ``accept()`` the list.
"""

from owl_basic.analysis import analyse


def test_if_with_else_does_not_corrupt_later_if_without_else():
    # An IF with an ELSE clause is simplified first (this set the class default).
    analyse('A%=8\nIF A%>5 THEN PRINT "big" ELSE PRINT "small"\nPRINT "x"\n',
            "withelse")
    # A later IF with no ELSE must still analyse (falseClause stays None).
    program = analyse('A%=8\nIF A%>5 THEN PRINT "big"\nPRINT "x"\n', "noelse")
    assert program is not None
