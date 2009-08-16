# BBC BASIC Lexer

import re

from errors import error
        
tokens = (
    'EOL',
    'ARRAYID_LPAREN',
    'PROC_ID',
    'FN_ID',
    'ID',
    'LITERAL_STRING',
    'LITERAL_FLOAT',
    'LITERAL_INTEGER',
    'QUERY',
    'PLING',
    'PIPE',
    'HASH',
    'DOLLAR',
    'APOSTROPHE',
    'COLON',
    'COMMA',
    'SEMICOLON',
    'PLUS',
    'MINUS',
    'TIMES',
    'DIVIDE',
    'EQ',
    'NE',
    'LTE',
    'GTE',
    'LT',
    'GT',
    'PLUS_ASSIGN',
    'MINUS_ASSIGN',
    'TIMES_ASSIGN',
    'DIVIDE_ASSIGN',
    'AND_ASSIGN',
    'DIV_ASSIGN',
    'EOR_ASSIGN',
    'MOD_ASSIGN',
    'OR_ASSIGN',
    'SHIFT_LEFT',
    'SHIFT_RIGHT',
    'SHIFT_RIGHT_UNSIGNED',
    'AMPERSAND',
    'LPAREN',
    'RPAREN',
    'LBRAC',
    'RBRAC',
    'CARET',
    'TILDE',
    'DOT',
    'AND',
    'DIV',
    'EOR',
    'MOD',
    'OR',
    'ERROR',
    'LINE',
    'OFF',
    'STEP',
    'STEREO',
    'SPC',
    'TAB_LPAREN',
    'ELSE',
    'THEN',
    'OPENIN',
    'ABS',
    'ACS',
    'ADVAL',
    'ASC',
    'ASN',
    'ATN',
    'BGET',
    'BEAT',
    'BEATS',
    'COS',
    'COUNT',
    'DEG',
    'ERL',
    'ERR',
    'EVAL',
    'EXP',
    'EXT',
    'FALSE',
    'GET',
    'INKEY',
    'INSTR_LPAREN',
    'INT',
    'LEN',
    'LN',
    'LOG',
    'OPENUP',
    'OPENOUT',
    'PI',
    'POINT',
    'POINT_LPAREN',
    'POS',
    'RAD',
    'RND',
    'RND_LPAREN',
    'SGN',
    'SIN',
    'SQR',
    'TAN',
    'TO',
    'TOP',
    'TRUE',
    'USR',
    'VAL',
    'VPOS',
    'CHR_STR',
    'GET_STR',
    'INKEY_STR',
    'LEFT_STR_LPAREN',
    'MID_STR_LPAREN',
    'RIGHT_STR_LPAREN',
    'STR_STR',
    'STRING_STR_LPAREN',
    'EOF',
    'SUM',
    'SUMLEN',
    'WHILE',
    'CASE',
    'WHEN',
    'OF',
    'ENDCASE',
    'OTHERWISE',
    'ENDIF',
    'ENDWHILE',
    'PTR',
    'PAGE',
    'TIME',
    'TIME_STR',
    'LOMEM',
    'HIMEM',
    'SOUND',
    'BPUT',
    'CALL',
    'CHAIN',
    'CLEAR',
    'CLOSE',
    'CLG',
    'CLS',
    'DATA',
    'DEF',
    'DIM',
    'DIM_LPAREN',
    'DRAW',
    'END',
    'ENDPROC',
    'ENVELOPE',
    'FOR',
    'GOSUB',
    'GOTO',
    'GCOL',
    'IF',
    'INPUT',
    'LET',
    'LIBRARY',
    'LOCAL',
    'MODE',
    'MOVE',
    'NEXT',
    'ON',
    'VDU',
    'VOICES',
    'PLOT',
    'PRINT',
    'READ',
    'REPEAT',
    'REPORT',
    'RESTORE',
    'RETURN',
    'RUN',
    'STOP',
    'TEMPO',
    'COLOUR',
    'TRACE',
    'UNTIL',
    'WIDTH',
    'OSCLI',
    'CIRCLE',
    'ELLIPSE',
    'FILL',
    'MOUSE',
    'ORIGIN',
    'QUIT',
    'RECTANGLE',
    'SWAP',
    'SYS',
    'TINT',
    'WAIT',
    'INSTALL',
    'PRIVATE',
    'BY',
    'EXIT',
    'NOT',
    'MANDEL'
)

def t_COMMENT(t):
    r'REM[^\n]*'
    pass

# Define a rule so we can split lines with a trailing backslash and leading backslash
def t_CONTINUATION(t):
    r'\\[ \t]*[\r\n][ \t]*\\'
    t.lexer.lineno += 1
    pass

