# Functions for analysing the CFG graph

import bbc_ast


def tagNode(tag, node):
    if tag not in node.entryPoints:
        node.addEntryPoint(tag)
        tagFollowingStatements(node, tag)

def tagSuccessors(entry_point):
    """
    Given an entry point tag all successors of that entry point
    with the routine name
    """
    tag = None
    if isinstance(entry_point, bbc_ast.DefineProcedure):
        # TODO: There is a bug here, whereby SUBXYZ can get relabelled PROCSUBXYZ
        tag = "PROC" + entry_point.name
    elif isinstance(entry_point, bbc_ast.DefineFunction):
        tag = "FN" + entry_point.name
    elif len(entry_point.comeFromEdges) != 0:
        tag = "SUB" + str(entry_point.lineNum)
    else:
        # TODO: Find a better way to do this rather than defaulting here
        tag = "MAIN"
    
    if tag is not None:
        tagNode(tag, entry_point)
        tagFollowingStatements(entry_point, tag)
    
def tagFollowingStatements(node, tag):
    for successor in node.outEdges:
        tagNode(tag, successor)

def deTagSuccessors(node):
    """
    Given a node and its entry point tags, remove all those tags from following
    the nodes.
    """
    tags = node.entryPoints
    if tags is not None:
        deTagFollowingStatements(node, tags)
    
def deTagFollowingStatements(node, tags):
    for successor in node.outEdges:
        deTagNode(tags, successor)
        
def deTagNode(tags, node):
    if tags.issubset(node.entryPoints):
        node.entryPoints.difference_update(tags)
        deTagFollowingStatements(node, tags)