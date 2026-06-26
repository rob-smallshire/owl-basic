"""Symbol-table pass over INPUT#, whose visit method was copy-pasted from
``visitInput`` without renaming the node.

``visitInputFile(self, input)`` referred in its body to a non-existent
``statement`` (NameError) and then to ``inputList``, a field the ``InputFile``
node does not have (its items are a ``variable_list`` under ``items``). Every
INPUT# thus crashed the front end once the CFG was walked. Surfaced across ~7
Acorn User type-ins (e.g. Tau85-b/JUL85.DAVIES2).
"""
from helpers import analyse


def test_input_file_analyses():
    program = analyse('A% = OPENIN("d")\nINPUT#A%, x%, y$\nPRINT x%\nEND\n',
                      name="inf")
    assert program is not None


def test_input_file_multiple_variables_analyses():
    program = analyse('chan% = OPENIN("d")\nINPUT#chan%, a, b%, c$\nEND\n',
                      name="inf2")
    assert program is not None
