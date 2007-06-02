import sys

import ply.lex as lex

tokens = (
    'EOL',
    'ID',
    'LITERAL_STRING',
    'LITERAL_INTEGER',
    'LITERAL_FLOAT',
    'QUERY',
    'PLING',
    'PIPE',
    'HASH',
    'DOLLAR',
    'PRIME',
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
    'BACKSLASH',
    'AND',
    'DIV',
    'EOR',
    'MOD',
    'OR',
    'ERROR',
    'LINE',
    'OFF',
    'STEP',
    'SPC',
    'TAB',
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
    'COS',
    'COUNT',
    'DEG',
    'ERL',
    'ERR',
    'EVAL',
    'EXP',
    'EXT',
    'FALSE',
    'FN',
    'GET',
    'INKEY',
    'INSTR',
    'INT',
    'LEN',
    'LN',
    'LOG',
    'OT',
    'OPENUP',
    'OPENOUT',
    'PI',
    'POINT',
    'POS',
    'RAD',
    'RND',
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
    'LEFT_STR',
    'MID_STR',
    'RIGHT_STR',
    'STR_STR',
    'STRING_STR',
    'EOF',
    'SUM',
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
    'LOCAL',
    'MODE',
    'MOVE',
    'NEXT',
    'ON',
    'VDU',
    'PLOT',
    'PRINT',
    'PROC',
    'READ',
    'REPEAT',
    'REPORT',
    'RESTORE',
    'RETURN',
    'RUN',
    'STOP',
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
    'EXIT'
)

# BBC Basic reserved words
reserved = {
    'AND' : 'AND',
    'DIV' : 'DIV',
    'EOR' : 'EOR',
    'MOD' : 'MOD',
    'OR'  : 'OR',
    'ERROR' : 'ERROR',
    'LINE' : 'LINE',
    'OFF' : 'OFF',
    'STEP' : 'STEP',
    'SPC' : 'SPC',
    'TAB' : 'TAB',
    'ELSE' : 'ELSE',
    'THEN' : 'THEN',
    'OPENIN' : 'OPENIN',
    'ABS' : 'ABS',
    'ACS' : 'ACS',
    'ADVAL' : 'ADVAL',
    'ASC' : 'ASC',
    'ASN' : 'ASN',
    'ATN' : 'ATN',
    'BGET' : 'BGET',
    'COS' : 'COS',
    'COUNT' : 'COUNT',
    'DEG' : 'DEG',
    'ERL' : 'ERL',
    'ERR' : 'ERR',
    'EVAL' : 'EVAL',
    'EXP' : 'EXP',
    'EXT' : 'EXT',
    'FALSE' : 'FALSE',
    'FN' : 'FN',
    'GET' : 'GET',
    'INKEY' : 'INKEY',
    'INSTR' : 'INSTR',
    'INT' : 'INT',
    'LEN' : 'LEN',
    'LN' : 'LN',
    'LOG' : 'LOG',
    'OT' : 'OT',
    'OPENUP' : 'OPENUP',
    'OPENOUT' : 'OPENOUT',
    'PI' : 'PI',
    'POINT' : 'POINT',
    'POS' : 'POS',
    'RAD' : 'RAD',
    'RND' : 'RND',
    'SGN' : 'SGN',
    'SIN' : 'SIN',
    'SQR' : 'SQR',
    'TAN' : 'TAN',
    'TO' : 'TO',
    'TOP' : 'TOP',
    'TRUE' : 'TRUE',
    'USR' : 'USR',
    'VAL' : 'VAL',
    'VPOS' : 'VPOS',
    'CHR$' : 'CHR_STR',
    'GET$' : 'GET_STR',
    'INKEY$' : 'INKEY_STR',
    'LEFT$' : 'LEFT_STR',
    'MID$' : 'MID_STR',
    'RIGHT$' : 'RIGHT_STR',
    'STR$' : 'STR_STR',
    'STRING$' : 'STRING_STR',
    'EOF' : 'EOF',
    'SUM' : 'SUM',
    'WHILE' : 'WHILE',
    'CASE' : 'CASE',
    'WHEN' : 'WHEN',
    'OF' : 'OF',
    'ENDCASE' : 'ENDCASE',
    'OTHERWISE' : 'OTHERWISE',
    'ENDIF' : 'ENDIF',
    'ENDWHILE' : 'ENDWHILE',
    'PTR' : 'PTR',
    'PAGE' : 'PAGE',
    'TIME' : 'TIME',
    'LOMEM' : 'LOMEM',
    'HIMEM' : 'HIMEM',
    'SOUND' : 'SOUND',
    'BPUT' : 'BPUT',
    'CALL' : 'CALL',
    'CHAIN' : 'CHAIN',
    'CLEAR' : 'CLEAR',
    'CLOSE' : 'CLOSE',
    'CLG' : 'CLG',
    'CLS' : 'CLS',
    'DATA' : 'DATA',
    'DEF' : 'DEF',
    'DIM' : 'DIM',
    'DRAW' : 'DRAW',
    'END' : 'END',
    'ENDPROC' : 'ENDPROC',
    'ENVELOPE' : 'ENVELOPE',
    'FOR' : 'FOR',
    'GOSUB' : 'GOSUB',
    'GOTO' : 'GOTO',
    'GCOL' : 'GCOL',
    'IF' : 'IF',
    'INPUT' : 'INPUT',
    'LET' : 'LET',
    'LOCAL' : 'LOCAL',
    'MODE' : 'MODE',
    'MOVE' : 'MOVE',
    'NEXT' : 'NEXT',
    'ON' : 'ON',
    'VDU' : 'VDU',
    'PLOT' : 'PLOT',
    'PRINT' : 'PRINT',
    'PROC' : 'PROC',
    'READ' : 'READ',
    'REPEAT' : 'REPEAT',
    'REPORT' : 'REPORT',
    'RESTORE' : 'RESTORE',
    'RETURN' : 'RETURN',
    'RUN' : 'RUN',
    'STOP' : 'STOP',
    'COLOUR' : 'COLOUR',
    'COLOR' : 'COLOUR',
    'TRACE' : 'TRACE',
    'UNTIL' : 'UNTIL',
    'WIDTH' : 'WIDTH',
    'OSCLI' : 'OSCLI',
    'CIRCLE' : 'CIRCLE',
    'ELLIPSE' : 'ELLIPSE',
    'FILL' : 'FILL',
    'MOUSE' : 'MOUSE',
    'ORIGIN' : 'ORIGIN',
    'QUIT' : 'QUIT',
    'RECTANGLE' : 'RECTANGLE',
    'SWAP' : 'SWAP',
    'SYS' : 'SYS',
    'TINT' : 'TINT',
    'WAIT' : 'WAIT',
    'INSTALL' : 'INSTALL',
    'PRIVATE' : 'PRIVATE',
    'BY' : 'BY',
    'EXIT' : 'EXIT'
}

