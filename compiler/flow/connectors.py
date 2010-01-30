'''
Functions for manipulating the control flow graph
'''

from ast_utils import findFollowingStatement

def connectToFollowing(statement):
    following = findFollowingStatement(statement)
    if following is not None:
        connect(statement, following)

def connect(from_statement, to_statement):
    from_statement.addOutEdge(to_statement)
    to_statement.addInEdge(from_statement)
