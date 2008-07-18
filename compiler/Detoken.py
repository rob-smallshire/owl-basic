#!/usr/bin/env python
#
# (c) 2007 Matt Godbolt.
#
# Updated 2008 Ian Smallshire.
#
# Use however you like, as long as you put credit where credit's due.
# Some information obtained from source code from RISC OS Open.
# v0.01 - first release.  Doesn't deal with GOTO line numbers.
# v0.02 - edited to output line numbers where needed and fixed
#         the GOTO/RESTORE/GOSUB line numbers.
# v0.03 - Added file type detection for input and provision
#         for BB4W encoded tokens(NOT YET IMPLIMENTED)and line no's
import struct, re, getopt, sys

# The list of BBC BASIC V tokens:
# Base tokens, starting at 0x7f
tokens = [
    'OTHERWISE', # 7f
    'AND', 'DIV', 'EOR', 'MOD', 'OR', 'ERROR', 'LINE', 'OFF',
    'STEP', 'SPC', 'TAB(', 'ELSE', 'THEN', '<line>' , 'OPENIN', 'PTR',

    'PAGE', 'TIME', 'LOMEM', 'HIMEM', 'ABS', 'ACS', 'ADVAL', 'ASC',
    'ASN', 'ATN', 'BGET', 'COS', 'COUNT', 'DEG', 'ERL', 'ERR',

    'EVAL', 'EXP', 'EXT', 'FALSE', 'FN', 'GET', 'INKEY', 'INSTR(',
    'INT', 'LEN', 'LN', 'LOG', 'NOT', 'OPENUP', 'OPENOUT', 'PI',

    'POINT(', 'POS', 'RAD', 'RND', 'SGN', 'SIN', 'SQR', 'TAN',
    'TO', 'TRUE', 'USR', 'VAL', 'VPOS', 'CHR$', 'GET$', 'INKEY$',

    'LEFT$(', 'MID$(', 'RIGHT$(', 'STR$', 'STRING$(', 'EOF',
        '<ESCFN>', '<ESCCOM>', '<ESCSTMT>',
    'WHEN', 'OF', 'ENDCASE', 'ELSE' # ELSE2
        , 'ENDIF', 'ENDWHILE', 'PTR',

    'PAGE', 'TIME', 'LOMEM', 'HIMEM', 'SOUND', 'BPUT', 'CALL', 'CHAIN',
    'CLEAR', 'CLOSE', 'CLG', 'CLS', 'DATA', 'DEF', 'DIM', 'DRAW',

    'END', 'ENDPROC', 'ENVELOPE', 'FOR', 'GOSUB', 'GOTO', 'GCOL', 'IF',
    'INPUT', 'LET', 'LOCAL', 'MODE', 'MOVE', 'NEXT', 'ON', 'VDU',

    'PLOT', 'PRINT', 'PROC', 'READ', 'REM', 'REPEAT', 'REPORT', 'RESTORE',
    'RETURN', 'RUN', 'STOP', 'COLOUR', 'TRACE', 'UNTIL', 'WIDTH', 'OSCLI']

# Referred to as "ESCFN" tokens in the source, starting at 0x8e.
cfnTokens = [
    'SUM', 'BEAT']
# Referred to as "ESCCOM" tokens in the source, starting at 0x8e.
comTokens = [
    'APPEND', 'AUTO', 'CRUNCH', 'DELET', 'EDIT', 'HELP', 'LIST', 'LOAD',
    'LVAR', 'NEW', 'OLD', 'RENUMBER', 'SAVE', 'TEXTLOAD', 'TEXTSAVE', 'TWIN'
    'TWINO', 'INSTALL']
# Referred to as "ESCSTMT", starting at 0x8e.
stmtTokens= [
    'CASE', 'CIRCLE', 'FILL', 'ORIGIN', 'PSET', 'RECT', 'SWAP', 'WHILE',
    'WAIT', 'MOUSE', 'QUIT', 'SYS', 'INSTALL', 'LIBRARY', 'TINT', 'ELLIPSE',
    'BEATS', 'TEMPO', 'VOICES', 'VOICE', 'STEREO', 'OVERLAY']

