def all_equal(vals):
    '''
    Check if all elements of a list are equal.
    :param vals: a sequence of items
    '''
    if vals:
        i = iter(vals)
        first = next(i)
        for item in i:
            if first != item:
                return False
    return True
    
def representative(s):
	'''
	Return an arbitrary value from the set s
	:param s: A set
	:returns: A representative value from s
	'''
	return next(iter(s))

def all_indices(string, sub, listindex=None, offset=0):
    # call as l = all_indices(string, sub)
    # http://code.activestate.com/recipes/499314-find-all-indices-of-a-substring-in-a-given-string/
    # listindex must default to None, not []: a mutable default argument is
    # shared across calls and would accumulate indices from every invocation.
    if listindex is None:
        listindex = []
    i = string.find(sub, offset)
    while i >= 0:
        listindex.append(i)
        i = string.find(sub, i + 1)
    return listindex