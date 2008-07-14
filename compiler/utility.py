# Miscellaneous utility functions

def underscoresToCamelCase(s):
    t = s.replace('_', ' ').title().replace(' ', '')
    u = t[0].lower() + t[1:]
    return u
