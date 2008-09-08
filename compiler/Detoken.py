#!/usr/bin/env python
#
# (c) 2007 Matt Godbolt.
#
# Updated 2008 Ian Smallshire.
#
# Get v0.01 @ http://xania.org/200711/bbc-basic-v-format
#
# Use however you like, as long as you put credit where credit's due.
# Some information obtained from source code from RISC OS Open.
# v0.01 - first release.  Doesn't deal with GOTO line numbers.       (c) 2007 Matt Godbolt
# v0.02 - edited to output line numbers where needed and fixed       Ian Smallshire
#         the GOTO/RESTORE/GOSUB line numbers.
# v0.03 - Added file type detection for input and provision          Ian Smallshire
#         for BB4W encoded tokens
# v0.04 - Now decodes BB4W tokens as well as Acorn.                  Ian Smallshire
# v0.05 - Corrected tokens inside strings. No longer detokenized     Rob & Ian Smallshire
# v0.06 - Fixed line number decoding with line numbers over 32767    Ian Smallshire

#line numbers for bb4w still need testing properly.
#if input file is plane text it must be terminated by an EOL
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
    'WHEN', 'OF', 'ENDCASE', 'ELSE', 'ENDIF', 'ENDWHILE', 'PTR',
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
    'APPEND', 'AUTO', 'CRUNCH', 'DELETE', 'EDIT', 'HELP', 'LIST', 'LOAD',
    'LVAR', 'NEW', 'OLD', 'RENUMBER', 'SAVE', 'TEXTLOAD', 'TEXTSAVE', 'TWIN'
    'TWINO', 'INSTALL']
# Referred to as "ESCSTMT", starting at 0x8e.
stmtTokens= [
    'CASE', 'CIRCLE', 'FILL', 'ORIGIN', 'PSET', 'RECT', 'SWAP', 'WHILE',
    'WAIT', 'MOUSE', 'QUIT', 'SYS', 'INSTALL', 'LIBRARY', 'TINT', 'ELLIPSE',
    'BEATS', 'TEMPO', 'VOICES', 'VOICE', 'STEREO', 'OVERLAY']
# BB4W tokens....
# these tokens start at 128 and wrap around to 0-15
bb4wTokens=["AND","DIV","EOR","MOD","OR","ERROR","LINE","OFF",
        "STEP","SPC","TAB(","ELSE","THEN","","OPENIN","PTR",
        "PAGE","TIME","LOMEM","HIMEM","ABS","ACS","ADVAL","ASC",
        "ASN","ATN","BGET","COS","COUNT","DEG","ERL","ERR",
        "EVAL","EXP","EXT","FALSE","FN","GET","INKEY","INSTR(",
        "INT","LEN","LN","LOG","NOT","OPENUP","OPENOUT","PI",
        "POINT(","POS","RAD","RND","SGN","SIN","SQR","TAN",
        "TO","TRUE","USR","VAL","VPOS","CHR$","GET$","INKEY$",
        "LEFT$(","MID$(","RIGHT$(","STR$","STRING$(","EOF","SUM","WHILE",
        "CASE","WHEN","OF","ENDCASE","OTHERWISE","ENDIF","ENDWHILE","PTR",
        "PAGE","TIME","LOMEM","HIMEM","SOUND","BPUT","CALL","CHAIN",
        "CLEAR","CLOSE","CLG","CLS","DATA","DEF","DIM","DRAW",
        "END","ENDPROC","ENVELOPE","FOR","GOSUB","GOTO","GCOL","IF",
        "INPUT","LET","LOCAL","MODE","MOVE","NEXT","ON","VDU",
        "PLOT","PRINT","PROC","READ","REM","REPEAT","REPORT","RESTORE",
        "RETURN","RUN","STOP","COLOUR","TRACE","UNTIL","WIDTH","OSCLI",
        "","CIRCLE","ELLIPSE","FILL","MOUSE","ORIGIN","QUIT","RECTANGLE",
        "SWAP","SYS","TINT","WAIT","INSTALL","","PRIVATE","BY","EXIT"]