# Define a rule so we can track line numbers
def t_EOL(t):
    r'[\r\n]+' 
    t.lexer.lineno += len(t.value) # possible error with line number on different platforms
    #print "t.lexer.lineno = %s" % t.lexer.lineno
    return t

# In BBC BASIC identifiers cannot begin with prefixes, so we go contrary
# to the advice in the PLY manual, since we want PRINTED to be lexed as
# PRINT ED

# BBC Basic keywords

# The order of these tokens is significant, since some keywords such as
# TO form the first part of TOP.  Also, most keywords are disallowed at the
# start of variable names, however, some keywords are allowed at the start
# of an identifier name. These are listed after the t_ID token. Finally, some
# keywords incorporate the left parenthesis as part of the keyword, for statements
# where no space is permitted between the keyword and the parenthesis.

# Nine letter keywords

def t_OTHERWISE(t):
    r'OTHERWISE'
    return t

def t_RECTANGLE(t):
    r'RECTANGLE'
    return t

# Eight letter keywords

def t_ENVELOPE(t):
    r'ENVELOPE'
    return t

def t_ENDWHILE(t):
    r'ENDWHILE'
    return t

# Seven letter keywords

def t_ELLIPSE(t):
    r'ELLIPSE'
    return t

def t_INSTALL(t):
    r'INSTALL'
    return t

def t_OPENOUT(t):
    r'OPENOUT'
    return t

def t_PRIVATE(t):
    r'PRIVATE'
    return t

def t_RESTORE(t):
    r'RESTORE'
    return t

def t_RIGHT_STR_LPAREN(t):
    r'RIGHT\$\('
    return t

def t_STRING_STR_LPAREN(t):
    r'STRING\$\('
    return t

# Six letter keywords

def t_CIRCLE(t):
    r'CIRCLE'
    return t

def t_COLOUR(t):
    r'COLOU?R'    #major error here. cannot return a string.
    t.type = 'COLOUR' 
    return t # have removed the return of 'COLOUR' due to tokenising failure

def t_INKEY_STR(t):
    r'INKEY\$'
    return t

def t_INSTR_LPAREN(t):
    r'INSTR\('
    return t

def t_LEFT_STR_LPAREN(t):
    r'LEFT\$\('
    return t

# Existence in ARM BASIC documented at
# http://www.g7jjf.com/acornArm.htm 
def t_MANDEL(t):
    r'MANDEL'
    return t

def t_OPENIN(t):
    r'OPENIN'
    return t

def t_OPENUP(t):
    r'OPENUP'
    return t

def t_ORIGIN(t):
    r'ORIGIN'
    return t

def t_POINT_LPAREN(t):
    r'POINT\('
    return t

def t_REPEAT(t):
    r'REPEAT'
    return t

def t_RETURN(t):
    r'RETURN'
    return t

def t_SUMLEN(t):
    r'SUMLEN'
    return t

def t_STEREO(t):
    r'STEREO'
    return t

def t_VOICES(t):
    r'VOICES'
    return t

# Five letter keywords

def t_ADVAL(t):
    r'ADVAL'
    return t

def t_BEATS(t):
    r'BEATS'
    return t

def t_CHAIN(t):
    r'CHAIN'
    return t

def t_ERROR(t):
    r'ERROR'
    return t

def t_GOSUB(t):
    r'GOSUB'
    return t

def t_HIMEM(t):
    r'HIMEM'
    return t

def t_INKEY(t):
    r'INKEY'
    return t

def t_INPUT(t):
    r'INPUT'
    return t

def t_LOCAL(t):
    r'LOCAL'
    return t

def t_LOMEM(t):
    r'LOMEM'
    return t

def t_MID_STR_LPAREN(t):
    r'MID\$\('
    return t

def t_MOUSE(t):
    r'MOUSE'
    return t

def t_OSCLI(t):
    r'OSCLI'
    return t

def t_POINT(t):
    r'POINT'
    return t

def t_PRINT(t):
    r'PRINT'
    return t

def t_SOUND(t):
    r'SOUND'
    return t

def t_TRACE(t):
    r'TRACE'
    return t

def t_TEMPO(t):
    r'TEMPO'
    return t

def t_TIME_STR(t):
    r'TIME\$'
    return t

def t_UNTIL(t):
    r'UNTIL'
    return t

def t_WHILE(t):
    r'WHILE'
    return t

def t_WIDTH(t):
    r'WIDTH'
    return t

# Four letter keywords

def t_BEAT(t):
    r'BEAT'
    return t

def t_CASE(t):
    r'CASE'
    return t

def t_CHR_STR(t):
    r'CHR\$'
    return t

def t_DATA(t):
    r'DATA[^\n]*'
    # Note: Data captures everything until the
    #       end of the line. The data items are
    #       not tokenized at this point.
    m = re.match(r'DATA([^\n]+)', t.value)
    if m is None:
        fatalError("No DATA in %s" % t.value)
    t.value = m.group(1)
    return t

