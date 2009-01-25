"""
A Python Singleton mixin class that makes use of some of the ideas
found at http://c2.com/cgi/wiki?PythonSingleton. Just inherit
from it and you have a singleton. No code is required in
subclasses to create singleton behavior -- inheritance from 
Singleton is all that is needed.

Assume S is a class that inherits from Singleton. Useful behaviors
are:

1) Getting the singleton:

    S.getInstance() 
    
returns the instance of S. If none exists, it is created. 

2) The usual idiom to construct an instance by calling the class, i.e.

    S()
    
is disabled for the sake of clarity. If it were allowed, a programmer
who didn't happen  notice the inheritance from Singleton might think he
was creating a new instance. So it is felt that it is better to
make that clearer by requiring the call of a class method that is defined in
Singleton. An attempt to instantiate via S() will restult in an SingletonException
being raised.

3) If S.__init__(.) requires parameters, include them in the
first call to S.getInstance(.). If subsequent calls have parameters,
a SingletonException is raised.

4) As an implementation detail, classes that inherit 
from Singleton may not have their own __new__
methods. To make sure this requirement is followed, 
an exception is raised if a Singleton subclass includ
es __new__. This happens at subclass instantiation
time (by means of the MetaSingleton metaclass.

By Gary Robinson, grobinson@transpose.com. No rights reserved -- 
placed in the public domain -- which is only reasonable considering
how much it owes to other people's version which are in the
public domain. The idea of using a metaclass came from 
a  comment on Gary's blog (see 
http://www.garyrobinson.net/2004/03/python_singleto.html#comments). 
Other improvements came from comments and email from other
people who saw it online. (See the blog post and comments
for further credits.)

Not guaranteed to be fit for any particular purpose. Use at your
own risk. 
"""





class SingletonException(Exception):
    pass


class MetaSingleton(type):
    def __new__(metaclass, strName, tupBases, dict):
        if dict.has_key('__new__'):
            raise SingletonException, 'Can not override __new__ in a Singleton'
        return super(MetaSingleton,metaclass).__new__(metaclass, strName, tupBases, dict)
        
    def __call__(cls, *lstArgs, **dictArgs):
        raise SingletonException, 'Singletons may only be instantiated through getInstance()'
        
class Singleton(object):
    __metaclass__ = MetaSingleton
    
    def __init__(self, *args, **kwargs):
        """
        Provided for compatibility with subclasses which call super() in their __init__
        """
        super(Singleton, self).__init__(*args, **kwargs)
    
    # @TODO: This method NEEDS to be thread-safe
    def getInstance(cls, *lstArgs, **kwargs):
        """
        Call this to instantiate an instance or retrieve the existing instance.
        If the singleton requires args to be instantiated, include them the first
        time you call getInstance.        
        """
        if cls._isInstantiated():
            if len(lstArgs) + len(kwargs) != 0:
                raise SingletonException, 'If no supplied args, singleton must already be instantiated, or __init__ must require no args'
        else:
            instance = cls.__new__(cls)
            instance.__init__(*lstArgs, **kwargs)
            cls.cInstance = instance
        return cls.cInstance
    getInstance = classmethod(getInstance)
    
    def _isInstantiated(cls):
        return hasattr(cls, 'cInstance')
    _isInstantiated = classmethod(_isInstantiated)  

    def _getConstructionArgCountNotCountingSelf(cls):
        return cls.__init__.im_func.func_code.co_argcount - 1
    _getConstructionArgCountNotCountingSelf = classmethod(_getConstructionArgCountNotCountingSelf)

    def _forgetClassInstanceReferenceForTesting(cls):
        """
        This is designed for convenience in testing -- sometimes you 
        want to get rid of a singleton during test code to see what
        happens when you call getInstance() under a new situation.
        
        To really delete the object, all external references to it
        also need to be deleted.
        """
        try:
            delattr(cls,'cInstance')
        except AttributeError:
            # run up the chain of base classes until we find the one that has the instance
            # and then delete it there
            for baseClass in cls.__bases__: 
                if issubclass(baseClass, Singleton):
                    baseClass._forgetClassInstanceReferenceForTesting()
    _forgetClassInstanceReferenceForTesting = classmethod(_forgetClassInstanceReferenceForTesting)
    


if __name__ == '__main__':
    
    unittest.main()

    