t_QUERY = r'\?'
t_PLING = r'\!'
t_PIPE = r'\|'
t_HASH = r'\#'
t_DOLLAR = r'\$'
t_PRIME = r"'"
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
t_SHIFT_RIGHT_UNSIGNED = r'>>'
t_AMPERSAND = r'&'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRAC = r'\['
t_RBRAC = r'\]'
t_CARET = r'\^'
t_TILDE = r'~'
t_BACKSLASH = r'\\'
t_DOT = r'\.'

t_ignore  = ' \t'

def t_COMMENT(t):
    r'REM[^\n]*'
    pass


# Define a rule so we can track line numbers
def t_EOL(t):
    r'[\r\n]+'
    t.lexer.lineno += len(t.value)
    return t

def t_ID(t):
    r'[@a-zA-Z_][a-zA-Z_0-9]*[$%&#]?'
    t.type = reserved.get(t.value, 'ID')
    return t

def t_LITERAL_STRING(t):
    r'"((?:[^"]+|"")*)"(?!")'
    t.value = t.value[1:-1].replace('""', '"')
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
    r'&[\dA-Fa-f]+'
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

def t_LITERAL_FLOAT(t):
    r'([+-]?)(?=\d|\.\d)\d*(\.\d*)?(E([+-]?\d+))?'
    try:
        t.value = float(t.value)
    except ValueError:
        print "Number %s is too large!" % t.value
    return t

# Error handling rule
def t_error(t):
    print "Illegal character '%s'" % t.value[0]
    t.lexer.skip(1)

# Build the lexer
lex.lex()

f = open(sys.argv[1], 'r')
data = f.read()
f.close()

# Give the lexer some input
lex.input(data)

# Tokenize
while 1:
    tok = lex.token()
    if not tok: break      # No more input
    print tok
