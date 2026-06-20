# A visitor for performing type-checking over the Abstract Syntax Tree

import logging

from owl_basic.visitor import Visitor
from owl_basic.errors import *
from owl_basic.exceptions import CompileError
from owl_basic.utility import underscoresToCamelCase
from owl_basic.syntax.ast import Cast, Concatenate, LiteralInteger
from owl_basic.ast_utils import elideNode
from owl_basic.owltyping.type_system import (NumericOwlType, ObjectOwlType, IntegerOwlType,
                                LongIntegerOwlType, FloatOwlType, ByteOwlType, PendingOwlType,
                                StringOwlType, ArrayOwlType)

_INT32_MIN = -2147483648
_INT32_MAX = 2147483647
_INT64_MIN = -(2 ** 63)
_INT64_MAX = 2 ** 63 - 1


def _integer_range(owl_type):
    '''The (min, max) range of an integer storage type, or None if the type is
    not a fixed-width integer (so no range check applies).'''
    if isinstance(owl_type, ByteOwlType):
        return (0, 255)
    if isinstance(owl_type, LongIntegerOwlType):
        return (_INT64_MIN, _INT64_MAX)
    if isinstance(owl_type, IntegerOwlType):   # ChannelOwlType is an int32 too
        return (_INT32_MIN, _INT32_MAX)
    return None

# Integer arithmetic that is safe to fold at compile time. DIV/MOD are left to
# the runtime so their truncate-toward-zero sign behaviour is defined in exactly
# one place; only the overflow-prone additive/multiplicative ops fold here.
_FOLD_OPS = {
    "Plus": lambda a, b: a + b,
    "Minus": lambda a, b: a - b,
    "Multiply": lambda a, b: a * b,
}

# Additive/multiplicative operators on two 32-bit integers are evaluated in 64
# bits so they cannot overflow at 32; the result narrows (checked) only when
# stored to a 32-bit variable. These are exactly the operators that can grow a
# value beyond its operands' width.
_WIDENING_OPS = frozenset(_FOLD_OPS)
from owl_basic import sigil

logger = logging.getLogger('owltyping.typecheck_visitor')

