class Option(object):
    pass

class BoolOption(Option):
    def __init__(self, default=None):
        self.value = default
        
class IntegerOption(Option):
    def __init__(self, default=None):
        self.value = default

class FloatOption(Option):
    def __init__(self, default=None):
        self.value = default

class StringOption(Option):
    def __init__(self, default=None):
        self.value = default

class TypeOption(Option):
    def __init__(self, default=None):
        self.value = default