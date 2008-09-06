# A visitor for performing type-checking over the Abstract Syntax Tree

from visitor import Visitor
from errors import *
from utility import underscoresToCamelCase
from bbc_types import *
from bbc_ast import Cast, Concatenate
from ast_utils import elideNode

class TypecheckVisitor(Visitor):
    """
    AST visitor for determining the actual type of each node
    """
    def __init__(self):
        pass
    
    def visit(self, node):
        "Override visit to allow safe traversal of lists"
        if isinstance(node, list):
            for elem in node:
                self.visit(elem)
        else:
            super(TypecheckVisitor, self).visit(node)
    
    def visitAstNode(self, node):
        node.forEachChild(self.visit)
        self.checkSignature(node)
    
    def visitAstStatement(self, statement):
        "Generic visitor for simple statements"
        statement.forEachChild(self.visit)      
        if not self.checkSignature(statement):
            return
        self.insertNumericCasts(statement)
        
    def visitAssignment(self, assignment):
        # Determine the actual type of the lValue and rValue
        
        self.visit(assignment.lValue)
        self.visit(assignment.rValue)
        if isinstance(assignment.rValue, list):
            # Deal with L-values which are lists
            if assignment.lValue.actualType.isA(ArrayType):
                for item in assignment.rValue:
                    if item.actualType.isConvertibleTo(assignment.lValue.actualType._getElementType()):
                        if item.actualType is not assignment.lValue.actualType._getElementType():
                            self.insertCast(item, item.actualType, target=assignment.lValue.actualType._getElementType())
                    else:
                        message = "Cannot assign list item of type %s to elements of %s" % (item.actualType.__doc__, assignment.lValue.actualType.__doc__)
                        self.typeMismatch(assignment, message)
            else:
                message = "List is only assignable to an array"
                self.typeMismatch(assignment, message)
        else:
            print assignment.rValue
            print assignment.rValue.actualType
            if assignment.rValue.actualType.isConvertibleTo(assignment.lValue.actualType):
                if assignment.rValue.actualType is not assignment.lValue.actualType:
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
            concat.parent = plus.parent
            plus.parent.setProperty(concat, plus.parent_property, plus.parent_index)
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
    
    def visitArray(self, array):
        # Decode the variable name sigil into the actual type
        # The sigils are one of [$%&~]
        array.actualType = self.identifierToType(array.identifier)
    
    def visitVariable(self, variable):
        # Decode the variable name sigil into the actual type
        # The sigils are one of [$%&~]
        variable.actualType = self.identifierToType(variable.identifier)
    
    def visitIf(self, iff):
        self.visit(iff.condition)
        self.visit(iff.trueClause)
        self.visit(iff.falseClause)
        print "iff.condition.actualType = %s" % iff.condition.actualType
        if iff.condition.actualType.isConvertibleTo(IntegerType):
            self.insertCast(iff.condition, iff.condition.actualType, iff.condition.formalType)
        else:
            self.typeMismatch(iff, "Conditional expression must be convertible to %s." % iff.condition.actualType.__doc__)
    
    def visitOnGoto(self, ongoto):
        self.visit(ongoto.switch)
        if ongoto.switch.actualType.isConvertibleTo(IntegerType):
            self.insertCast(ongoto.switch, ongoto.switch.actualType, ongoto.switch.formalType)
        else:
            self.typeMismatch(ongoto, "Selector expression must be convertible to %s" % ongoto.switch.actualType.__doc__)
        
        for target in ongoto.targetLogicalLines:
            self.visit(target)
            if target.actualType.isConvertibleTo(IntegerType):
                self.insertCast(target, target.actualType, IntegerType)
            else:
                self.typeMismatch(ongoto, "Target expressions must be convertible to Integer")
            
        self.visit(ongoto.outOfRangeClause)
            
    def visitUnaryNumericOperator(self, operator):
        self.visit(operator.factor)
        if not self.checkSignature(operator):
            return
        operator.actualType = operator.factor.actualType
        
    def visitBinaryIntegerOperator(self, operator):
        self.visit(operator.lhs)
        self.visit(operator.rhs)
        if not self.checkSignature(operator):
            return
        # TODO: Pull this out into a function
        if operator.lhs.actualType is not IntegerType:
            self.insertCast(operator.lhs, source=operator.lhs.actualType, target=IntegerType)
        if operator.rhs.actualType is not IntegerType:
            self.insertCast(operator.rhs, source=operator.rhs.actualType, target=IntegerType)
    
    def visitDyadicIndirection(self, dyadic):
        self.visit(dyadic.base)
        self.visit(dyadic.offset)
        if not self.checkSignature(dyadic):
            return
        self.insertNumericCasts(dyadic)
        
         
    def visitUnaryNumericFunc(self, func):
        self.visit(func.factor)
        if not self.checkSignature(func):
            return
        if func.factor.actualType is IntegerType:
            self.insertCast(func.factor, source=func.factor.actualType, target=FloatType)
            
    def visitIntFunc(self, func):
        self.visit(func.factor)
        if not self.checkSignature(func):
            return
        if func.factor.actualType is IntegerType:
            elideNode(func)
    
    def visitNot(self, operator):
        self.visit(operator.factor)
        if not self.checkSignature(operator):
            return
        if operator.factor.actualType is not IntegerType:
            self.insertCast(operator.factor, source = operator.factor.actualType, target=IntegerType)
    
    def visitInstr(self, instr):
        self.visit(instr.source)
        self.visit(instr.subString)
        self.visit(instr.startPosition)
        if not self.checkSignature(instr):
            return
        if instr.startPosition is not None and instr.startPosition.actualType is not IntegerType:
            self.insertCast(instr.startPosition, source = instr.startPosition.actualType, target = IntegerType)
    
    def visitUserFunc(self, func):
        # TODO Add to a list of user defined functions to be typechecked
        print "func.actualParameters = %s at line %s" % (func.actualParameters, func.lineNum)
        
        for parameter in func.actualParameters:
            self.visit(parameter)
    
    def insertNumericCasts(self, node):
        """
        Where an Integer value is being passed to a parameter of Numeric type,
        insert an Integer->Float cast operation.
        """
        for name, child in node.children.items():
            if child is not None:
                if isinstance(child, list):
                    formal_type = node.child_infos[name][0].formalType
                    if formal_type is not None:
                        if formal_type.isA(NumericType):
                            for subchild in child:
                                self.insertCast(subchild, source=subchild.actualType, target=formal_type)
                        else:
                            sys.stderr.write("Compiler construction: Missing formal type information on %s, %s\n" % (node, name))
                else:
                    formal_type = node.child_infos[name].formalType
                    if formal_type is not None:
                        if formal_type.isA(NumericType):
                            self.insertCast(child, source=child.actualType, target=formal_type)
                        else:
                            sys.stderr.write("Compiler construction: Missing formal type information on %s, %s\n" % (node, name))
            
    def insertCast(self, child, source, target):
        """Wrap the supplied node is a Cast node from source type to target type"""
        if source is target:
            return
        
        if source is FloatType and target is IntegerType:
            message = "of %s to %s, possible loss of data" % (source.__doc__, target.__doc__)
            self.castWarning(child, message)
        
        parent = child.parent
        parent_property = child.parent_property
        parent_index    = child.parent_index
        cast = Cast(sourceType=source, targetType=target, value=child)
        cast.lineNum = parent.lineNum
        # TODO: Tidy up this redundancy!
        cast.formalType = cast.targetType
        cast.actualType = cast.formalType
        cast.parent = parent
        cast.parent_property = parent_property
        cast.parent_index = parent_index
        cast.value.parent = cast
        cast.value.parent_property = "value"
        cast.value.parent_index = None
        parent.setProperty(cast, parent_property, parent_index)
        
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
            sigil = identifier[-2:-1]
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
        print "node = %s at line %s" % (node, node.lineNum)
        result = True
        for name, info in node.child_infos.items():
            print "name = %s" % name
            if isinstance(info, list):
                info = info[0]
                formal_type = info.formalType
                child_nodes = getattr(node, underscoresToCamelCase(name))
                if child_nodes is not None:
                    for child_node in child_nodes:
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
        if child_node is not None:
            actual_type = child_node.actualType
            if formal_type is not None: # None types do not need to be checked
                if actual_type is not None:
                    if not actual_type.isConvertibleTo(formal_type):
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
        
        