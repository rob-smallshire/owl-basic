# A visitor for performing type-checking over the Abstract Syntax Tree

from visitor import Visitor
from errors import *
from utility import underscoresToCamelCase
from bbc_types import *
from bbc_ast import Cast

class TypecheckVisitor(Visitor):
    """
    AST visitor for determining the actual type of each node
    """
    def __init__(self):
        pass
    
    def visitAstNode(self, node):
        node.forEachChild(self.visit)
        self.checkSignature(node)
    
    def visitAssignment(self, assignment):
        # Determine the actual type of the lValue and rValue
        self.visit(assignment.lValue)
        self.visit(assignment.rValue)
        
        if assignment.rValue.actualType.isA(assignment.lValue.actualType):
            if assignment.rValue.actualType != assignment.lValue.actualType:
                self.insertCast(node.rValue, source=assignment.rValue.actualType, target=assignment.lValue.actualType)
        elif assignment.lValue.actualType.isA(NumericType) and assignment.rValue.actualType.isA(NumericType):
            self.insertCast(assignment.rValue, assignment.rValue.actualType, assignment.lValue.actualType)
        else:
            message = "Cannot assign %s to %s" % (assignment.rValue.actualType, assignment.lValue.actualType)
            self.typeMismatch(assignment, message)
            
    def visitPlus(self, plus):
        # Determine the actual type of sub-expressions
        self.visit(plus.lhs)
        self.visit(plus.rhs)
        
        # If this is a string concatenation, convert the node and re-visit
        if plus.lhs.actualType == StringType and plus.rhs.actualType == StringType:
            concat = Concatenate(lhs = plus.lhs, rhs = plus.rhs)
            concat.lhs.parent = concat
            concat.rhs.parent = concat
            setattr(plus.parent, plus.parent_property, concat)
            self.visit(concat)
            return
        
        if not self.checkSignature(plus):
            return
        
        # Compute the type of the plus expression
        if plus.lhs.actualType == plus.rhs.actualType:
            plus.actualType = plus.lhs.actualType
        elif plus.lhs.actualType == IntegerType and plus.rhs.actualType == FloatType:
            self.insertCast(plus.lhs, source=IntegerType, target=FloatType)
            plus.actualType = FloatType
        elif plus.lhs.actualType == FloatType and plus.rhs.actualType == IntegerType:
            self.insertCast(plus.rhs, source=IntegerType, target=FloatType)
            plus.actualType = FloatType
        else:
            message = "Cannot add %s to %s" % (plus.lhs.actualType, plus.rhs.actualType)
            self.typeMismatch(plus, message)
    
    def visitMinus(self, minus):
        # Determine the actual type of sub-expressions
        self.visit(minus.lhs)
        self.visit(minus.rhs)
            
        if not self.checkSignature(minus):
            return
        
        # Compute the type of the minus expression
        if minus.lhs.actualType == minus.rhs.actualType:
            minus.actualType = minus.lhs.actualType
        elif minus.lhs.actualType == IntegerType and minus.rhs.actualType == FloatType:
            self.insertCast(minus.lhs, source=IntegerType, target=FloatType)
            minus.actualType = FloatType
        elif minus.lhs.actualType == FloatType and minus.rhs.actualType == IntegerType:
            self.insertCast(minus.rhs, source=IntegerType, target=FloatType)
            minus.actualType = FloatType
        else:
            message = "Cannot subtract %s from %s" % (minus.rhs.actualType, minus.lhs.actualType)
            self.typeMismatch(minus, message)
    
    def visitMultiply(self, multiply):
        # Determine the actual type of sub-expressions
        self.visit(multiply.lhs)
        self.visit(multiply.rhs)
        
        if not self.checkSignature(multiply):
            return
        
        # Compute the type of the multiply expression
        if multiply.lhs.actualType == multiply.rhs.actualType:
            multiply.actualType = multiply.lhs.actualType
        elif multiply.lhs.actualType == IntegerType and multiply.rhs.actualType == FloatType:
            self.insertCast(multiply.lhs, source=IntegerType, target=FloatType)
            multiply.actualType = FloatType
        elif multiply.lhs.actualType == FloatType and multiply.rhs.actualType == IntegerType:
            self.insertCast(multiply.rhs, source=IntegerType, target=FloatType)
            multiply.actualType = FloatType
        else:
            message = "Cannot multiply %s by %s" % (multiply.lhs.actualType, multiply.rhs.actualType)
            self.typeMismatch(multiply, message)
    
    def visitDivide(self, divide):
        # Determine the actual type of sub-expressions
        self.visit(divide.lhs)
        self.visit(divide.rhs)
        
        if not self.checkSignature(divide):
            return
        
        # Compute the type of the division expression
        divide.actualType = FloatType            
        if divide.lhs.actualType == IntegerType:
            self.insertCast(divide.lhs, source=IntegerType, target=FloatType)
        if divide.rhs.actualType == IntegerType:
            self.insertCast(divide.rhs, source=IntegerType, target=FloatType)
            
    def visitPower(self, power):
        # Determine the actual type of sub-expressions
        self.visit(divide.lhs)
        self.visit(divide.rhs)
        
        if not self.checkSignature(divide):
            return
        
        # Compute the actual type of the power expression
        power.actualType = FloatType
        if power.lhs.actualType == IntegerType and power.rhs.actualType == FloatType:
            self.insertCast(power.lhs, source=IntegerType, target=FloatType)
        elif power.lhs.actualType == FloatType and power.rhs.actualType == IntegerType:
            self.insertCast(power.rhs, source=IntegerType, target=FloatType)
        else:
            message = "Cannot raise %s by %s" % (divide.lhs.actualType, divide.rhs.actualType)
            self.typeMismatch(divide, message)
    
    def visitVariable(self, variable):
        # Decode the variable name sigil into the actual type
        # The sigils are one of [$%&~]
        variable.actualType = self.identifierToType(variable.identifier)
         
    def visitUnaryNumericFunc(self, func):
        self.visit(func.factor)
        if not self.checkSignature(func):
            return
        if func.factor.actualType is IntegerType:
            self.insertCast(func.factor, source=func.factor.actualType, target=FloatType)
        
    def insertCast(self, child, source, target):
        """Wrap the supplied node is a Cast node from source type to target type"""
        if source is FloatType and target is IntegerType:
            message = "of %s to %s, possible loss of data" % (source, target)
            self.castWarning(child, message)
        
        parent = child.parent
        parent_property = child.parent_property
        child_name, index = parent.findChild(child) # TODO: Give parent_property as a hint
        cast = Cast(sourceType=source, targetType=target, value=child)
        cast.parent = parent
        cast.parent_property = parent_property
        cast.value.parent = cast
        cast.value.parent_property = "value"
        setattr(parent, parent_property, cast)
        
    def identifierToType(self, identifier):
        sigil = identifier[-1]
        if sigil == '$':
            return StringType
        elif sigil == '%':
            return IntegerType
        elif sigil == '&':
            return ByteType
        elif sigil == '~':
            return ReferenceType
        elif sigil == '(':
            sigil = identifer[-2:-1]
            if sigil == '$':
                return StringArrayType
            elif sigil == '%':
                return IntegerArrayType
            elif sigil == '&':
                return ByteArrayType
            elif sigil == '~':
                return ReferenceArrayType
            else:
                return FloatArrayType
        return FloatType 
            
    def checkSignature(self, node):
        """
        Check the actualType of each child node against the formalType of each
        child node and determine if they are of compatible type. For example,
        IntegerType is compatible with NumericType, and NumericType is compatible
        with ScalarType, but StringType is not compatible with NumericType.
        """
        result = True
        for name, info in node.child_infos.items():
            if isinstance(info, list):
                info = info[0]
                formal_type = info.formalType
                for child_node in getattr(node, underscoresToCamelCase(name)):
                    child_result = self.checkType(node, child_node, formal_type, info)
                    result = result and child_result
            else:
                formal_type = info.formalType
                child_node = getattr(node, underscoresToCamelCase(name))
                child_result = self.checkType(node, child_node, formal_type, info)
                result = result and child_result
        return result
    
    def checkType(self, node, child_node, formal_type, info):
        """
        Checks that child_node of node is of formal_type. 
        """
        actual_type = child_node.actualType
        
        if formal_type is not None: # None types do not need to be checked
            if actual_type is not None:
                if not actual_type.isA(formal_type):
                    message = "%s of %s is incompatible with supplied parameter of type %s" % (info.description, node.description, actual_type.__doc__)
                    self.typeMismatch(node, message)
                    return False
            else:
                message = "%s of %s has no type information" % (info.description, node.description)
                self.typeError(node, message)
                return False
        return True
    
    def typeError(self, node, message):
        message = "%s at line %d" % (message, node.lineNum)
        internal(message)
            
    def typeMismatch(self, node, message):
        message = "Type mismatch: %s at line %d" % (message, node.lineNum)
        error(message)
        
    def castWarning(self, node, message):
        message = "Implicit conversion %s at line %d" % (message, node.lineNum)
        warning(message)
        
        