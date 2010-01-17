'''
Functions which emit the most optimal OpCodes.
'''

import clr
import System
from System.Reflection.Emit import *

def emitLdarg(generator, index):
    assert 0 <= index <= 65535
    if index == 0:
        generator.Emit(OpCodes.Ldarg_0)
    elif index == 1:
        generator.Emit(OpCodes.Ldarg_1)
    elif index == 2:
        generator.Emit(OpCodes.Ldarg_2)
    elif index == 3:
        generator.Emit(OpCodes.Ldarg_3)
    elif 3 < index <= 255:
        generator.Emit.Overloads[OpCode, System.Byte](OpCodes.LdArg_S, System.Byte(index))
    else:
        generator.Emit(OpCodes.LdArg, index)

def emitLdc_I4(generator, constant):
    assert -2147483648 <= constant <= 2147483647
    if constant == -1:
        generator.Emit(OpCodes.Ldc_I4_M1)  
    elif constant == 0:
        generator.Emit(OpCodes.Ldc_I4_0)
    elif constant == 1:
        generator.Emit(OpCodes.Ldc_I4_1)
    elif constant == 2:
        generator.Emit(OpCodes.Ldc_I4_2)
    elif constant == 3:
        generator.Emit(OpCodes.Ldc_I4_3)
    elif constant == 4:
        generator.Emit(OpCodes.Ldc_I4_4)
    elif constant == 5:
        generator.Emit(OpCodes.Ldc_I4_5)
    elif constant == 6:
        generator.Emit(OpCodes.Ldc_I4_6)
    elif constant == 7:
        generator.Emit(OpCodes.Ldc_I4_7)
    elif constant == 8:
        generator.Emit(OpCodes.Ldc_I4_8)
    elif -128 <= constant <= 127:
        generator.Emit.Overloads[OpCode, System.SByte](OpCodes.Ldc_I4_S, System.SByte(constant))
    else:
        generator.Emit(OpCodes.Ldc_I4, constant)
    
def emitStarg(generator, index):
    assert 0 <= index <= 65535
    if index <= 255:
        generator.Emit[OpCode, System.Byte](OpCodes.Starg_S, System.SByte(index))
    else:
        generator.Emit(OpCodes.Starg, index)

