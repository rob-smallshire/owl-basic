# Functions for analysing the CFG graph

from owl_basic.syntax import ast


def tagNode(tag, node):
    # Iterative depth-first tagging: recursing per CFG node overflows the call
    # stack on large programs.
    stack = [node]
    while stack:
        current = stack.pop()
        if tag not in current.entryPoints:
            current.addEntryPoint(tag)
            stack.extend(current.outEdges)

def tagSuccessors(entry_point, line_mapper):
    """
    Given an entry point node, tag all successors of that entry point
    with the routine name
    :param entry_point: A node which is the entry point into a routine
    :param line_mapper: An object which supports a physicalToLogical method call
                        to convert line numbers.
    """
    tag = None
    if isinstance(entry_point, ast.DefineProcedure):
        # TODO: There is a bug here, whereby SUBXYZ can get relabelled PROCSUBXYZ
        tag = "PROC" + entry_point.name
    elif isinstance(entry_point, ast.DefineFunction):
        tag = "FN" + entry_point.name
    elif len(entry_point.comeFromGosubEdges) != 0:
        logical_line_number = line_mapper.physicalToLogical(entry_point.lineNum)
        tag = "SUB%d" % logical_line_number
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
    # Iterative depth-first de-tagging, for the same stack-overflow reason as
    # tagNode.
    stack = [node]
    while stack:
        current = stack.pop()
        if tags.issubset(current.entryPoints):
            current.entryPoints.difference_update(tags)
            stack.extend(current.outEdges)