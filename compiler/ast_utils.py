from utility import camelCaseToUnderscores

def elideNode(node, liftFormalTypes=False):
    """
    Removes a node from the AST, assigning the contents of its only attribute
    attribute to the owning attribute, thereby simplifing the AST structure. If
    liftFormalTypes is true, the formal type of the child is propagates to the
    new owner of the data.
    """
    # TODO: Refactor! D.R.Y.
    assert len(node.child_infos) == 1
    print node
    print node.child_infos
    if isinstance(node.child_infos.values()[0], list):
        prop = node.child_infos.keys()[0] # TODO: Rename list_property
        print prop
        
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