def t_DIM_LPAREN(t):
    r'DIM\('
    return t

def t_DRAW(t):
    r'DRAW'
    return t

def t_ELSE(t):
    r'ELSE'
    return t

def t_EVAL(t):
    r'EVAL'
    return t

def t_FILL(t):
    r'FILL'
    return t

def t_GCOL(t):
    r'GCOL'
    return t

def t_GET_STR(t):
    r'GET\$'
    return t

def t_GOTO(t):
    r'GOTO'
    return t

def t_LINE(t):
    r'LINE'
    return t

def t_LIBRARY(t):
    r'LIBRARY'
    return t

def t_MODE(t):
    r'MODE'
    return t

def t_MOVE(t):
    r'MOVE'
    return t

def t_NEXT(t):
    r'NEXT'
    return t

def t_PLOT(t):
    r'PLOT'
    return t

def t_PAGE(t):
    r'PAGE'
    return t

def t_QUIT(t):
    r'QUIT'
    return t

def t_READ(t):
    r'READ'
    return t

def t_RND_LPAREN(t):
    r'RND\('
    return t

def t_STEP(t):
    r'STEP'
    return t

def t_STR_STR(t):
    r'STR\$'
    return t

def t_SWAP(t):
    r'SWAP'
    return t

def t_TAB_LPAREN(t):
    r'TAB\('
    return t

def t_THEN(t):
    r'THEN'
    return t

def t_TIME(t):
    r'TIME'
    return t

def t_TINT(t):
    r'TINT'
    return t

def t_VPOS(t):
    r'VPOS'
    return t

def t_WAIT(t):
    r'WAIT'
    return t

def t_WHEN(t):
    r'WHEN'
    return t

# Three letter keywords

def t_ABS(t):
    r'ABS'
    return t

def t_ACS(t):
    r'ACS'
    return t

def t_AND(t):
    r'AND'
    return t

def t_ASC(t):
    r'ASC'
    return t

def t_ASN(t):
    r'ASN'
    return t

def t_ATN(t):
    r'ATN'
    return t

def t_CALL(t):
    r'CALL'
    return t

def t_COS(t):
    r'COS'
    return t

def t_DEF(t):
    r'DEF'
    return t

def t_DEG(t):
    r'DEG'
    return t

def t_DIM(t):
    r'DIM'
    return t

def t_DIV(t):
    r'DIV'
    return t

def t_EOR(t):
    r'EOR'
    return t

def t_ERL(t):
    r'ERL'
    return t

def t_ERR(t):
    r'ERR'
    return t

def t_EXP(t):
    r'EXP'
    return t

def t_FOR(t):
    r'FOR'
    return t

def t_GET(t):
    r'GET'
    return t

def t_INT(t):
    r'INT'
    return t

def t_LEN(t):
    r'LEN'
    return t

def t_LET(t):
    r'LET'
    return t

def t_LOG(t):
    r'LOG'
    return t

def t_MOD(t):
    r'MOD'
    return t

def t_NOT(t):
    r'NOT'
    return t

def t_OFF(t):
    r'OFF'
    return t

def t_PTR(t):
    r'PTR'
    return t

def t_RAD(t):
    r'RAD'
    return t

def t_RND(t):
    r'RND'
    return t

def t_SGN(t):
    r'SGN'
    return t

def t_SIN(t):
    r'SIN'
    return t

def t_SPC(t):
    r'SPC'
    return t

def t_SQR(t):
    r'SQR'
    return t

def t_SUM(t):
    r'SUM'
    return t

def t_SYS(t):
    r'SYS'
    return t

def t_TAN(t):
    r'TAN'
    return t

def t_TOP(t):
    r'TOP'
    return t

def t_USR(t):
    r'USR'
    return t

def t_VAL(t):
    r'VAL'
    return t

def t_VDU(t):
    r'VDU'
    return t

# Two letter keywords

def t_IF(t):
    r'IF'
    return t

def t_LN(t):
    r'LN'
    return t

def t_ON(t):
    r'ON'
    return t

def t_OR(t):
    r'OR'
    return t

def t_TO(t):
    r'TO'
    return t


# Keywords before this point are disallowed at the start
# of variable names

# Now we list reserved identifiers. These cannot be used as
# identifiers, but that can feature at the start of identifiers

