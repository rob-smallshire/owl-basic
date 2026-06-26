# BBC BASIC Lexer

import re

from owl_basic.errors import error
        
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
    'REPORT_STR',
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
    'MANDEL',
    'COMMENT',
    'STAR_COMMAND',
    'ASSEMBLER'
)

def t_ASSEMBLER(t):
    # An inline assembler block: [ ... ]. Grab it whole as raw text -- its
    # contents are machine mnemonics, not BASIC -- so it is one token the front
    # end keeps opaque and a backend lowers or rejects (see
    # docs/inline-assembler.md). The closing ']' is the first one that is not
    # inside a quoted string: per the BBC ROM the terminator is only recognised
    # at the start of a statement, and a string (e.g. EQUS "Contains]") is read
    # as one operand, so a ']' between quotes is data, not the terminator. A
    # plain regex can't honour that, so scan manually.
    r'\['
    data = t.lexer.lexdata
    start = t.lexer.lexpos - 1          # the '[' just matched
    i = t.lexer.lexpos
    n = len(data)
    while i < n:
        char = data[i]
        if char == '"':                 # skip a quoted string whole
            i += 1
            while i < n and data[i] != '"':
                i += 1
            i += 1                       # step past the closing quote
            continue
        if char == ']':
            i += 1                       # include the terminator
            break
        i += 1
    t.value = data[start:i]
    t.lexer.lexpos = i
    t.lexer.lineno += t.value.count('\n')
    return t

def t_COMMENT(t):
    r'REM[^\n]*'
    # Note: REM captures everything until the
    #       end of the line. We need to capture
    #       REMs because its is possible to RESTORE
    #       to a REMed line and use the DATA within it
    m = re.match(r'REM([^\n]*)', t.value)
    t.value = m.group(1)
    return t

# A star command (*HELP, *FX19, *CAT, ...) passes the rest of its line to the OS.
# '*' is only ever a *binary* multiply, so a '*' with no value before it is a star
# command: at the start of a line/program, after ':' or end-of-line, or after a
# keyword that takes no operand (REPEAT/THEN/ELSE -- the REPEAT*FX19 byte-saver).
# It consumes to end of line. Anywhere a value precedes it, it is multiplication
# (or '*='), so rewind the lexer to just the operator. Tried before t_TIMES (a
# function token), so it sees every '*' and decides.
_STAR_COMMAND_PRECEDERS = frozenset(
    (None, 'EOL', 'COLON', 'REPEAT', 'THEN', 'ELSE'))

def t_STAR_COMMAND(t):
    r'\*[^\n]*'
    if getattr(t.lexer, 'last_token_type', None) in _STAR_COMMAND_PRECEDERS:
        return t
    if t.value.startswith('*='):
        t.type = 'TIMES_ASSIGN'
        t.value = '*='
        t.lexer.lexpos = t.lexpos + 2
    else:
        t.type = 'TIMES'
        t.value = '*'
        t.lexer.lexpos = t.lexpos + 1
    return t

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

def t_REPORT_STR(t):
    r'REPORT\$'
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

def t_LIBRARY(t):
    r'LIBRARY'
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
    # CONDITIONAL keyword: suppressed before a name char, so RETURNX stays a
    # variable (ROM keyword-table bit-0 flag). Same shape as the TIME fix.
    r'RETURN(?![A-Za-z0-9_])'
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
    # CONDITIONAL keyword: suppressed before a name char, so HIMEMX stays a
    # variable (ROM bit-0 flag). Same shape as the TOP fix.
    r'HIMEM(?![A-Za-z0-9_])'
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
    # CONDITIONAL keyword: suppressed before a name char, so LOMEMX stays a
    # variable (ROM bit-0 flag). Same shape as the TOP fix.
    r'LOMEM(?![A-Za-z0-9_])'
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
    # DATA captures the rest of the line as raw items (not tokenised here). An
    # empty DATA -- a bare `DATA` -- is valid; its content is the empty string.
    t.value = t.value[len('DATA'):]
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
    # CONDITIONAL keyword: suppressed before a name char, so PAGEX stays a
    # variable (ROM bit-0 flag). Same shape as the TOP fix.
    r'PAGE(?![A-Za-z0-9_])'
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
    # CONDITIONAL keyword: suppressed before a name char, so TIMEX stays a
    # variable (ROM bit-0 flag). Same shape as the TOP fix.
    r'TIME(?![A-Za-z0-9_])'
    return t

def t_TINT(t):
    r'TINT'
    return t

def t_VPOS(t):
    # CONDITIONAL keyword: suppressed before a name char, so VPOSX stays a
    # variable (ROM bit-0 flag). Same shape as the TOP fix.
    r'VPOS(?![A-Za-z0-9_])'
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
    # CONDITIONAL keyword: suppressed before a name char, so ERLX stays a
    # variable (ROM bit-0 flag). Same shape as the TOP fix.
    r'ERL(?![A-Za-z0-9_])'
    return t

def t_ERR(t):
    # CONDITIONAL keyword: suppressed before a name char, so ERRX stays a
    # variable (ROM bit-0 flag). Same shape as the TOP fix.
    r'ERR(?![A-Za-z0-9_])'
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
    # CONDITIONAL keyword: suppressed before a name char, so PTRX stays a
    # variable (ROM bit-0 flag). Same shape as the TOP fix.
    r'PTR(?![A-Za-z0-9_])'
    return t

def t_RAD(t):
    r'RAD'
    return t

def t_RND(t):
    # CONDITIONAL keyword: suppressed before a name char, so RNDX stays a
    # variable (ROM bit-0 flag). Same shape as the TOP fix.
    r'RND(?![A-Za-z0-9_])'
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