def Detokenise(line):
    """Replace all tokens in the line 'line' with their ASCII equivalent."""
    # Internal function used as a callback to the regular expression
    # to replace tokens with their ASCII equivalents.
    def ReplaceFunc(match):
        ext, token = match.groups()
        tokenOrd = ord(token[0])
        if ext: # An extended opcode, CASE/WHILE/SYS etc
            if ext == '\xc6':
                return cfnTokens[tokenOrd-0x8e]
            if ext == '\xc7':
                return comTokens[tokenOrd-0x8e]
            if ext == '\xc8':
                return stmtTokens[tokenOrd-0x8e]
            raise Exception, "Bad token"
        else: # Normal token, plus any extra characters
            if token[0] == '\x8d': # line number following token
                #decode the 24 bit line number
                return str(DecodeLineNo(token[1:]))
            else:
                return tokens[tokenOrd-127] + token[1:]

    # This regular expression is essentially:
    # (Optional extension token) followed by
    # (REM token followed by the rest of the line)
    #     -- this ensures we don't detokenise the REM statement itself
    # OR
    # (Line number following token, with 3 characters in the range 64-127)
    # OR
    # (any token)
    return re.sub(r'([\xc6-\xc8])?(\xf4.*|\x8d[\x40-\x7f]{3}|[\x7f-\xff])', ReplaceFunc, line)

def DecodeLineNo(lineNo):
    """Returns a line number from a 24bit encoded line number"""
    # TODO could be edited to also convert 16 bit line numbers depending on input string length
    byte0=ord(lineNo[0])
    byte1=ord(lineNo[1])
    byte2=ord(lineNo[2])
    #needed to be ANDed with 255 after multipy because with this formula
    #on the 6502 it lost the high bits with the Logical Shift 
    msb = byte2 ^ (( byte0 * 16) & 255)          
    lsb = byte1 ^ (((byte0 & 0x30 ) * 4) & 255)  
    return (lsb + (msb * 256))

def ReadLines(data):
    """Returns a list of [line number, tokenised line] from a binary
       BBC BASIC V format file."""
    fileType=0
    if len(data) < 4:
        # TODO unsure how you want to return error
        raise Exception, "Bad Program"
    
    fileExt = data[-4:]
    if fileExt[3] == '\x0d':
        fileType=7 
        decode = 0
        lineEnd='\x0d'
        print 'file uses CR'
    if fileExt[3] == '\x0a':
        fileType=6
        decode = 0
        lineEnd='\x0a'
        print 'file uses LF'
    if fileExt[2:4] == '\x0a\x0d':
        fileType=5 
        decode = 0
        lineEnd='\x0a\x0d'
        print 'file uses LFCR'
    if fileExt[2:4] == '\x0d\x0a':
        fileType=4 
        deocde = 0
        lineEnd='\x0d\x0a'
        print 'file uses CRLF'
    if fileExt[2:4] == '\x0d\xff':
        fileType=2 
        decode = 1
        lineEnd='\x0d'
        print 'BBC BASIC (Acorn)'
    if fileExt == '\x0d\x00\xff\xff':
        fileType=1
        deocde = 2 
        lineEnd='\x0d'
        print 'BBC BASIC (80/86)'
        
    lenLineEnd = len(lineEnd)
    lines = []
    while True:
        if (decode == 1) & (len(data) < 2):
            raise Exception, "Bad program"
        if (decode == 1) & (data[0] != '\r'):
            raise Exception, "Bad program"
        if (decode == 1) & (data[1] == '\xff'):
            break
        if (decode == 2):
            raise Exception, "BB4W tokens need testing"
        if (decode == 1):
            lineNumber, length = struct.unpack('>hB', data[1:4])
            lineData = data[4:length]
        if (decode == 0):
            lineNumber = ''
            findStart=lenLineEnd
            #make sure dont miss first chars of plane text
            if data[0:lenLineEnd] != lineEnd:
                findStart=0
            length = data.find(lineEnd,findStart)
            lineData = data[findStart:length]
        lines.append([lineNumber, lineData])
        data = data[length:]
        if len(data) <= len(lineEnd):
            # may need to check what data is in last chars
            # all tests have been ending tokens/CR/LF
            break
    return lines

def Decode(data, output):
    """Decode binary data 'data' and write the result to 'output'."""
    lineNoNeeded = False
    if None != re.search('\x8d', data): #check if line number references are used anywhere in the file
        lineNoNeeded = True
    lines = ReadLines(data)
    for lineNumber, line in lines:
        lineData = Detokenise(line)
        if lineNoNeeded:
            output.write(str(lineNumber))
        output.write(lineData + '\n') 

if __name__ == "__main__":
    optlist, args = getopt.getopt(sys.argv[1:], '')
    if len(args) != 2:
        print "Usage: %s INPUT OUTPUT" % sys.argv[0]
        #sys.exit(1)
    #entireFile = open(args[0], 'rb').read()
    #output = open(args[1], 'w')
    entireFile = open('calc.bbc', 'rb').read()
    output = open('calc1.txt', 'w')
    Decode(entireFile, output)
    output.close()