class TypecheckVisitor(Visitor):
    """
    AST visitor for determining the actual type of each node
    """
    def __init__(self, entry_points, report_diagnostics=True):
        '''
        :param entry_points: A dictionary of entry_point names to AstStatements.
        :param report_diagnostics: Whether to emit type errors/warnings. The
            first of the two typecheck passes synthesises types with every
            user-function call still Pending, so any mismatch it sees may be an
            artifact of inference not having run yet; it runs with this False and
            stays silent. The second, authoritative pass (types resolved) reports.
        '''
        self.__entry_points = entry_points
        self.__report_diagnostics = report_diagnostics
    
    def visit(self, node):
        "Override visit to allow safe traversal of lists"
        if isinstance(node, list):
            for elem in node:
                self.visit(elem)
        else:
            super(TypecheckVisitor, self).visit(node)
    
    def visitAstNode(self, node):
        node.forEachChild(self.visit)
        self.checkSignature(node) # TODO: What about return types
        self.insertNumericCasts(node)
    
    def visitAstStatement(self, statement):
        "Generic visitor for simple statements"
        # TODO: If this is the same as above, it can be removed
        statement.forEachChild(self.visit)      
        if not self.checkSignature(statement):
            return
        self.insertNumericCasts(statement)
        
    def visitAssignment(self, assignment):
        # Determine the actual type of the lValue and rValue
        
        self.visit(assignment.lValue)
        self.visit(assignment.rValue)
        # @% takes either the packed integer control word or a printf-style
        # format string (later BBC BASIC); the backend routes each form, so no
        # scalar cast to the variable's nominal integer type is wanted here.
        if (type(assignment.lValue).__name__ == "Variable"
                and getattr(assignment.lValue, "identifier", None) == "@%"):
            return
        if isinstance(assignment.rValue, list):
            # A whole-array assignment: A() = <expr-list>. Scalar operands are
            # cast to the element type (fill/init); a whole-array operand (e.g.
            # the B() of A() = B()) is left alone -- it is applied element-wise.
            if assignment.lValue.actualType.isArray():
                element_type = assignment.lValue.actualType.elementType()
                for item in assignment.rValue:
                    item_type = getattr(item, "actualType", None)
                    if item_type is not None and item_type.isArray():
                        continue
                    self.checkAndInsertRValueCast(item, element_type)
            else:
                message = "List is only assignable to an array"
                self.typeMismatch(assignment, message)
        else:
            logger.debug(assignment.lValue)
            self.checkAndInsertRValueCast(assignment.rValue, assignment.lValue.actualType)
        
    def visitForToStep(self, for_stmt):
        '''
        Visit FOR N=1 TO 10 STEP 2
        '''
        self.visit(for_stmt.identifier)
        self.visit(for_stmt.first)
        self.visit(for_stmt.last)
        self.visit(for_stmt.step)
        counter_type = for_stmt.identifier.actualType
        self.checkAndInsertRValueCast(for_stmt.first, counter_type)
        self.checkAndInsertRValueCast(for_stmt.last, counter_type)
        self.checkAndInsertRValueCast(for_stmt.step, counter_type)
    
    def visitBinaryNumericOperator(self, operator):
        '''
        Visit - * / ^
        '''
        self.visit(operator.lhs)
        self.visit(operator.rhs)
        if self._foldConstant(operator):
            return
        # TODO: Propagate pending types
        self.determineNumericResultType(operator)
        self.promoteNumericOperands(operator)

    def _foldConstant(self, operator):
        '''
        If an additive/multiplicative operator has two integer-literal operands,
        replace it with the folded constant. The fold is done in arbitrary
        precision and typed by magnitude, so a product that overflows 32 bits
        becomes a 64-bit literal (e.g. 100000*80500 -> 8050000000) rather than
        wrapping. Returns True if the node was folded and replaced.
        '''
        fold = _FOLD_OPS.get(type(operator).__name__)
        if fold is None:
            return False
        lhs, rhs = operator.lhs, operator.rhs
        if not (isinstance(lhs, LiteralInteger) and isinstance(rhs, LiteralInteger)):
            return False
        value = fold(lhs.value, rhs.value)
        literal = LiteralInteger(value=value)
        literal.lineNum = operator.lineNum
        literal.actualType = (IntegerOwlType() if _INT32_MIN <= value <= _INT32_MAX
                              else LongIntegerOwlType())
        literal.parent = operator.parent
        literal.parent_property = operator.parent_property
        literal.parent_index = operator.parent_index
        operator.parent.setProperty(literal, operator.parent_property, operator.parent_index)
        return True
                
    def visitDivide(self, divide):
        '''
        Specialization of visitBinaryNumericOperator: BBC BASIC '/' is always
        real division, even for integer operands (1/10 == 0.1), unlike DIV.
        Promote both operands to float and yield a float result.
        '''
        self.visit(divide.lhs)
        self.visit(divide.rhs)
        if divide.lhs.actualType == PendingOwlType() or divide.rhs.actualType == PendingOwlType():
            divide.actualType = PendingOwlType()
            return
        self.insertCast(divide.lhs, source=divide.lhs.actualType, target=FloatOwlType())
        self.insertCast(divide.rhs, source=divide.rhs.actualType, target=FloatOwlType())
        divide.actualType = FloatOwlType()

    def visitPower(self, power):
        '''
        Specialization of visitBinaryNumericOperator: BBC BASIC '^'
        (exponentiation) always yields a real, even for integer operands
        (2^3 == 8.0). Promote both operands to float; the result is float.
        '''
        self.visit(power.lhs)
        self.visit(power.rhs)
        if power.lhs.actualType == PendingOwlType() or power.rhs.actualType == PendingOwlType():
            power.actualType = PendingOwlType()
            return
        self.insertCast(power.lhs, source=power.lhs.actualType, target=FloatOwlType())
        self.insertCast(power.rhs, source=power.rhs.actualType, target=FloatOwlType())
        power.actualType = FloatOwlType()

    def visitLiteralInteger(self, node):
        '''
        An integer literal too large for the 32-bit range is a 64-bit integer
        (a LongInteger), so e.g. PRINT 5000000000 does not overflow.
        '''
        if not (_INT32_MIN <= node.value <= _INT32_MAX):
            node.actualType = LongIntegerOwlType()

    def visitPlus(self, plus):
        '''
        Specialization of visitBinaryNumericOperator to handle string concatenation
        '''
        # Determine the actual type of sub-expressions
        self.visit(plus.lhs)
        self.visit(plus.rhs)
        
        # If this is a string concatenation, convert the node and re-visit
        if plus.lhs.actualType == StringOwlType() and plus.rhs.actualType == StringOwlType():
            # TODO: Create a function in ast_utils to replace a node
            concat = Concatenate(lhs = plus.lhs, rhs = plus.rhs)
            concat.lhs.parent = concat
            concat.rhs.parent = concat
            concat.parent = plus.parent
            plus.parent.setProperty(concat, plus.parent_property, plus.parent_index)
            self.visit(concat)
            return

        if self._foldConstant(plus):
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
        operator.actualType = IntegerOwlType()
                        
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
        # Re-read each index from the list after visiting: constant folding may
        # have replaced the index node in place (e.g. A%(2+3) -> A%(5)). The
        # indices may be a bare list or an ExpressionList (an array-element
        # l-value formal/LOCAL keeps the ExpressionList); use its element list.
        indices = getattr(indexer.indices, "expressions", indexer.indices)
        for i in range(len(indices)):
            self.visit(indices[i])
            self.checkAndInsertRValueCast(indices[i], IntegerOwlType())
    
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
            if target.actualType.isConvertibleTo(IntegerOwlType()):
                self.insertCast(target, target.actualType, IntegerOwlType())
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
        # DIV/MOD, the bitwise operators and shifts operate at the width of the
        # wider operand: 64-bit if either operand is a LongInteger, else 32-bit.
        # The narrower operand widens to match (lossless); the polymorphic CIL
        # opcodes (div/rem/and/or/xor) then compute at that width.
        if (isinstance(operator.lhs.actualType, LongIntegerOwlType)
                or isinstance(operator.rhs.actualType, LongIntegerOwlType)):
            target = LongIntegerOwlType()
        else:
            target = IntegerOwlType()
        if operator.lhs.actualType != target:
            self.insertCast(operator.lhs, source=operator.lhs.actualType, target=target)
        if operator.rhs.actualType != target:
            self.insertCast(operator.rhs, source=operator.rhs.actualType, target=target)
        operator.actualType = target
    
    def visitDyadicIndirection(self, dyadic):
        self.visit(dyadic.base)
        self.visit(dyadic.offset)
        if not self.checkSignature(dyadic):
            # TODO: Error?
            return
        self.insertNumericCasts(dyadic)
        
         
    def visitUnaryNumericFunc(self, func):
        self.visit(func.factor)
        if not self.checkSignature(func):
            # TODO: Error?
            return
        if func.factor.actualType == IntegerOwlType():
            self.insertCast(func.factor, source=func.factor.actualType, target=FloatOwlType())
            
    def visitAbsFunc(self, abs):
        '''
        Check that the argument is numeric.  If so, propagate the type of the argument to
        the type of the ABS function.
        '''
        self.visit(abs.factor)
        if not self.checkSignature(abs):
            # TODO: Error?
            return
        abs.actualType = abs.factor.actualType
            
    def visitIntFunc(self, func):
        self.visit(func.factor)
        if not self.checkSignature(func):
            # TODO: Error?
            return
        if func.factor.actualType == IntegerOwlType():
            elideNode(func)
    
    def visitNot(self, operator):
        self.visit(operator.factor)
        if not self.checkSignature(operator):
            # TODO: Error?
            return
        if operator.factor.actualType != IntegerOwlType():
            self.insertCast(operator.factor, source = operator.factor.actualType, target=IntegerOwlType())
    
    def visitInstr(self, instr):
        self.visit(instr.source)
        self.visit(instr.subString)
        self.visit(instr.startPosition)
        if not self.checkSignature(instr):
            # TODO: Error?
            return
        if instr.startPosition is not None and instr.startPosition.actualType != IntegerOwlType():
            self.insertCast(instr.startPosition, source = instr.startPosition.actualType, target = IntegerOwlType())
        
    def visitReadFunc(self, read_func):
        # Infer the type of ReadFunc in x = ReadFunc from the type of x
        # This depends on the type of the lValue of the assignment having been
        # determined previously, and assumes that the parent of ReadFunc is always 
        # an Assignment
        read_func.actualType = read_func.parent.lValue.actualType
        
    def visitUserFunc(self, user_func):
        if user_func.actualParameters:
            self.visit(user_func.actualParameters)
            # TODO: Check argument types against Procedure
            # TODO: This needs different code for internal and external linkage
            self.checkActualParameters(user_func)
        # The function's return type is inferred between typecheck passes; until
        # it is known the call stays Pending (so operators over it stay Pending).
        entry_point = self.__entry_points.get(user_func.name)
        inferred = getattr(entry_point, "returnType", None)
        if inferred is not None and not inferred.isA(PendingOwlType()):
            user_func.actualType = inferred
        else:
            user_func.actualType = PendingOwlType()
    
    def visitCallProcedure(self, proc):
        if proc.actualParameters:
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
        # Lookup the callable and retrieve its formal parameters
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
                    message = "Cannot pass actual parameter number %d of type %s to formal parameter type of %s" % (n, actual.actualType.__doc__, formal.argument.actualType.__doc__)
                    self.typeMismatch(call, message)
                n += 1 
        elif self.__report_diagnostics:
            # An unknown callable: name a function FNx / procedure PROCx clearly,
            # and only from the authoritative second pass (the first may not have
            # walked the definition yet).
            kind, bare = (("function", call.name[2:]) if call.name.startswith("FN")
                          else ("procedure", call.name[4:])
                          if call.name.startswith("PROC") else ("routine", call.name))
            error("Call to undefined %s '%s': no DEF %s is defined"
                  % (kind, bare, call.name))
    
    def determineNumericResultType(self, operator):    
        if operator.lhs.actualType == PendingOwlType() or operator.rhs.actualType == PendingOwlType():
            operator.actualType = PendingOwlType()
            return

        if not self.checkSignature(operator):
            # An operand is the wrong kind (e.g. 1 + "x"). checkSignature has
            # already reported the mismatch; give the result the boxed Object
            # type so it is not left untyped -- an untyped node cascades into a
            # "no type information" internal error and crashes the compiler.
            operator.actualType = ObjectOwlType()
            return
        
        def opTypes(lhs_type, rhs_type):
            return operator.lhs.actualType.isA(lhs_type) and operator.rhs.actualType.isA(rhs_type)

        # +, -, * of two 32-bit integers are evaluated in 64 bits so they do not
        # wrap; the result narrows back (checked) only on store to a 32-bit var.
        if (type(operator).__name__ in _WIDENING_OPS
                and opTypes(IntegerOwlType(), IntegerOwlType())):
            operator.actualType = LongIntegerOwlType()
            return

        if   opTypes(ObjectOwlType(),  NumericOwlType()) : operator.actualType = FloatOwlType()
        elif opTypes(NumericOwlType(), ObjectOwlType())  : operator.actualType = FloatOwlType()
        elif opTypes(IntegerOwlType(), FloatOwlType())   : operator.actualType = FloatOwlType()
        elif opTypes(FloatOwlType(),   IntegerOwlType()) : operator.actualType = FloatOwlType()
        # A byte (e.g. from ? indirection) acts as an integer in arithmetic and
        # promotes along byte < integer < float when mixed with a wider type.
        elif opTypes(ByteOwlType(),    FloatOwlType())   : operator.actualType = FloatOwlType()
        elif opTypes(FloatOwlType(),   ByteOwlType())    : operator.actualType = FloatOwlType()
        elif opTypes(ByteOwlType(),    IntegerOwlType()) : operator.actualType = IntegerOwlType()
        elif opTypes(IntegerOwlType(), ByteOwlType())    : operator.actualType = IntegerOwlType()
        elif opTypes(ByteOwlType(),    ByteOwlType())    : operator.actualType = IntegerOwlType()
        # A 64-bit LongInteger dominates narrower integers; mixed with a float
        # it promotes to float (which may lose precision above 2^53).
        elif opTypes(LongIntegerOwlType(), FloatOwlType())   : operator.actualType = FloatOwlType()
        elif opTypes(FloatOwlType(),   LongIntegerOwlType()) : operator.actualType = FloatOwlType()
        elif opTypes(LongIntegerOwlType(), IntegerOwlType()) : operator.actualType = LongIntegerOwlType()
        elif opTypes(IntegerOwlType(), LongIntegerOwlType()) : operator.actualType = LongIntegerOwlType()
        elif opTypes(LongIntegerOwlType(), ByteOwlType())    : operator.actualType = LongIntegerOwlType()
        elif opTypes(ByteOwlType(),    LongIntegerOwlType()) : operator.actualType = LongIntegerOwlType()
        elif operator.lhs.actualType == operator.rhs.actualType:
            operator.actualType = operator.lhs.actualType
        else:
            message = "Cannot apply operator %s to operands of type of %s and %s" % (operator.__doc__, operator.lhs.actualType.__doc__, operator.rhs.actualType.__doc__)
            self.typeMismatch(operator, message)
            operator.actualType = ObjectOwlType()  # boxed fallback; do not leave untyped
                       
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
        def opTypes(lhs_type, rhs_type):
            return operator.lhs.actualType.isA(lhs_type) and operator.rhs.actualType.isA(rhs_type)

        # A widening +, -, * over two 32-bit integers: widen both to 64 bits so
        # the operation is computed without wrapping (cf. determineNumericResultType).
        if (type(operator).__name__ in _WIDENING_OPS
                and opTypes(IntegerOwlType(), IntegerOwlType())):
            self.insertCast(operator.lhs, source=IntegerOwlType(), target=LongIntegerOwlType())
            self.insertCast(operator.rhs, source=IntegerOwlType(), target=LongIntegerOwlType())
            return

        if opTypes(IntegerOwlType(), FloatOwlType()):
            self.insertCast(operator.lhs, source=IntegerOwlType(), target=FloatOwlType())
        elif opTypes(ByteOwlType(), FloatOwlType()):
            self.insertCast(operator.lhs, source=ByteOwlType(), target=FloatOwlType())
        elif opTypes(FloatOwlType(), IntegerOwlType()):
            self.insertCast(operator.rhs, source=IntegerOwlType(), target=FloatOwlType())
        elif opTypes(FloatOwlType(), ByteOwlType()):
            self.insertCast(operator.rhs, source=ByteOwlType(), target=FloatOwlType())
        # A byte acts as an integer in arithmetic: widen it so the operands match.
        elif opTypes(ByteOwlType(), IntegerOwlType()):
            self.insertCast(operator.lhs, source=ByteOwlType(), target=IntegerOwlType())
        elif opTypes(IntegerOwlType(), ByteOwlType()):
            self.insertCast(operator.rhs, source=ByteOwlType(), target=IntegerOwlType())
        elif opTypes(ByteOwlType(), ByteOwlType()):
            self.insertCast(operator.lhs, source=ByteOwlType(), target=IntegerOwlType())
            self.insertCast(operator.rhs, source=ByteOwlType(), target=IntegerOwlType())
        # Widen the narrower operand to 64 bits (or to float) so both match.
        elif opTypes(IntegerOwlType(), LongIntegerOwlType()):
            self.insertCast(operator.lhs, source=IntegerOwlType(), target=LongIntegerOwlType())
        elif opTypes(LongIntegerOwlType(), IntegerOwlType()):
            self.insertCast(operator.rhs, source=IntegerOwlType(), target=LongIntegerOwlType())
        elif opTypes(ByteOwlType(), LongIntegerOwlType()):
            self.insertCast(operator.lhs, source=ByteOwlType(), target=LongIntegerOwlType())
        elif opTypes(LongIntegerOwlType(), ByteOwlType()):
            self.insertCast(operator.rhs, source=ByteOwlType(), target=LongIntegerOwlType())
        elif opTypes(LongIntegerOwlType(), FloatOwlType()):
            self.insertCast(operator.lhs, source=LongIntegerOwlType(), target=FloatOwlType())
        elif opTypes(FloatOwlType(), LongIntegerOwlType()):
            self.insertCast(operator.rhs, source=LongIntegerOwlType(), target=FloatOwlType())
    
    def insertNumericCasts(self, node):
        """
        Where an Integer value is being passed to a parameter of Numeric type,
        insert an Integer->Float cast operation.
        """
        for name, child in list(node.children.items()):
            if child is not None:
                if isinstance(child, list):
                    formal_type = node.child_infos[name][0].formalType
                    if formal_type is not None:
                        if formal_type.isA(NumericOwlType()):
                            for subchild in child:
                                self.insertCast(subchild, source=subchild.actualType, target=formal_type)
                        else:
                            sys.stderr.write("Compiler construction: Missing formal type information on %s, %s\n" % (node, name))
                else:
                    formal_type = node.child_infos[name].formalType
                    if formal_type is not None:
                        if formal_type.isA(NumericOwlType()):
                            self.insertCast(child, source=child.actualType, target=formal_type)
                        else:
                            sys.stderr.write("Compiler construction: Missing formal type information on %s, %s\n" % (node, name))
            
    def insertCast(self, child, source, target):
        """Wrap the supplied node in a Cast node from source type to target type"""
       
        if source is target:
            return
        
        if source.isA(PendingOwlType()):
            logging.debug("Ignoring request to insert cast from PendingType")
            return
               
        if source.isA(target):
            # Implicit conversion allowed, no cast needed
            logging.debug("%s implicitly converted to %s" % (source, target))
            return
        
        if source.isA(NumericOwlType()) and target.isA(NumericOwlType()):
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
        for name, info in list(node.child_infos.items()):
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
            logger.debug("child_node = %s" % child_node)
            actual_type = child_node.actualType
            logger.debug("formal_type = %s" % formal_type)
            logger.debug("actual_type = %s" % actual_type)
            if formal_type is not None: # None types do not need to be checked
                if actual_type is not None:
                    if not actual_type.isConvertibleTo(formal_type):
                        message = "%s of %s is incompatible with supplied parameter of type %s at line %s" % (info.description, node.description, actual_type.__doc__, node.lineNum)
                        self.typeMismatch(node, message)
                        return False
                else:
                    
                    message = "%s of %s has no type information" % (info.description, node.description)
                    self.typeError(node, message)
                    return False
        return True
    
    def checkAndInsertRValueCast(self, r_value, target_type):
        '''
        Check the value of the given r_value for compatibility with the target_type
        and insert casts as necessary, or raise an error if no conversion is possible.
        :param r_value: The r_value Node which is to be type checked. 
        :param target_type: The type to which the r_value should be converted.
        '''
        assert target_type is not None
        if r_value is not None: # TODO Could this be an assert?
            self._checkConstantInRange(r_value, target_type)
            if r_value.actualType.isConvertibleTo(target_type):
                if r_value.actualType is not target_type:
                    self.insertCast(r_value, r_value.actualType, target_type)
            else:
                message = "Cannot assign %s to %s" % (r_value.actualType.__doc__, target_type.__doc__)
                self.typeMismatch(r_value, message)
                
    def _checkConstantInRange(self, r_value, target_type):
        '''
        A constant (an integer literal, possibly the result of folding) stored
        into a narrower integer variable is an error the compiler can prove now,
        rather than truncating silently: A% = 100000*80500 is rejected at
        compile time. Dynamic (non-constant) narrowing is checked at runtime.
        '''
        if not isinstance(r_value, LiteralInteger):
            return
        bounds = _integer_range(target_type)
        if bounds is None:
            return
        low, high = bounds
        if not (low <= r_value.value <= high):
            raise CompileError(
                "constant %d is out of range for %s at line %s"
                % (r_value.value, target_type.__doc__, r_value.lineNum))

    def typeError(self, node, message):
        if not self.__report_diagnostics:
            return  # first (synthesis) pass: types not yet resolved, stay silent
        message = "%s at line %d" % (message, node.lineNum)
        internal(message)

    def typeMismatch(self, node, message):
        if not self.__report_diagnostics:
            return  # first (synthesis) pass: a Pending call is not a real mismatch
        message = "Type mismatch: %s at line %s" % (message, node.lineNum)
        error(message)

    def castWarning(self, node, message):
        if not self.__report_diagnostics:
            return  # first (synthesis) pass: defer to the authoritative second pass
        message = "Implicit conversion %s at line %s" % (message, node.lineNum)
        warning(message)
        
        