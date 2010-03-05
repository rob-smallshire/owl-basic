from visitor import Visitor

class SetFunctionTypeVisitor(Visitor):
    '''
    Visitor for assigning the type of a named function at every call
    site of that function.
    '''

    def __init__(self, function_name, function_type):
        '''
        :param function_name: The name of the function including the FN prefix.
        :param type: The actual type to be assigned to the function.
        '''
        self.function_name = function_name
        self.function_type = function_type
        
    def visitAstNode(self, node):
        node.forEachChild(self.visit)
        
    def visitUserFunc(self, user_func):
        if user_func.name == self.function_name:
            print "Setting type of call to %s to %s" % (self.function_name, self.function_type) 
            user_func.actualType = self.function_type
        user_func.forEachChild(self.visit)
        