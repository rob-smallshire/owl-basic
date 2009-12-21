import errors
from utility import camelCaseToUnderscores

def elideNode(node, liftFormalTypes=False):
    """
    Removes a node from the AST, assigning the contents of its only attribute
    attribute to the owning attribute, thereby simplifying the AST structure. If
    liftFormalTypes is true, the formal type of the child is propagates to the
    new owner of the data.
    """
    # TODO: Refactor! D.R.Y.
    assert len(node.child_infos) == 1
    #print node
    #print node.child_infos
    if isinstance(node.child_infos.values()[0], list):
        prop = node.child_infos.keys()[0] # TODO: Rename list_property
        #print prop
        
        for item in getattr(node, prop):
            if item is not None:
                item.parent = node.parent
                item.parent_property = node.parent_property
                # Note: item.parent_index remains unchanged
    else:
        prop = node.child_infos.keys()[0]
        assert not isinstance(prop, list)
        item = getattr(node, prop)
        if item is not None:
            item.parent = node.parent
            item.parent_property = node.parent_property
            # Note: item.parent_index remains unchanged
    assert hasattr(node.parent, node.parent_property)
    if liftFormalTypes:
        node.parent.child_infos[camelCaseToUnderscores(node.parent_property)] = node.child_infos[prop]
    node.parent.setProperty(getattr(node, prop), node.parent_property)
    
def findFollowingStatement(statement):
    """
    Given a statement, locates the following statement
    """
    #print "findFollowingStatement"
    if statement.parent is None:
        #print "statement.parent is None"
        return None
    #print "statement.lineNum = %s" % statement.lineNum
    parent_list = getattr(statement.parent, statement.parent_property)
    
    #print "parent_list = %s" % parent_list
    if isinstance(parent_list, list):
        #print "parent_index = %d" % statement.parent_index
        #print "len(parent_list) = %d" % len(parent_list)
        if statement.parent_index < (len(parent_list) - 1):
            #print "parent_list[statement.parent_index + 1] = %s" % parent_list[statement.parent_index + 1]
            return parent_list[statement.parent_index + 1]
    
    return findFollowingStatement(statement.parent)

def findRoot(node):
    """
    Given an AST node find the root node of the AST.
    """
    n = node
    while n.parent is not None:
        n = n.parent
    return n

def findNode(node, predicate):
    """
    Given an AST node, search up the tree until a node matching the
    predicate function is found. Returns the Node or None
    """
    n = node
    while n is not None:
        if predicate(n):
            return n
        n = n.parent
    return None

def insertStatementBefore(statement, target):
    """
    Insert target before statement in the AST, and correct the AST and CFG references to match
    """
    # TODO: Does this need to correct incoming GOTOs or is that handled by adjusting the AST edges
    
    if statement.parent is None:
        errors.fatalError("Cannot insert statement before %s at line %s" % (statement, statement.lineNum))
    
    parent_list = getattr(statement.parent, statement.parent_property)
    
    if isinstance(parent_list, list):
        parent_list.insert(statement.parent_index, target)
        target.parent = statement.parent
        target.parent_property = statement.parent_property
        target.parent_index = statement.parent_index
        statement.parent_index += 1
                  
    else:
        errors.fatalError("Cannot insert statement into non-list %s at line %s" % (statement, statement.lineNum))
        return
        
    # Reconnect CFG
    for prior_stmt in statement.inEdges:
        assert statement in prior_stmt.outEdges
        prior_stmt.outEdges.remove(statement)
        prior_stmt.outEdges.append(target)
        target.inEdges.append(prior_stmt)
    
    statement.clearInEdges()    
    statement.addInEdge(target)
    
    target.clearOutEdges()
    target.addOutEdge(statement)
    
def removeStatement(statement):
    """
    Remove the statement from the AST
    """
    if statement.parent is None:
        errors.fatalError("Cannot remove statement %s at line %s" % (statement, statement.lineNum))
        
    # Remove from the parent list
    parent_list = getattr(statement.parent, statement.parent_property)
    parent_list.remove(statement)
    
    # Reconnect CFG
    for prior_stmt in statement.inEdges:
        assert statement in prior_stmt.outEdges
        prior_stmt.outEdges.remove(statement)
        prior_stmt.outEdges.extend(statement.outEdges)
        
    for next_stmt in statement.outEdges:
        assert statement in next_stmt.inEdges
        next_stmt.inEdges.remove(statement)
        next_stmt.inEdges.extend(statement.inEdges)

    statement.clearInEdges()
    statement.clearOutEdges()

def replaceStatement(old, new):
    '''
    Replace old with new in the AST and CFG
    '''
    insertStatementBefore(old, new)
    removeStatement(old)

def deParentNode(node):
    '''
    Disconnect a node from its parent
    :returns: The node  
    '''
    raise "Not implemented"
    
def parentNode(node, parent, parent_property):
    '''
    Parent a node the the given property
    '''
    raise "Not implemented"
    
def reParentnode(node, new_parent, parent_property=None):
    '''
    :param node: The node to be reparented
    :param new_parent: The new parent for node
    :paraent_property: The property of the parent to which the node will be attached. If not
                       supplied this will use the parent_property as the original parent.
    '''
    if parent_property is None:
        parent_property = node.parent_property
        
    deParentNode(node)
    parentNode(node, new_parent, parent_property)
