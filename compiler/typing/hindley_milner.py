'''
Created on 5 Apr 2010
An implementation of the Hindley Milner type checking algorithm based on the
Scala code by Andrew Forrest, the Perl code by Nikita Borisov and the paper
"Basic Polymorphic Typechecking" by Cardelli.
@author: Robert Smallshire
'''

from itertools import izip

#=======================================================#

class SyntaxNode(object):
    
    def __str__(self):
        return "(%s)" % self.nakedString()

class Lambda(SyntaxNode):
    
    def __init__(self, v, body):
        self.v = v
        self.body = body
        
    def nakedString(self):
        return "fn " + self.v + " => " + str(self.body)
        
class Ident(SyntaxNode):
    
    def __init__(self, name):
        self.name = name
        
    def __str__(self):
        return self.nakedString()
    
    def nakedString(self):
        return self.name
        
class Apply(SyntaxNode):
    
    def __init__(self, fn, arg):
        self.fn = fn
        self.arg = arg
        
    def nakedString(self):
        return str(self.fn) + " " + str(self.arg)
        
class Let(SyntaxNode):
    
    def __init__(self, v, defn, body):
        self.v = v
        self.defn = defn
        self.body = body
        
    def nakedString(self):
        return "let " + self.v + " = " + str(self.defn) + " in " + str(self.body)
        
class Letrec(SyntaxNode):
    
    def __init__(self, v, defn, body):
        self.v = v
        self.defn = defn
        self.body = body
        
    def nakedString(self):
        return "letrec " + self.v + " = " + str(self.defn) + " in " + str(self.body)

#=======================================================#

class TypeError(Exception):
    def __init__(self, message):
        self.__message = message
    
    message = property(lambda self: self.__message)
        
    def __str__(self):
        return str(self.message)
 
class ParseError(Exception):
    def __init__(self, message):
        self.__message = message
        
    message = property(lambda self: self.__message)
    
    def __str__(self):
        return str(self.message)
        
#=======================================================#
            
class Variable(object):
    
    def __init__(self, id):
        self.id = id
        self.instance = None
        self.__name = None
    
    def _getName(self):
        if self.__name is None:
            self.__name = uniqueName().next()
        return self.__name
    
    name = property(_getName)
                
    def __str__(self):
        return "Variable(id = %s)" % self.id
    
    def __repr__(self):
        return str(self)

class Oper(object):   
    
    def __init__(self, name, types):
        self.name = name
        self.types = types
                
def Function(from_type, to_type):
    return Oper("->", [from_type, to_type])

Integer = Oper("int", [])
Bool    = Oper("bool", [])

next_variable_name = 'a'

def uniqueName():
    global next_variable_name
    while True:
        result = next_variable_name
        next_variable_name = chr(ord(next_variable_name) + 1)
        yield result

next_variable_id = 0

def newVariable():
    '''
    Factory function which creates a new Variable
    '''
    global next_variable_id
    result = next_variable_id
    next_variable_id += 1
    return Variable(result)

def string(t):
    assert t is not None
    if isinstance(t, Variable):
        if t.instance is not None:
            return string(t.instance) 
        else:
            return t.name # TODO: Check
            
    elif isinstance(t, Oper):
        num_types = len(t.types)
        if num_types == 0:
            return t.name
        elif num_types == 2:
            return "(%s %s %s)" % (string(t.types[0]), t.name, string(t.types[1]))
        else:
            return "%s %s" % (t.name, ' '.join(t.types))
    assert 0, "Unhandled type %s" % type(t)

def analyse(node, env, non_generic=None):
    '''
    Computes the type of the AST node in the context of the environment env
    :param node:
    :param env:
    :param non_generic: A set of non-generic variables
    '''
    
    if non_generic is None:
        non_generic = set()
    
    if isinstance(node, Ident):
        return getType(node.name, env, non_generic)
    elif isinstance(node, Apply):
        fun_type = analyse(node.fn, env, non_generic)
        arg_type = analyse(node.arg, env, non_generic)
        result_type = newVariable()
        unify(Function(arg_type, result_type), fun_type)
        return result_type
    elif isinstance(node, Lambda):
        arg_type = newVariable()
        new_env = env.copy()
        new_env[node.v] = arg_type
        new_non_generic = non_generic.copy()
        new_non_generic.add(arg_type)
        result_type = analyse(node.body, new_env, new_non_generic)
        return Function(arg_type, result_type)
    elif isinstance(node, Let):
        defn_type = analyse(node.defn, env, non_generic)
        new_env = env.copy()
        new_env[node.v] = defn_type
        return analyse(node.body, new_env, non_generic)
    elif isinstance(node, Letrec):
        new_type = newVariable()
        new_env = env.copy()
        new_env[node.v] = new_type
        new_non_generic = non_generic.copy()
        new_non_generic.add(new_type)
        defn_type = analyse(node.defn, new_env, new_non_generic)
        unify(new_type, defn_type)
        return analyse(node.body, new_env, non_generic)
    assert 0, "Unhandled type %s" % type(t)

def getType(name, env, non_generic):
    '''
    :param name: A string
    :param env: The environment mapping from names to types
    :param non_generic: A set of non-generic Variables
    '''
    if name in env:
        return fresh(env[name], non_generic)
    elif isIntegerLiteral(name):
        return Integer
    else:
        raise ParseError("Undefined symbol %s" % name)
        
