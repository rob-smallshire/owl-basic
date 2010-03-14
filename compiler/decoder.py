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

class Decoder(object):
    
    def __init__(self, data):
        self.data = data
        self.lines = []
        
    #data = property(lambda self: self.__data)
        
class PlainTextDecoder(Decoder):
    
    def __init__(self, data):
        super(PlainTextDecoder, self).__init__(data)
        
    def decode(self):
        split_lines = self.data.split(self.lineEnd)
        
        # Remove any trailing empty line
        if len(split_lines[-1]) == 0:
            split_lines = split_lines[:-1]
            
        has_line_numbers = None # Tri-state None, True or False
        logical_line_number = 10
        
        for line in split_lines:
            m = re.match(r'\s*(\d+)?\s?(.*)', line) # TODO: Factor this regex out of here and decoder
            line_number, line_body = m.group(1), m.group(2)
            current_line_has_number = line_number is not None
            
            if has_line_numbers is None:
                has_line_numbers = current_line_has_number
            else:
                if current_line_has_number != has_line_numbers:
                    raise Exception, "Inconsistent line numbering" 
            
            # Fake line numbers if they are missing
            if has_line_numbers == False:
                line_number = logical_line_number
                
            logical_line_number += 10
                            
            self.lines.append((line_number, line_body))
            
        return self.lines

class PlainTextCrDecoder(PlainTextDecoder):
    lineEnd = '\x0d'
    fileTypeName = 'plain text CR'

    def __init__(self, data):
        super(PlainTextCrDecoder, self).__init__(data)

class PlainTextLfDecoder(PlainTextDecoder):
    lineEnd = '\x0a'
    fileTypeName = 'plain text LF'
    
    def __init__(self, data):
        super(PlainTextLfDecoder, self).__init__(data)

class PlainTextLfCrDecoder(PlainTextDecoder):
    lineEnd = '\x0a\x0d'
    fileTypeName = 'plain text LFCR'
    
    def __init__(self, data):
        super(PlainTextLfCrDecoder, self).__init__(data)
    
class PlainTextCrLfDecoder(PlainTextDecoder):
    lineEnd = '\x0d\x0a'
    fileTypeName = 'plain text CRLF'
    
    def __init__(self, data):
        super(PlainTextCrLfDecoder, self).__init__(data)

class BbcBasicAcornDecoder(Decoder):
    lineEnd = '\x0d'
    fileTypeName = 'BBC BASIC (Acorn)'
    
    def __init__(self, data):
        super(BbcBasicAcornDecoder, self).__init__(data)
    
    def decode(self):
        lenLineEnd = len(self.lineEnd)
        while True:
            if len(self.data) < 2:
                raise Exception, "Bad program"
            if self.data[1] == '\xff':
                break
            #  {<cr> <linehi> <linelo> <len> <text>} <cr> <ff>
            lineNumber=(ord(self.data[2]) + (ord(self.data[1]) * 256))
            length=ord(self.data[3])
            lineData = self.data[4:length]
            self.lines.append([lineNumber, self.detokenise(lineData)])
            self.data = self.data[length:]
            if len(self.data) <= len(self.lineEnd):
                # may need to check what data is in last chars
                # all tests have been ending tokens/CR/LF
                break
        return self.lines
    
    def detokenise(self, lineData):
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
        return re.sub(r'"(?:(?:[^"]+|"")*)"(?!")|( ?)([\xc6-\xc8])?(\xf4.*|\x8d[\x40-\x7f]{3}|[\x7f-\xff])',
                      BbcBasicAcornDecoder.replaceFunc, lineData)
    
    @staticmethod
    def replaceFunc(match):
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

class BbcBasic8086(Decoder):
    lineEnd = '\x0d'
    fileTypeName = 'BBC BASIC (80/86)'
    
    def __init__(self, data):
        super(BbcBasic8086, self).__init__(data)
        
    def decode(self):
        # TODO this needs testing 
        # i have read somewhere that bb4w uses different tokens
        # and also has diff line number formatting
        # (http://bb4w.wikispaces.com/Format)
        # {<len> <linelo> <linehi> <text> <cr>} <00> <ff> <ff>
        lenLineEnd = len(self.lineEnd)
        
        while True:
            # TODO check if order of bytes is correct
            lineNumber=(ord(self.data[1]) + (ord(self.data[2]) * 256)) # line number bytes in different order
            length=ord(self.data[0])
            if lineNumber == -1:
                break
            lineData = self.data[3:length]
            self.lines.append([lineNumber, self.detokenise(lineData)])
            self.data = self.data[length:]
            if len(self.data) <= len(self.lineEnd):
                # may need to check what data is in last chars
                # all tests have been ending tokens/CR/LF
                break
        return self.lines
    
    def detokenise(self, lineData):
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
        return re.sub(r'"(?:(?:[^"]+|"")*)"(?!")|( ?)(\xf4.*|\x8d[\x40-\x7f]{3}|[\x7f-\xff]|[\x00-\x0f])',
                      BbcBasic8086Decoder.replaceFunc, line)
    
    @staticmethod
    def replaceFunc(match):
        if match.group().startswith('"'):
            return match.group()
        else:
            prefix, token = match.groups()
            if len(prefix) == 0:
                prefix = ' '
            tokenOrd = ord(token[0])
            if token[0] == '\x8d': # line number following token
                #decode the 24 bit line number
                return str(DecodeLineNo(token[1:]))
            else:
                return prefix + bb4wTokens[tokenOrd ^ 128] + token[1:]

def fileType(data):
    '''
    Factory to produce the correct decoder depending on the file contents.
    '''
    if len(data) < 4:
        # TODO unsure how you want to return error
        raise Exception, "Bad Program"
    
    fileExt = data[-4:]
    
    # Check final byte sequence (longest sequence first)
    if fileExt == '\x0d\x00\xff\xff':
        return BbcBasic8086Decoder(data)
    elif fileExt[2:4] == '\x0a\x0d':
        return PlainTextLfCrDecoder(data)  
    elif fileExt[2:4] == '\x0d\x0a':
        return PlainTextCrLfDecoder(data)
    elif fileExt[2:4] == '\x0d\xff':
        return BbcBasicAcornDecoder(data)
    elif fileExt[3] == '\x0d':
        return PlainTextCrDecoder(data);
    elif fileExt[3] == '\x0a':
        return PlainTextLfDecoder(data)
    else:
        raise Exception, "Unrecognised program format"
    
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
    decoder = fileType(data)
    lines = decoder.decode()
    return lines
    
def decode(data, output):
    """Decode binary data 'data' and write the result to 'output'."""
    lines = ReadLines(data)
    for lineNumber, lineData in lines:
        output.write(str(lineNumber) + ' ')
        # Normalise line endings to \n
        output.write(lineData.strip() + '\n')

if __name__ == "__main__":
    optlist, args = getopt.getopt(sys.argv[1:], '')
    if len(args) != 2:
        print "Usage: %s INPUT OUTPUT" % sys.argv[0]
        sys.exit(1)
    entireFile = open(args[0], 'rb').read()
    output = open(args[1], 'w')
    decode(entireFile, output)
    output.close()
