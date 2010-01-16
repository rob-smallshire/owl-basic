# A visitor for performing type-checking over the Abstract Syntax Tree

from visitor import Visitor
from errors import *
from utility import underscoresToCamelCase
from bbc_types import *
from bbc_ast import Cast, Concatenate
from ast_utils import elideNode
import sigil

class TypecheckVisitor(Visitor):
    """
    AST visitor for determining the actual type of each node
    """
    def __init__(self, entry_points):
        '''
        :param entry_points: A dictionary of entry_point names to AstStatements.
        '''
        self.__entry_points = entry_points
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
            if assignment.rValue.actualType.isConvertibleTo(assignment.lValue.actualType):
                if assignment.rValue.actualType is not assignment.lValue.actualType:
                    self.insertCast(assignment.rValue, assignment.rValue.actualType, assignment.lValue.actualType)
            else:
                message = "Cannot assign %s to %s" % (assignment.rValue.actualType.__doc__, assignment.lValue.actualType.__doc__)
                self.typeMismatch(assignment, message)
    
    def visitBinaryNumericOperator(self, operator):
        '''
        Visit - * / ^
        '''
        self.visit(operator.lhs)
        self.visit(operator.rhs)
        # TODO: Propagate pending types
        self.determineNumericResultType(operator)
        self.promoteNumericOperands(operator)
                
    def visitPlus(self, plus):
        '''
        Specialization of visitBinaryNumericOperator to handle string concatenation
        '''
        # Determine the actual type of sub-expressions
        self.visit(plus.lhs)
        self.visit(plus.rhs)
        
        # If this is a string concatenation, convert the node and re-visit
        if plus.lhs.actualType == StringType and plus.rhs.actualType == StringType:
            # TODO: Create a function in ast_utils to replace a node
            concat = Concatenate(lhs = plus.lhs, rhs = plus.rhs)
            concat.lhs.parent = concat
            concat.rhs.parent = concat
            concat.parent = plus.parent
            plus.parent.setProperty(concat, plus.parent_property, plus.parent_index)
            self.visit(concat)
            return
        
        self.determineNumericResultType(plus)
        self.promoteNumericOperands(plus)
        
    def visitRelationalOperator(self, operator):
        '''
        Visit = <> < > <= >=
        '''        
        self.visit(operator.lhs)
        self.visit(operator.rhs)
        
        if not (operator.lhs.actualType.isConvertibleTo(operator.rhs.actualType) or operator.rhs.actualType.isConvertibleTo(operator.lhs.actualType)):
            message = "Cannot compare %s with %s using operator %s" % (operator.lhs.actualType.__doc__, operator.rhs.actualType.__doc__, operator.__doc__)
            self.typeMismatch(operator, message)
        
        self.promoteNumericOperands(operator)
        operator.actualType = IntegerType
                        
    def visitArray(self, array):
        # Decode the variable name sigil into the actual type
        # The sigils are one of [$%&~]
        array.actualType = sigil.identifierToType(array.identifier)
    
    def visitVariable(self, variable):
        # Decode the variable name sigil into the actual type
        # The sigils are one of [$%&~]
        variable.actualType = sigil.identifierToType(variable.identifier)
        
    def visitIndexer(self, indexer):
        # Decode the variable name sigil into the actual type
        # The sigils are one of [$%&~]
        indexer.actualType = sigil.identifierToType(indexer.identifier[:-1])
    
    def visitIf(self, iff):
        # TODO: Does this do anything that visitAstNode doesn't do?
        self.visit(iff.condition)
        self.visit(iff.trueClause)
        self.visit(iff.falseClause)
        condition_formal_type = iff.child_infos['condition'].formalType
        if iff.condition.actualType.isConvertibleTo(condition_formal_type):
            self.insertCast(iff.condition, iff.condition.actualType, condition_formal_type)
        else:
            self.typeMismatch(iff, "Conditional expression must be convertible to %s." % condition_formal_type.__doc__)
    
    def visitOnGoto(self, ongoto):
        # TODO: Does this do anything that visitAstNode doesn't do?
        self.visit(ongoto.switch)
        switch_formal_type = ongoto.child_infos['switch'].formalType
        if ongoto.switch.actualType.isConvertibleTo(switch_formal_type):
            self.insertCast(ongoto.switch, ongoto.switch.actualType, switch_formal_type)
        else:
            self.typeMismatch(ongoto, "Selector expression must be convertible to %s" % switch_formal_type.__doc__)
        
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
            
    def visitAbsFunc(self, abs):
        '''
        Check that the argument is numeric.  If so, propagate the type of the argument to
        the type of the ABS function.
        '''
        self.visit(abs.factor)
        if not self.checkSignature(abs):
            return
        abs.actualType = abs.factor.actualType
            
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
        for parameter in func.actualParameters:
            self.visit(parameter)
    
    def visitReadFunc(self, read_func):
        # Infer the type of ReadFunc in x = ReadFunc from the type of x
        # This depends on the type of the lValue of the assignment having been
        # determined previously, and assumes that the parent of ReadFunc is always 
        # an Assignment
        read_func.actualType = read_func.parent.lValue.actualType
        
    def visitUserFunc(self, user_func):
        self.visit(user_func.actualParameters)
        # TODO: Check argument types against Procedure
        # TODO: This needs different code for internal and external linkage
        self.checkActualParameters(user_func)
    
    def visitCallProcedure(self, proc):
        self.visit(proc.actualParameters)
        # TODO: Check argument types against Procedure
        # TODO: This needs different code for internal and external linkage
        self.checkActualParameters(proc)
        
    def checkActualParameters(self, call):
        '''
        Check the actualParameters of 'call' against the formal parameters
        of the callable.
        :param call: An AstNode with an actualParameters property and a name property
        :returns: True is the actual parameter types are compatible with the formal parameter types, otherwise False
        '''
        # Lookup the callable and retrieve its formal paramaters
        if call.name in self.__entry_points:
            callable = self.__entry_points[call.name]
            n = 1
            for actual, formal in zip(call.actualParameters,
                                      callable.formalParameters.arguments):
                if formal.argument.actualType is None:
                    # There is no type information on the callable yet, so visit it
                    self.visit(callable)
                if actual.actualType.isConvertibleTo(formal.argument.actualType):
                    self.insertCast(actual, source=actual.actualType, target=formal.argument.actualType)
                else:
                    message = "Cannot pass actual parameter number %d of type %s to formal parameter type of %s" % (actual.actualType.__doc__, formal.argument.actualType.__doc__)
                    self.typeMismatch(call, message)
                n += 1

                    
                
                
        else:
            error("Did not find entry point for %s" % callable.name)
        
        # Check each formal parameter against an actual parameter
        pass
    
    def determineNumericResultType(self, operator):    
        if not self.checkSignature(operator):
            return
        
        def opTypes(lhs_type, rhs_type):
            return operator.lhs.actualType.isA(lhs_type) and operator.rhs.actualType.isA(rhs_type)

        if   opTypes(ObjectType,  NumericType) : operator.actualType = FloatType
        elif opTypes(NumericType, ObjectType)  : operator.actualType = FloatType
        elif opTypes(IntegerType, FloatType)   : operator.actualType = FloatType
        elif opTypes(FloatType,   IntegerType) : operator.actualType = FloatType
        elif operator.lhs.actualType == operator.rhs.actualType:
            operator.actualType = operator.lhs.actualType
        else:
            message = "Cannot apply operator %s to operands of type of %s and %s" % (operator.__doc__, operator.lhs.actualType.__doc__, operator.rhs.actualType.__doc__)
            self.typeMismatch(operator, message)    
                   
    def promoteNumericOperands(self, operator):
        '''
        Given a binary operator with lhs and rhs operands, if the operands are of
        NumericType, insert casts as necessary to promote operands as necessary to
        FloatType from IntegerType in the case of mixed operand types.
        e.g. Int op Int     => Int op Int
             Float op Float => Float op Float
             Float op Int   => Float op Float
             Int op FLoat   => Float op Float
        '''
        # TODO: Handle byte types - use the precision of the types to decide how to promote...
        def opTypes(lhs_type, rhs_type):
            return operator.lhs.actualType.isA(lhs_type) and operator.rhs.actualType.isA(rhs_type)
        
        if opTypes(IntegerType, FloatType):
            self.insertCast(operator.lhs, source=IntegerType, target=FloatType)
        elif opTypes(FloatType, IntegerType):
            self.insertCast(operator.rhs, source=IntegerType, target=FloatType)
    
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
        """Wrap the supplied node in a Cast node from source type to target type"""
       
        if source is target:
            return
               
        if source.isA(target):
            # Implicit conversion allowed, no cast needed
            logging.debug("%s implicitly converted to %s" % (source, target))
            return
        
        if source.isA(NumericType) and target.isA(NumericType):
            if target.bitsIntegerPrecision() < source.bitsIntegerPrecision():
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
        
        