def fresh(t, non_generic):
    '''
    :param t:           A Type
    :param non_generic: A set of non-generic Variables
    '''
    mappings = {} # A mapping of Variables to Variables
    def freshrec(tp):
        '''
        :param tp A Type
        '''
        p = prune(tp)
        if isinstance(p, Variable):
            if isGeneric(p, non_generic):
                if p not in mappings:
                    mappings[p] = newVariable()
                return mappings[p]
            else:
                return p
        elif isinstance(p, Oper):
            return Oper(p.name, [freshrec(x) for x in p.types])
        
    return freshrec(t)
    
def unify(t1, t2):
    a = prune(t1)
    b = prune(t2)
    if isinstance(a, Variable):
        if a != b:
            if occursInType(a, b):
                raise TypeError("recursive unification")
            a.instance = b
    elif isinstance(a, Oper) and isinstance(b, Variable):
        unify(b, a)
    elif isinstance(a, Oper) and isinstance(b, Oper):
        if (a.name != b.name or len(a.types) != len(b.types)):
            raise TypeError("Type mismatch: %s != %s" % (string(a), string(b)))
        for p, q in izip(a.types, b.types):
            unify(p, q)
    else:
        assert 0, "Not unified"

def prune(t):
    '''
    Returns the currently defining instance of t.
    As a side effect, collapses the list of type instances.
    '''
    if isinstance(t, Variable):
        if t.instance is not None:
            t.instance = prune(t.instance)
            return t.instance
    return t
    
def isGeneric(v, non_generic):
    '''
    Must be called with v pre-pruned
    :param v: The Variable to be tested for genericity
    :param non_generic: A set of non-generic Variables
    '''
    return not occursIn(v, non_generic)

def occursInType(v, type2):
    '''
    Must be called with v pre-pruned
    :param v:
    :param type2:
    :returns: True if''' 
    pruned_type2 = prune(type2)
    if pruned_type2 == v:
        return True
    elif isinstance(pruned_type2, Oper):
        return occursIn(v, pruned_type2.types)
    return False

def occursIn(t, types):
    return any(occursInType(t, t2) for t2 in types)

def isIntegerLiteral(name):
    result = True
    try:
        int(name)
    except ValueError:
        result = False
    return result

#==================================================================#

def tryExp(env, ast):
    print str(ast) + " : ",
    try:
        t = analyse(ast, env)
        print string(t)
    except ParseError, e:
        print e
    except TypeError, e:
        print e

def main():
    
    var1 = newVariable()
    var2 = newVariable()
    pair_type = Oper("*", (var1, var2))
    
    var3 = newVariable()
    
    my_env = { "pair" : Function(var1, Function(var2, pair_type)),
               "true" : Bool,
               "cond" : Function(Bool, Function(var3, Function(var3, var3))),
               "zero" : Function(Integer, Bool),
               "pred" : Function(Integer, Integer),
               "times": Function(Integer, Function(Integer, Integer)) }
    
    pair = Apply(Apply(Ident("pair"), Apply(Ident("f"), Ident("4"))), Apply(Ident("f"), Ident("true")))
    
    examples = [
            # factorial
            Letrec("factorial", # letrec factorial =
                Lambda("n",    # fn n =>
                    Apply(
                        Apply(   # cond (zero n) 1
                            Apply(Ident("cond"),     # cond (zero n)
                                Apply(Ident("zero"), Ident("n"))),
                            Ident("1")),
                        Apply(    # times n
                            Apply(Ident("times"), Ident("n")),
                            Apply(Ident("factorial"),
                                Apply(Ident("pred"), Ident("n")))
                        )
                    )
                ),      # in
                Apply(Ident("factorial"), Ident("5"))
            ),

            # Should fail:
            # fn x => (pair(x(3) (x(true)))
            Lambda("x",
                Apply(
                    Apply(Ident("pair"),
                        Apply(Ident("x"), Ident("3"))),
                    Apply(Ident("x"), Ident("true")))),

            # pair(f(3), f(true))
            Apply(
                Apply(Ident("pair"), Apply(Ident("f"), Ident("4"))), 
                Apply(Ident("f"), Ident("true"))),


            # letrec f = (fn x => x) in ((pair (f 4)) (f true))
            Let("f", Lambda("x", Ident("x")), pair),

            # fn f => f f (fail)
            Lambda("f", Apply(Ident("f"), Ident("f"))),

            # let g = fn f => 5 in g g
            Let("g",
                Lambda("f", Ident("5")),
                Apply(Ident("g"), Ident("g"))),

            # example that demonstrates generic and non-generic variables:
            # fn g => let f = fn x => g in pair (f 3, f true)
            Lambda("g",
                   Let("f",
                       Lambda("x", Ident("g")),
                       Apply(
                            Apply(Ident("pair"),
                                  Apply(Ident("f"), Ident("3"))
                            ),
                            Apply(Ident("f"), Ident("true"))))),

            # Function composition
            # fn f (fn g (fn arg (f g arg)))
            Lambda("f", Lambda("g", Lambda("arg", Apply(Ident("g"), Apply(Ident("f"), Ident("arg"))))))
        
    ]
    
    for example in examples:
        tryExp(my_env, example)
    
if __name__ == '__main__':
    main()
     