reserved = {
    'ENDWHILE' : 'ENDWHILE',
    'ENDCASE' : 'ENDCASE',
    'ENDPROC' : 'ENDPROC',
    'REPORT' : 'REPORT',
    'RETURN' : 'RETURN',
    'CLEAR' : 'CLEAR',
    'CLOSE' : 'CLOSE',
    'COUNT' : 'COUNT',
    'ENDIF' : 'ENDIF',
    'FALSE' : 'FALSE',
    'HIMEM' : 'HIMEM',
    'LOMEM' : 'LOMEM',
    'BGET' : 'BGET',
    'BPUT' : 'BPUT',
    'EXIT' : 'EXIT',
    'PAGE' : 'PAGE',
    'QUIT' : 'QUIT',
    'STOP' : 'STOP',
    'TIME' : 'TIME',
    'TRUE' : 'TRUE',
    'VPOS' : 'VPOS',
    'WAIT' : 'WAIT',
    'CLG' : 'CLG',
    'CLS' : 'CLS',
    'END' : 'END',
    'EOF' : 'EOF',
    'ERL' : 'ERL',
    'ERR' : 'ERR',
    'EXT' : 'EXT',
    'OFF' : 'OFF',
    'POS' : 'POS',
    'PTR' : 'PTR',
    'RND' : 'RND',
    'RUN' : 'RUN',
    'BY' : 'BY',
    'OF' : 'OF',
    'PI' : 'PI'
            }

# Identifiers

def t_PROC_ID(t):
    r'PROC[a-zA-Z_0-9`@]+'
    t.value = t.value
    return t

def t_FN_ID(t):
    r'FN[a-zA-Z_0-9`@]+'
    t.value = t.value
    return t

def t_ARRAYID_LPAREN(t):
    r'[a-zA-Z_`][a-zA-Z_0-9`]*[$%&~]?\('
    t.type = reserved.get(t.value, 'ARRAYID_LPAREN')
    return t

# TODO: Cannot use @ symbol at the beginning of
#       any variable name. @% is a special variable
def t_ID(t):
    r'([@a-zA-Z_`][a-zA-Z_0-9`]*[$%&~]?)'
    # TODO: Hash doesn't seem to work in here.
    # Ampersand (byte) and hash (64-bit numeric ?int) suffixes only apply to BBC BASIC for Windows
    # Tilde suffix only applies to OWL BASIC - object reference
    t.type = reserved.get(t.value, 'ID') # Check for reserved identifiers
    return t

# Operators
t_QUERY = r'\?'
t_PLING = r'\!'
t_PIPE = r'\|'
t_HASH = r'\#'
t_DOLLAR = r'\$'
t_APOSTROPHE = r"'"
t_COLON = r':'
t_COMMA = r','
t_SEMICOLON = r';'
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_EQ = r'='
t_NE = r'<>'
t_LTE = r'<='
t_GTE = r'>='
t_LT = r'<'
t_GT = r'>'
t_PLUS_ASSIGN = r'\+='
t_MINUS_ASSIGN = r'-='
t_TIMES_ASSIGN = r'\*='
t_DIVIDE_ASSIGN = r'/='
t_AND_ASSIGN = r'AND='
t_DIV_ASSIGN = r'DIV='
t_EOR_ASSIGN = r'EOR='
t_MOD_ASSIGN = r'MOD='
t_OR_ASSIGN = r'OR='
t_SHIFT_LEFT = r'<<'
t_SHIFT_RIGHT = r'>>'
t_SHIFT_RIGHT_UNSIGNED = r'>>>'
t_AMPERSAND = r'&'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRAC = r'\['
t_RBRAC = r'\]'
t_CARET = r'\^'
t_TILDE = r'~'
t_DOT = r'\.'



t_ignore  = ' \t'

def t_LITERAL_STRING(t):
    r'"((?:[^"]+|"")*)"(?!")'
    t.value = t.value[1:-1].replace('""', '"')
    return t

def t_LITERAL_FLOAT(t):
    r'\d*\.\d+(E([+-]?\d+))?'
    try:
        t.value = float(t.value)
    except ValueError:
        print "Number %s is too large!" % t.value
    return t

def t_LITERAL_INTEGER(t):
    r'\d+'
    try:
        t.value = int(t.value)
    except ValueError:
        print "Number %s is too large!" % t.value
        t.value = 0
    return t

def t_LITERAL_HEX_INTEGER(t):
    r'&[\dA-F]+'
    try:
        t.value = int(t.value[1:], 16)
        t.type = 'LITERAL_INTEGER'
    except ValueError:
        print "Number %s is too large!" % t.value
        t.value = 0
    return t

def t_LITERAL_BINARY_INTEGER(t):
    r'%[01]+'
    try:
        t.value = int(t.value[1:], 2)
        t.type = 'LITERAL_INTEGER'
    except ValueError:
        print "Number %s is too large!" % t.value
        t.value = 0
    return t

# Error handling rule
def t_error(t):
    print "Illegal character '%s'" % t.value[0]
    t.lexer.skip(1)