def Detokenise(line, decode):

    """Replace all tokens in the line 'line' with their ASCII equivalent."""
    # Internal function used as a callback to the regular expression
    # to replace tokens with their ASCII equivalents.
    def ReplaceFunc(match):
        if match.group().startswith('"'):
            return match.group()
        else:
            prefix, ext, token = match.groups()
            if len(prefix) == 0:
                prefix = ' '
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
                    return prefix + tokens[tokenOrd - 127] + token[1:]
    def ReplaceFuncBB4W(match):
        if match.group().startswith('"'):
            return match.group()
        else:
            print match.groups()
            prefix, token = match.groups()
            if len(prefix) == 0:
                prefix = ' '
            tokenOrd = ord(token[0])
            if token[0] == '\x8d': # line number following token
                #decode the 24 bit line number
                return str(DecodeLineNo(token[1:]))
            else:
                return prefix + bb4wTokens[tokenOrd ^ 128] + token[1:]

    if decode ==2:
        # This uses BB4W encoding
        # This regular expression is essentially:
        # Match a quoted string OR
        #
        # (REM token followed by the rest of the line)
        #     -- this ensures we don't detokenise the REM statement itself
        # OR
        # (Line number following token, with 3 characters in the range 64-127)
        # OR
        # (any token 127-255)
        # OR
        # (any token 0-15) TODO check if 16 is needed (EXIT) i think
        return re.sub(r'"(?:(?:[^"]+|"")*)"(?!")|( ?)(\xf4.*|\x8d[\x40-\x7f]{3}|[\x7f-\xff]|[\x00-\x0f])', ReplaceFuncBB4W, line)
    else:   
        # Acorn encoding
        # This regular expression is essentially:
        # Match a quoted string OR
        #
        # (Optional extension token) followed by
        # (REM token followed by the rest of the line)
        #     -- this ensures we don't detokenise the REM statement itself
        # OR
        # (Line number following token, with 3 characters in the range 64-127)
        # OR
        # (any token)
        return re.sub(r'"(?:(?:[^"]+|"")*)"(?!")|( ?)([\xc6-\xc8])?(\xf4.*|\x8d[\x40-\x7f]{3}|[\x7f-\xff])', ReplaceFunc, line)

def DecodeLineNo(lineNo):
    """Returns a line number from a 24bit encoded line number"""
    byte0=ord(lineNo[0])
    byte1=ord(lineNo[1])
    byte2=ord(lineNo[2])
    #needed to be ANDed with 255 after multiply because with this formula
    #on the 6502 it moved the high bits to carry with the Logical Shift 
    msb = byte2 ^ (( byte0 * 16) & 255)          
    lsb = byte1 ^ (((byte0 & 0x30 ) * 4) & 255)  
    return (lsb + (msb * 256))

def ReadLines(data):
    """Returns a list of [line number, tokenised line] from a binary
       BBC BASIC format file."""
    fileType=0
    if len(data) < 4:
        # TODO unsure how you want to return error
        raise Exception, "Bad Program"
    
    fileExt = data[-4:]
    if fileExt[3] == '\x0d':
        fileType=7 
        decode = 0
        lineEnd='\x0d'
        fileTypeName = 'plain text CR'
    if fileExt[3] == '\x0a':
        fileType=6
        decode = 0
        lineEnd='\x0a'
        fileTypeName = 'plain text LF'
    if fileExt[2:4] == '\x0a\x0d':
        fileType=5 
        decode = 0
        lineEnd='\x0a\x0d'
        fileTypeName = 'plain text LFCR'
    if fileExt[2:4] == '\x0d\x0a':
        fileType=4 
        deocde = 0
        lineEnd='\x0d\x0a'
        fileTypeName = 'plain text CRLF'
    if fileExt[2:4] == '\x0d\xff':
        fileType=2 
        decode = 1
        lineEnd='\x0d'
        fileTypeName = 'BBC BASIC (Acorn)'
    if fileExt == '\x0d\x00\xff\xff':
        fileType=1
        decode = 2 
        lineEnd='\x0d'
        fileTypeName = 'BBC BASIC (80/86)'
    
    print fileTypeName
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
            # TODO this needs testing 
            # i have read somewhere that bb4w uses different tokens
            # and also has diff line number formatting
            # (http://bb4w.wikispaces.com/Format)
            # {<len> <linelo> <linehi> <text> <cr>} <00> <ff> <ff>

            # TODO check if order of bytes is correct
            lineNumber=(ord(data[1]) + (ord(data[2]) * 256)) # line number bytes in different order
            length=ord(data[0])
            if lineNumber == -1:
                break
            lineData = data[3:length]
        if (decode == 1):
            #  {<cr> <linehi> <linelo> <len> <text>} <cr> <ff>
            lineNumber=(ord(data[2]) + (ord(data[1]) * 256))
            length=ord(data[3])
            lineData = data[4:length]
        if (decode == 0):
            #  {[<text>] [<cr>|<lf>|<cr><lf>|<lf><cr>]}
            
            lineNumber = ''
            findStart=lenLineEnd
            #make sure dont miss first chars of plane text
            if data[0:lenLineEnd] != lineEnd:
                findStart=0
            length = data.find(lineEnd,findStart)
            lineData = data[findStart:length]
        lines.append([lineNumber, Detokenise(lineData, decode)])
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
    for lineNumber, lineData in lines:
        if lineNoNeeded:
            output.write(str(lineNumber) + ' ')
        output.write(lineData.strip() + '\n')
    return lineNoNeeded

if __name__ == "__main__":
    optlist, args = getopt.getopt(sys.argv[1:], '')
    if len(args) != 2:
        print "Usage: %s INPUT OUTPUT" % sys.argv[0]
        sys.exit(1)
    entireFile = open(args[0], 'rb').read()
    output = open(args[1], 'w')
    Decode(entireFile, output)
    output.close()
