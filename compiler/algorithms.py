def all_equal(vals):
    '''
    Check if all elements of a list are equal.
    :param vals: a sequence of items
    '''
    if vals:
        i = iter(vals)
        first = i.next()
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
	return iter(s).next()