# Token types that complete a value/operand. A TOP whose TO would land right
# after one of these is the FOR byte-saver's separator glued onto the loop limit
# -- TO + P, not the pseudo-variable -- because two values cannot abut. The BBC II
# ROM has no TOP token: "TOP" always crunches to the TO token plus a literal 'P',
# and the top-of-program pseudo-variable is reconstructed at runtime (fn_to) only
# when that TO lands in *operand* position. We approximate operand position with
# the previous token: anything NOT in this set (an operator, '(', ',', a statement
# keyword, TO/STEP, or line start -> last_token_type None) is operand position, so
# TOP stands as the pseudo-variable. Keying on the previous token, not the
# preceding character, is what tells `P+2 TOP` (a value, so TO P) from `PRINT TOP`
# (operand, so the pseudo-variable) -- both have a space before TOP. See
# docs/bbc-tokeniser-to-top.md.
_TOP_VALUE_ENDERS = frozenset([
    'LITERAL_INTEGER', 'LITERAL_FLOAT', 'LITERAL_STRING',
    'ID', 'RPAREN', 'RBRAC',
    # nullary value keywords / pseudo-variables that complete an operand
    'COUNT', 'ERL', 'ERR', 'FALSE', 'GET', 'POS', 'PI', 'RND', 'TOP', 'TRUE',
    'VPOS', 'END', 'HIMEM', 'LOMEM', 'PTR', 'TIME', 'TIME_STR', 'PAGE',
])

def t_TOP(t):
    # TOP only as a COMPLETE word (negative lookahead): TOPI falls through to
    # TO + PI, matching the ROM's name-run rule. When the previous token ends a
    # value, this TOP is the FOR byte-saver -- glued (P+2TOP+98) or spaced
    # (P+2 TOP+98), after a number, variable, ), ], or value keyword: emit TO and
    # leave the P to re-lex. Verified on the ROM: PRINT TOP prints an address, but
    # FORI=P+2TOP+98 runs as FOR I=P+2 TO P+98. (STOP is unaffected: its own rule
    # consumes the whole word before this one is tried.)
    r'TOP(?![A-Za-z0-9_])'
    if t.lexer.last_token_type in _TOP_VALUE_ENDERS:
        t.type = 'TO'
        t.value = 'TO'
        t.lexer.lexpos = t.lexpos + 2  # consumed only 'TO'; 'P...' re-lexes next
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
    r'[a-zA-Z_`][a-zA-Z_0-9`]*(%%|[$%&~])?\('
    t.type = reserved.get(t.value, 'ARRAYID_LPAREN')
    return t

# TODO: Cannot use @ symbol at the beginning of
#       any variable name. @% is a special variable
def t_ID(t):
    r'([@a-zA-Z_`][a-zA-Z_0-9`]*(%%|[$%&~])?)'
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
    # A string body is any run of non-quote characters, with "" an escaped quote.
    # The inner alternative is a SINGLE character ([^"], not [^"]+): a nested
    # quantifier ([^"]+ inside *) backtracks catastrophically on an unterminated
    # string ("abc... with no closing quote), hanging the lexer.
    r'"((?:[^"]|"")*)"(?!")'
    t.value = t.value[1:-1].replace('""', '"')
    return t

def t_LITERAL_FLOAT(t):
    # Digits optional on both sides of the point, so '.5', '5.' and a lone '.'
    # are all accepted; in BBC BASIC a bare '.' is the number 0 (e.g. the
    # deliberate infinite loop REPEAT UNTIL .). The second alternative accepts
    # E-notation with no decimal point, as BBC BASIC does (70E9, 1E10, 10E3).
    r'\d*\.\d*(?:E[+-]?\d+)?|\d+E[+-]?\d+'
    try:
        t.value = float(t.value)
    except ValueError:
        t.value = 0.0   # a lone '.' (or '.E..') is zero
    return t

def t_LITERAL_INTEGER(t):
    r'\d+'
    try:
        t.value = int(t.value)
    except ValueError:
        print("Number %s is too large!" % t.value)
        t.value = 0
    return t

def t_LITERAL_HEX_INTEGER(t):
    r'&[\dA-F]+'
    # A BBC BASIC hex constant is a bit pattern in a signed integer cell, not a
    # magnitude: an 8-hex-digit value with the top bit set is negative
    # (&AABBCCDD = -1430532899). The ROM folds digits into a 32-bit cell with no
    # overflow check (factor_hex). We size by digit count so OWL's 64-bit
    # integers are writable too: up to 8 digits -> signed 32-bit pattern, 9-16 ->
    # signed 64-bit pattern.
    digits = t.value[1:]
    width = 64 if len(digits) > 8 else 32
    value = int(digits, 16) & ((1 << width) - 1)
    if value >> (width - 1):           # top bit set -> negative
        value -= 1 << width
    t.value = value
    t.type = 'LITERAL_INTEGER'
    return t

def t_LITERAL_BINARY_INTEGER(t):
    r'%[01]+'
    try:
        t.value = int(t.value[1:], 2)
        t.type = 'LITERAL_INTEGER'
    except ValueError:
        print("Number %s is too large!" % t.value)
        t.value = 0
    return t

# Error handling rule
def t_error(t):
    # Count characters that cannot be tokenised so the front end can tell
    # binary/non-text input (a tokenised image, embedded data, garbage) from a
    # genuine syntax error in a text listing. buildLexer initialises the counter.
    count = getattr(t.lexer, "num_illegal_characters", 0)
    t.lexer.num_illegal_characters = count + 1
    t.lexer.skip(1)



