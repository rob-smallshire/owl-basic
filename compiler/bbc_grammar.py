import logging

import ply.yacc as yacc

# Get the token map from the lexer.  This is required.
from bbc_lexer import tokens
from bbc_ast import *

# Precedence table for the above operators
precedence = (
             ('right', 'UEQUAL'),
             ('left', 'EOR', 'OR'),
             ('left', 'AND'),
             ('nonassoc', 'EQ', 'NE', 'LTE', 'GTE', 'LT', 'GT', 'SHIFT_LEFT', 'SHIFT_RIGHT', 'SHIFT_RIGHT_UNSIGNED'),
             ('left', 'PLUS', 'MINUS'),
             ('left', 'TIMES', 'DIVIDE', 'MOD', 'DIV'),
             ('left', 'CARET'),
             ('left', 'PLING', 'QUERY'),  # Binary indirection operators
             ('right', 'FUNCTION', 'NOT', 'UPLUS', 'UMINUS', 'UPLING', 'UQUERY', 'UPIPE', 'UDOLLAR', 'UHASH'), # Unary operators
             )

def p_program(p):
    'program : statement_list'
    p[0] = Program(statements = p[1])
            
def p_statement_list(p):
    '''statement_list : compound_statement
                      | statement_list compound_statement'''
    if len(p) == 2:
        p[0] = StatementList()
        p[0].append(p[1])
    elif len(p) == 3:
        p[1].append(p[2])
        p[0] = p[1]
        
# A single line statement list - use in single-line IF THEN ELSE construct
def p_compound_statement(p):
    '''compound_statement : lone_stmt_body stmt_terminator
                          | multi_statement stmt_terminator'''
    p[0] = p[1]
        
def p_multi_statement(p):
    '''multi_statement : statement statements_tail'''
    p[2].prepend(p[1])
    p[0] = p[2]
    
def p_statements_tail(p):
    '''statements_tail : statement_separator statement statements_tail
                       | empty'''
    if len(p) == 4:
        p[3].prepend(p[2])
        p[0] = p[3]
    elif len(p) == 2:
        p[0] = StatementList() 

def p_statement_separator(p):
    'statement_separator : COLON'
    p[0] = p[1]

def p_stmt_terminator(p):
    'stmt_terminator : EOL'
    p[0] = p[1]
            
def p_statement(p):
    '''statement : stmt_body
                 | empty'''
    p[0] = p[1]

#=============================================================================#
# STATEMENTS

# TODO: Statements to be implemented
    '''stmt_body : chain_stmt
                 | local_stmt
                 | on_error_stmt
                 | restore_stmt    PAGE 69 BBCBASIC.PDF - RESTORE +offset???
                 | trace_stmt'''
    
# Statements which must appear alone on
# their own line
def p_lone_stmt_body(p):
    '''lone_stmt_body : case_stmt'''
    p[0] = p[1]
    
# Statements which can appear alone,
# or in compound statements on one line
def p_stmt_body(p):
    '''stmt_body : beats_stmt
                 | bput_stmt
                 | call_stmt
                 | circle_stmt
                 | clear_stmt
                 | clg_stmt
                 | cls_stmt
                 | close_stmt
                 | colour_stmt
                 | data_stmt
                 | def_stmt
                 | dim_stmt
                 | draw_stmt
                 | ellipse_stmt
                 | end_stmt
                 | end_fn_stmt
                 | endproc_stmt
                 | envelope_stmt
                 | error_stmt
                 | fill_stmt
                 | gcol_stmt
                 | goto_stmt
                 | on_goto_stmt
                 | gosub_stmt
                 | input_stmt
                 | install_stmt
                 | if_stmt
                 | for_stmt
                 | line_stmt
                 | library_stmt
                 | let_stmt
                 | local_stmt
                 | mode_stmt
                 | mouse_stmt
                 | move_stmt
                 | off_stmt
                 | on_stmt
                 | origin_stmt
                 | oscli_stmt
                 | next_stmt
                 | plot_stmt
                 | point_stmt
                 | print_stmt
                 | proc_stmt
                 | quit_stmt
                 | read_stmt
                 | rectangle_stmt
                 | repeat_stmt
                 | report_stmt
                 | restore_stmt
                 | return_stmt
                 | sound_stmt
                 | stop_stmt
                 | stereo_stmt
                 | swap_stmt
                 | sys_stmt
                 | tempo_stmt
                 | tint_stmt
                 | until_stmt
                 | vdu_stmt
                 | voices_stmt
                 | while_stmt
                 | width_stmt
                 | wait_stmt
                 | endwhile_stmt'''
    p[0] = Statement(body = p[1])
        
def p_bput_stmt(p):
    '''bput_stmt : BPUT channel COMMA expr
                 | BPUT channel COMMA expr SEMICOLON'''
    if len(p) == 5:
        p[0] = Bput(channel = p[2], data = p[4], newline=True)
    elif len(p) == 6:
        p[0] = Bput(channel = p[2], data = p[4], newline=False)
    p[0].lineNum = p.lineno(1)
    
def p_call_stmt(p):
    '''call_stmt : CALL expr
                 | CALL expr COMMA writable_list'''
    if len(p) == 3:
        p[0] = Call(address = p[2])
    elif len(p) == 5:
        p[0] = Call(address = p[2], parameters = p[4])
    p[0].lineNum = p.lineno(1)
    
# TODO CASE stmt
# Not that WHEN clauses which follow the OTHERWISE clause
# a legal, but cannot be executed.
# TODO : Put this into a special class of statements which
# must begin on a new line.
def p_case_stmt(p):
    '''case_stmt : CASE expr OF stmt_terminator when_clause_list ENDCASE'''
    p[0] = Case(condition = p[2], whenClauses = p[5])
    p[0].lineNum = p.lineno(1)

def p_when_clause_list(p):
    '''when_clause_list : when_clause
                        | when_clause_list when_clause'''
    if len(p) == 2:
        p[0] = WhenClauseList()
        p[0].append(p[1])
    elif len(p) == 3:
        p[1].append(p[2])
        p[0] = p[1]
    
def p_when_clause(p):
    '''when_clause : WHEN expr_list COLON statement_list
                   | OTHERWISE statement_list'''
    if len(p) == 5:
        p[0] = WhenClause(matches = p[2], statements = p[4])
    elif len(p) == 3:
        p[0] = OtherwiseClause(statements = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_beats_stmt(p):
    '''beats_stmt : BEATS expr'''
    p[0] = Beats(counter = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_circle_stmt(p):
    '''circle_stmt : CIRCLE expr COMMA expr COMMA expr
                   | CIRCLE FILL expr COMMA expr COMMA expr'''
    if len(p) == 7:
        p[0] = Circle(xCoord = p[2], yCoord = p[4], radius = p[6])
    elif len(p) == 8:
        p[0] = Circle(xCoord = p[3], yCoord = p[5], radius = p[7], fill=True)
    p[0].lineNum = p.lineno(1)
    
def p_clear_stmt(p):
    'clear_stmt : CLEAR'
    p[0] = Clear()
    p[0].lineNum = p.lineno(1)
    
def p_close_stmt(p):
    'close_stmt : CLOSE channel'
    p[0] = Close(channel = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_clg_stmt(p):
    'clg_stmt : CLG'
    p[0] = Clg()
    p[0].lineNum = p.lineno(1)
    
def p_cls_stmt(p):
    'cls_stmt : CLS'
    p[0] = Cls()
    p[0].lineNum = p.lineno(1)
    
def p_colour_stmt(p):
    '''colour_stmt : COLOUR expr
                   | COLOUR expr COMMA expr
                   | COLOUR expr TINT expr
                   | COLOUR expr COMMA expr COMMA expr COMMA expr'''
    if len(p) == 3:
        p[0] = Colour(colour = p[2])
    elif len(p) == 5:
        if p[3] == "TINT":
            p[0] = Colour(colour = p[2], tint = p[4])
        else:
            p[0] = Palette(logicalColour = p[2], physicalColour = p[4])
    elif len(p) == 9:
        p[0] = Palette(logicalColour = p[2], red = p[4], green = p[6], blue = p[8])
    p[0].lineNum = p.lineno(1)
    

# DATA
def p_data_statement(p):
    'data_stmt : DATA'
    p[0] = Data(data = p[1])
    p[0].lineNum = p.lineno(1)
    
def p_def_stmt(p):
    '''def_stmt : def_fn_stmt
                | def_proc_stmt'''
    p[0] = p[1]
    
# The statement list needs to be modified so there can be more
# than one point of return form functions
def p_def_fn_stmt(p):
    '''def_fn_stmt : DEF FN_ID statement
                   | DEF FN_ID LPAREN formal_arg_list RPAREN statement'''
    
    if len(p) == 4:
        p[0] = DefineFunction(name = p[2], followingStatement = p[3])
    elif len(p) == 7:
        p[0] = DefineFunction(name = p[2], formalParameters = p[4], followingStatement = p[6])
    p[0].lineNum = p.lineno(1)
    
def p_end_fn_stmt(p):
    '''end_fn_stmt : EQ expr %prec UEQUAL'''
    p[0] = ReturnFromFunction(returnValue = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_def_proc_stmt(p):
    '''def_proc_stmt : DEF PROC_ID statement
                     | DEF PROC_ID LPAREN formal_arg_list RPAREN statement'''
    if len(p) == 4:
        p[0] = DefineProcedure(name = p[2], followingStatement = p[3])
    elif len(p) == 7:
        p[0] = DefineProcedure(name = p[2], formalParameters = p[4], followingStatement = p[6])
    p[0].lineNum = p.lineno(1)
    
def p_endproc_stmt(p):
    '''endproc_stmt : ENDPROC'''
    p[0] = ReturnFromProcedure()
    p[0].lineNum = p.lineno(1)
    
def p_proc_stmt(p):
    '''proc_stmt : PROC_ID
                 | PROC_ID LPAREN actual_arg_list RPAREN'''
    if len(p) == 2:
        p[0] = CallProcedure(name = p[1])
    elif len(p) == 5:
        p[0] = CallProcedure(name = p[1], actualParameters = p[3])
    p[0].lineNum = p.lineno(1)

def p_dim_statement(p):
    '''dim_stmt : DIM dim_list'''
    p[0] = Dim(items = p[2])
    p[0].lineNum = p.lineno(1)

def p_dim_list(p):
    '''dim_list : dim_item
                | dim_list COMMA dim_item'''
    if len(p) == 2:
        p[0] = DimList()
        p[0].append(p[1])
    elif len(p) == 4:
        p[1].append(p[3])
        p[0] = p[1]
        
def p_dim_item(p):
    # TODO: BB4W structures would be added here
    '''dim_item : indexer
                | variable expr'''
    if len(p) == 2:
        p[0] = AllocateArray(identifier = p[1].identifier, dimensions = p[1].indices)
    elif len(p) == 3:
        p[0] = AllocateBlock(identifier = p[1], size = p[2])
    
    
def p_draw_stmt(p):
    '''draw_stmt : DRAW expr COMMA expr
                 | DRAW BY expr COMMA expr'''
    if len(p) == 5:
        p[0] = Draw(xCoord = p[2], yCoord = p[4])
    elif len(p) == 6:
        p[0] = Draw(xCoord = p[3], yCoord = p[5], relative=True)
    p[0].lineNum = p.lineno(1)
    
def p_end_stmt(p):
    '''end_stmt : END'''
    p[0] = End()
    p[0].lineNum = p.lineno(1)
    
def p_ellipse_stmt(p): # BBC BASIC V also supports rotation of an ellipse
    '''ellipse_stmt : ELLIPSE expr COMMA expr COMMA expr COMMA expr
                    | ELLIPSE FILL expr COMMA expr COMMA expr COMMA expr
                    | ELLIPSE expr COMMA expr COMMA expr COMMA expr COMMA expr
                    | ELLIPSE FILL expr COMMA expr COMMA expr COMMA expr COMMA expr'''

    if len(p) == 9:
        p[0] = Ellipse(xCoord = p[2], yCoord = p[4], semiMajor = p[6], semiMinor = p[8])
    elif len(p) == 10:
        p[0] = Ellipse(xCoord = p[3], yCoord = p[5], semiMajor = p[7], semiMinor = p[9], fill=True)
    elif len(p) == 11:
        p[0] = Ellipse(xCoord = p[2], yCoord = p[4], semiMajor = p[6], semiMinor = p[8], radians = p[10])
    elif len(p) == 12:
        p[0] = Ellipse(xCoord = p[3], yCoord = p[5], semiMajor = p[7], semiMinor = p[9], radians = p[11], fill=True)
    p[0].lineNum = p.lineno(1)
    

def p_error_stmt(p):
    '''error_stmt : ERROR expr COMMA expr
                  | ERROR EXT expr COMMA expr'''
    # TODO: Needs to handle the EXT keyword for returning an external error code
    #       ERROR EXT ERR, REPORT$ : REM pass on the error
    if len(p) == 5:
        p[0] = GenerateError(number = p[2], description = p[4])
    elif len(p) == 6:
        p[0] = ReturnError(number = p[2], description = p[4])
    p[0].lineNum = p.lineno(1)
    
def p_envelope_stmt(p):
    '''envelope_stmt : ENVELOPE expr COMMA expr COMMA expr COMMA expr COMMA expr COMMA expr COMMA expr COMMA expr COMMA expr COMMA expr COMMA expr COMMA expr COMMA expr COMMA expr'''
    p[0] = Envelope(n = p[2], t = p[4], picth1 = p[6], picth2 = p[8], pitch3 = p[10],
                    numSteps1 = p[12], numSteps2 = p[14], numSteps3 = p[16],
                    amplitudeAttack = p[18], amplitudeDecay = p[20], amplitudeSustain = p[22],
                    amplitudeRelease = p[24], targetAttack = p[26], targetDecay = p[28] )
    p[0].lineNum = p.lineno(1)

def p_fill_stmt(p):
    '''fill_stmt : FILL expr COMMA expr
                 | FILL BY expr COMMA expr'''
    if len(p) == 5:
        p[0] = Fill(xCoord = p[2], yCoord = p[4])
    elif len(p) == 6:
        p[0] = Fill(xCoord = p[3], yCoord = p[5], fill=True)
    p[0].lineNum = p.lineno(1)
    
def p_gcol_stmt(p):
    '''gcol_stmt : GCOL expr
                 | GCOL expr COMMA expr
                 | GCOL expr TINT expr
                 | GCOL expr COMMA expr TINT expr'''
    if len(p) == 3:
        p[0] = Gcol(logicalColour = p[2])
    elif len(p) == 5:
        if p[3] == 'TINT':
            p[0] = Gcol(logicalColour = p[2], tint = p[4])
        else:
            p[0] = Gcol(mode = p[2], logicalColour = p[4])
    elif len(p) == 7:
        p[0] = Gcol(mode = p[2], logicalColour = p[4], tint = p[6])
    p[0].lineNum = p.lineno(1)

def p_input_stmt(p):
    '''input_stmt : INPUT 
                  | INPUT input_list
                  | LINE INPUT
                  | LINE INPUT input_list
                  | INPUT LINE
                  | INPUT LINE input_list
                  | INPUT channel COMMA variable_list'''
    # TODO: All other syntax of input to replace the second line above - see PRINT
    if len(p) == 2:
        #INPUT 
        p[0] = Input()
    elif len(p) == 3:
        if p[1] == "LINE":
            #LINE INPUT
            p[0] = Input(inputLine = True) 
        elif p[2] == "LINE":
            #INPUT LINE
            p[0] = Input(inputLine = True) 
        else:
            #INPUT input_list
            p[0] = Input(inputList = p[2])
    elif len(p) == 4:
        if p[1] == "LINE":
            #LINE INPUT input_list
            p[0] = Input(inputLine = True, inputList = p[3]) 
        elif p[2] == "LINE":
            #INPUT LINE input_list
            p[0] = Input(inputLine = True, inputList = p[3])
    elif len(p) == 5:
        p[0] = InputFile(channel = p[2], items = p[4])
    p[0].lineNum = p.lineno(1)  

def p_input_list(p):
    '''input_list : input_item
                  | input_list input_item'''
    if len(p) == 2:
        p[0] = InputList()
        p[0].append(p[1])
    elif len(p) == 3:
        p[1].append(p[2])
        p[0] = p[1]
    
def p_input_item(p):
    '''input_item : literal_string
                  | tab
                  | spc
                  | input_manipulator
                  | writable'''
    p[0] = InputItem(item = p[1])
    
def p_input_manipulator(p):
    '''input_manipulator : APOSTROPHE
                         | COMMA
                         | SEMICOLON'''
    p[0] = InputManipulator(manipulator = p[1])
    p[0].lineNum = p.lineno(1)




    
def p_install_stmt(p):
    '''install_stmt : INSTALL expr'''
    if len(p) == 3:
        p[0] = Install(filename = p[2])
    p[0].lineNum = p.lineno(1)
    
# GOTO statement
def p_goto_stmt(p):
    '''goto_stmt : GOTO factor'''
    p[0] = Goto(targetLogicalLine = p[2])
    p[0].lineNum = p.lineno(1)

def p_on_goto_stmt(p):
    '''on_goto_stmt : ON expr GOTO expr_list
                    | ON expr GOTO expr_list ELSE multi_statement'''
    # TODO ELSE clause
    if len(p) == 5:
        p[0] = OnGoto(switch = p[2], targetLogicalLines = p[4])
    elif len(p) == 7:
        p[0] = OnGoto(switch = p[2], targetLogicalLines = p[4], outOfRangeClause = p[6])
    
# GOSUB statement
def p_gosub(p):
    '''gosub_stmt : GOSUB factor'''
    p[0] = Gosub(targetLogicalLine = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_return_stmt(p):
    '''return_stmt : RETURN'''
    p[0] = Return()
    p[0].lineNum = p.lineno(1)
    
def p_if_stmt(p):
    '''if_stmt : if_single_stmt'''
    #'''if_stmt : if_single_stmt
    #           | if_multi_stmt'''
    p[0] = p[1]
    
def p_if_single_stmt(p):
    '''if_single_stmt : IF expr clause
                      | IF expr THEN clause
                      | IF expr clause ELSE clause
                      | IF expr THEN clause ELSE clause'''
    if len(p) == 4:
        p[0] = If(condition = p[2], trueClause = p[3])
    elif len(p) == 5:
        p[0] = If(condition = p[2], trueClause = p[4])
    elif len(p) == 6:
        p[0] = If(condition = p[2], trueClause = p[3], falseClause = p[5])
    elif len(p) == 7:
        p[0] = If(condition = p[2], trueClause = p[4], falseClause = p[6])
    p[0].lineNum = p.lineno(1)
    
# The clause is only used with IF statements and
# possible ON statements when the result of an expression
# is interpreted as a line number to GOTO
def p_clause(p):
    '''clause : multi_statement
              | implicit_goto'''
    p[0] = p[1]

def p_implicit_goto(p):
    '''implicit_goto : factor'''
    p[0] = Goto(targetLogicalLine = p[1])
    
def p_if_multi_stmt(p):
    '''if_multi_stmt : IF expr THEN statement_list ENDIF
                     | IF expr THEN statement_list ELSE statement_list ENDIF'''
    if len(p) == 6:
        p[0] = If(condition = p[2], trueClause = p[4])
    elif len(p) == 8:
        p[0] = If(condition = p[2], trueClause = p[4], falseClause = p[6])
    p[0].lineNum = p.lineno(1)
    
# The syntax ruls for FOR..NEXT loops are not implemented by the
# grammar owing to the fact that NEXT is treated as a statement,
# rather than as a loop terminator.  A later analysis of the parse
# tree will attempt to match each NEXT with its corresponding FOR
def p_for_stmt(p):
    '''for_stmt : FOR writable EQ expr TO expr
                | FOR writable EQ expr TO expr STEP expr'''
    if len(p) == 7:
        p[0] = ForToStep(identifier = p[2], first = p[4], last = p[6], step = LiteralInteger(value = 1))
    elif len(p) == 9:
        p[0] = ForToStep(identifier = p[2], first = p[4], last = p[6], step = p[8])
    p[0].lineNum = p.lineno(1)
    
# Rule for dealing with unmatched NEXT statements
def p_next_stmt(p):
    '''next_stmt : NEXT nullable_variable_list'''
    p[0] = Next(identifiers = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_library_stmt(p):
    '''library_stmt : LIBRARY expr'''
    p[0] = LoadLibrary(filename = p[2])
    p[0].lineNum = p.lineno(1)

def p_line_stmt(p):
    '''line_stmt : LINE expr COMMA expr COMMA expr COMMA expr'''

    # TODO: Sort this lot out!  
    p[0] = Line(x1Coord = p[2], y1Coord = p[4], x2Coord = p[6], y2Coord = p[8])
    p[0].lineNum = p.lineno(1)

def p_let_stmt(p):
    '''let_stmt : assignment
                | increment
                | decrement'''
    p[0] = p[1]
    
def p_assignment(p):
    '''assignment : LET variable EQ expr
                  | LET array EQ array_expr
                  | LET indexer EQ expr
                  | lvalue EQ expr
                  | array EQ array_expr
                  | indexer EQ expr'''
    if len(p) == 5:
        p[0] = Assignment(lValue = p[2], rValue = p[4])
        p[0].lineNum = p.lineno(1)
    elif len(p) == 4:
        p[0] = Assignment(lValue = p[1], rValue = p[3])
        p[0].lineNum = p.lineno(2)
    
def p_increment(p):
    '''increment : LET variable PLUS_ASSIGN expr
                 | LET array PLUS_ASSIGN expr
                 | LET indexer PLUS_ASSIGN expr
                 | variable PLUS_ASSIGN expr
                 | array PLUS_ASSIGN expr
                 | indexer PLUS_ASSIGN expr'''
    if len(p) == 5:
        p[0] = Increment(lValue = p[2], rValue = p[4])
        p[0].lineNum = p.lineno(1)
    elif len(p) == 4:
        p[0] = Increment(lValue = p[1], rValue = p[3])
        p[0].lineNum = p.lineno(2)
    
def p_decrement(p):
    '''decrement : LET variable MINUS_ASSIGN expr
                 | LET array MINUS_ASSIGN expr
                 | LET indexer MINUS_ASSIGN expr
                 | variable MINUS_ASSIGN expr
                 | array MINUS_ASSIGN expr
                 | indexer MINUS_ASSIGN expr'''
    if len(p) == 5:
        p[0] = Decrement(lValue = p[2], rValue = p[4])
        p[0].lineNum = p.lineno(1)
    elif len(p) == 4:
        p[0] = Decrement(lValue = p[1], rValue = p[3])
        p[0].lineNum = p.lineno(2)

# LOCAL statement
def p_local_stmt(p):
    '''local_stmt : LOCAL variable_list'''
    p[0] = Local(variables = p[2])
    p[0].lineNum = p.lineno(1)
    
# MOVE statement
def p_move_stmt(p):
    '''move_stmt : MOVE expr COMMA expr
                 | MOVE BY expr COMMA expr'''
    if len(p) == 5:
        p[0] = Move(xCoord = p[2], yCoord = p[4])
    elif len(p) == 6:
        p[0] = Move(xCoord = p[3], yCoord = p[5], relative=True)
    p[0].lineNum = p.lineno(1)
    
def p_mode_stmt(p):
    '''mode_stmt : MODE expr
                 | MODE expr COMMA expr COMMA expr
                 | MODE expr COMMA expr COMMA expr COMMA expr'''
    if len(p) == 3:
        p[0] = Mode(number = p[2])
    elif len(p) == 7:
        p[0] = Mode(width = p[2], height = p[4], bitsPerPixel = p[6])
    elif len(p) == 9:
        p[0] = Mode(width = p[2], height = p[4], bitsPerPixel = p[6], frameRate = p[8])
    p[0].lineNum = p.lineno(1)
    

def p_mouse_stmt(p):
    '''mouse_stmt : MOUSE writable COMMA writable COMMA writable
                  | MOUSE writable COMMA writable COMMA writable COMMA writable
                  | MOUSE ON
                  | MOUSE ON expr
                  | MOUSE OFF
                  | MOUSE TO expr COMMA expr
                  | MOUSE RECTANGLE expr COMMA expr COMMA expr COMMA expr
                  | MOUSE RECTANGLE OFF
                  | MOUSE STEP expr
                  | MOUSE STEP expr COMMA expr
                  | MOUSE COLOUR expr COMMA expr COMMA expr COMMA expr'''
    #nested IF is to see that the p[2] contains
    if str(p[2]) == 'ON':
        if len(p) == 3:
            #MOUSE ON
            p[0] = MousePointer(pointer = LiteralInteger(value = 0))
        elif len(p) == 4:
            #MOUSE ON expr
            p[0] = MousePointer(pointer = p[3])
    elif str(p[2]) == 'OFF':
        #MOUSE OFF
        p[0] = MousePointer(pointer = None)
    elif str(p[2]) == 'TO':
        #MOUSE TO
        p[0] = MousePosition(xCoord = p[3], yCoord = p[5])
    elif str(p[2]) == 'RECTANGLE':
        if len(p) == 10:
            #MOUSE RECTANGLE
            p[0] = MouseRectangle(left = p[3], bottom = p[5], right = p[7], top = p[9])
        elif len(p) == 4:
            #MOUSE RECTANGLE OFF
            p[0] = MouseRectangleOff()
    elif str(p[2]) == 'STEP':
        if len(p) == 4:
            #MOUSE STEP expr
            p[0] = MouseStep(xCoeff = p[3])
        if len(p) == 6:
            #MOUSE STEP expr COMMA expr
            p[0] = MouseStep(xCoeff = p[3], yCoeff = p[5])
    elif str(p[2]) == 'COLOUR':    #Not sure if i need to check for COLOR
        #MOUSE COLOUR expr COMMA expr COMMA expr COMMA expr
        p[0] = MouseColour(logicalColour = p[3], red = p[5], green = p[7], blue = p[9])
    else:
        if len(p) == 7:
            #MOUSE variable COMMA variable COMMA variable
            p[0] = Mouse(xCoord = p[2], yCoord = p[4], buttons = p[6])
        elif len(p) == 9:
            #MOUSE variable COMMA variable COMMA variable COMMA variable
            p[0] = Mouse(xCoord = p[2], yCoord = p[4], buttons = p[6], time = p[8])
    p[0].lineNum = p.lineno(1)
    

def p_on_stmt(p):
    '''on_stmt : ON'''
    p[0] = On()
    p[0].lineNum = p.lineno(1)
    
def p_off_stmt(p):
    '''off_stmt : OFF'''
    p[0] = Off()
    p[0].lineNum = p.lineno(1)
    
def p_origin_stmt(p):
    '''origin_stmt : ORIGIN expr COMMA expr'''
    p[0] = Origin(xCoord = p[2], yCoord = p[4])
    p[0].lineNum = p.lineno(1)
    
def p_oscli_stmt(p):
    '''oscli_stmt : OSCLI expr'''
    p[0] = Oscli(command = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_plot_stmt(p):
    '''plot_stmt : PLOT expr COMMA expr
                 | PLOT expr COMMA expr COMMA expr
                 | PLOT BY expr COMMA expr'''
    if len(p) == 5:
        p[0] = Plot(mode = LiteralInteger(65), xCoord = p[2], yCoord = p[4])
    elif len(p) == 6:
        p[0] = Plot(mode = LiteralInteger(65), xCoord = p[3], yCoord = p[5], relative=True)
    elif len(p) == 7:
        p[0] = Plot(mode = p[4], xCoord = p[6], yCoord = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_point_stmt(p):
    '''point_stmt : POINT expr COMMA expr
                  | POINT BY expr COMMA expr
                  | POINT TO expr COMMA expr'''
    if len(p) == 5:
        p[0] = Point(xCoord = p[2], yCoord = p[4])
    elif len(p) == 6:
        if str(p[3]) == 'BY':
            p[0] = Point(xCoord = p[4], yCoord = p[6], relative=True)
        else:
            p[0] = MousePosition(xCoord = p[4], yCoord = p[6], moveMouse=False, movePointer = True)
    p[0].lineNum = p.lineno(1)
    
def p_print_stmt(p):
    '''print_stmt : PRINT
                  | PRINT print_list
                  | PRINT channel COMMA actual_arg_list'''
    if len(p) == 2:
        p[0] = Print()
    elif len(p) == 3:
        p[0] = Print(printList = p[2])
    elif len(p) == 4:
        p[0] = PrintFile(channel = p[2], items = p[3])
    p[0].lineNum = p.lineno(1)
    
def p_print_list(p):
    '''print_list : print_item
                  | print_list print_item'''
    if len(p) == 2:
        p[0] = PrintList()
        p[0].append(p[1])
    elif len(p) == 3:
        p[1].append(p[2])
        p[0] = p[1]
    
def p_print_item(p):
    '''print_item : expr
                  | tab
                  | spc
                  | print_manipulator'''
    p[0] = PrintItem(item = p[1])
    
def p_print_manipulator(p):
    '''print_manipulator : TILDE
                         | APOSTROPHE
                         | COMMA
                         | SEMICOLON'''
    p[0] = PrintManipulator(manipulator = p[1])
    p[0].lineNum = p.lineno(1)
    
def p_quit_stmt(p):
    # TODO: BBC BASIC on the Iyonix supports a parameter to QUIT
    '''quit_stmt : QUIT'''
    p[0] = Quit()
    p[0].lineNum = p.lineno(1)

def p_read(p):
    '''read_stmt : READ
                 | READ writable_list'''
    if len(p) == 2:
        p[0] = Read()
    elif len(p) == 3:
        p[0] = Read(writables = p[2])
    
def p_rectangle_stmt(p):
    '''rectangle_stmt : RECTANGLE expr COMMA expr COMMA expr
                      | RECTANGLE expr COMMA expr COMMA expr COMMA expr
                      | RECTANGLE expr COMMA expr COMMA expr TO expr COMMA expr
                      | RECTANGLE expr COMMA expr COMMA expr COMMA expr TO expr COMMA expr
                      | RECTANGLE FILL expr COMMA expr COMMA expr
                      | RECTANGLE FILL expr COMMA expr COMMA expr COMMA expr
                      | RECTANGLE FILL expr COMMA expr COMMA expr TO expr COMMA expr
                      | RECTANGLE FILL expr COMMA expr COMMA expr COMMA expr TO expr COMMA expr
                      | RECTANGLE SWAP expr COMMA expr COMMA expr TO expr COMMA expr
                      | RECTANGLE SWAP expr COMMA expr COMMA expr COMMA expr TO expr COMMA expr'''

    # TODO: Sort this lot out!  
    if len(p) == 7:
        # RECTANGLE expr COMMA expr COMMA expr
        p[0] = Rectangle(xCoord = p[2], yCoord = p[4], width = p[6])
    elif len(p) == 9:
        # RECTANGLE expr COMMA expr COMMA expr COMMA expr
        p[0] = Rectangle(xCoord = p[2], yCoord = p[4], width = p[6], height = p[8])
    elif len(p) == 11:
        # RECTANGLE expr COMMA expr COMMA expr TO expr COMMA expr
        p[0] = CopyRectangle(xCoordSource = p[2], yCoordSource = p[4], width = p[6], xCoordTarget = p[8], yCoordTarget = p[10])
    elif len(p) == 13:
        # RECTANGLE expr COMMA expr COMMA expr COMMA expr TO expr COMMA expr
        p[0] = CopyRectangle(xCoordSource = p[2], yCoordSource = p[4], width = p[6], height = p[8], xCoordTarget = p[10], yCoordTarget = p[12])
    elif len(p) == 8:
        # RECTANGLE FILL expr COMMA expr COMMA expr
        p[0] = Rectangle(xCoord = p[3], yCoord = p[5], width = p[7], fill=True)
    elif len(p) == 10:
        # RECTANGLE FILL expr COMMA expr COMMA expr COMMA expr
        p[0] = Rectangle(xCoord = p[3], yCoord = p[5], width = p[7], height = p[9], fill=True)
    elif len(p) == 12:
        if str(p[2]) == "FILL":
            # RECTANGLE FILL expr COMMA expr COMMA expr TO expr COMMA expr
            p[0] = MoveRectangle(xCoordSource = p[3], yCoordSource = p[5], width = p[7], xCoordTarget = p[9], yCoordTarget = p[11])
        elif str(p[2]) == "SWAP":
            # RECTANGLE SWAP expr COMMA expr COMMA expr TO expr COMMA expr
            p[0] = SwapRectangle(xCoordSource = p[3], yCoordSource = p[5], width = p[7], xCoordTarget = p[9], yCoordTarget = p[11])
    elif len(p) == 14:
        if str(p[2]) == "FILL":
            # RECTANGLE FILL expr COMMA expr COMMA expr COMMA expr TO expr COMMA expr
            p[0] = MoveRectangle(xCoordSource = p[3], yCoordSource = p[5], width = p[7], height = p[9], xCoordTarget = p[11], yCoordTarget = p[13])
        elif str(p[2]) == "SWAP":
            # RECTANGLE SWAP expr COMMA expr COMMA expr COMMA expr TO expr COMMA expr
            p[0] = SwapRectangle(xCoordSource = p[3], yCoordSource = p[5], width = p[7], height = p[9], xCoordTarget = p[11], yCoordTarget = p[13])
    p[0].lineNum = p.lineno(1)
    
def p_report_stmt(p):
    '''report_stmt : REPORT'''
    p[0] = Report()
    p[0].lineNum = p.lineno(1)
    
def p_repeat_stmt(p):
    '''repeat_stmt : REPEAT statement'''
    p[0] = Repeat(followingStatement = p[2])

def p_restore_stmt(p):
    '''restore_stmt : RESTORE
                    | RESTORE expr'''
    # TODO restore data 
    # TODO restore + expr
    if len(p) == 2:
        p[0] = Restore()
    elif len(p) == 3:
        p[0] = Restore(targetLogicalLine = p[2])
    p[0].lineNum = p.lineno(1)

    
def p_sound_stmt(p):
    '''sound_stmt : SOUND expr COMMA expr COMMA expr COMMA expr
                  | SOUND ON
                  | SOUND OFF'''
    if len(p) == 9:
        p[0] = Sound(channel = p[2], amplitude = p[4], pitch = p[6], duration = p[8])
    elif len(p) == 3:
        if str(p[3]) == 'OFF':
            p[0] = Mute(mute=True)
        else:
            p[0] = Mute(mute=False)
    p[0].lineNum = p.lineno(1)
    
def p_stereo_stmt(p):
    '''stereo_stmt : STEREO expr COMMA expr'''
    p[0] = Stereo(channel = p[2], position = p[4])
    p[0].lineNum = p.lineno(1)
    
def p_swap_stmt(p):
    '''swap_stmt : SWAP writable COMMA writable
                 | SWAP array COMMA array'''
    #SWAP var1 COMMA var2
    #SWAP array1 COMMA array2
    p[0] = Swap(identifier1 = p[2], identifier2 = p[4])
    p[0].lineNum = p.lineno(1)
    
def p_sys_stmt(p):
    '''sys_stmt : SYS expr
                | SYS expr SEMICOLON writable
                | SYS expr TO nullable_writable_list
                | SYS expr COMMA nullable_expr_list
                | SYS expr TO nullable_writable_list SEMICOLON writable
                | SYS expr COMMA nullable_expr_list SEMICOLON writable
                | SYS expr COMMA nullable_expr_list TO nullable_writable_list
                | SYS expr COMMA nullable_expr_list TO nullable_writable_list SEMICOLON writable'''
    if len(p) == 3:
        p[0] = Sys(routine = p[2])
    elif len(p) == 5:
        if str(p[3]) == ';':  # TODO D.R.Y. Get this from the token somehow
            p[0] = Sys(routine = p[2], flags = p[4])
        elif str(p[3]) == "TO":
            p[0] = Sys(routine = p[2], returnValues = p[4])
        elif str(p[3]) == ',':
            p[0] = Sys(routine = p[2], actualParameters = p[4])
    elif len(p) == 7:
        if str(p[3]) == "TO":
            p[0] = Sys(routine = p[2], returnValues = p[4], flags = p[6])
        elif str(p[3]) == ',':
            if str(p[5]) == ';':
                p[0] = Sys(routine = p[2], actualParameters = p[4], flags = p[6])
            elif str(p[5]) == "TO":
                p[0] = Sys(routine = p[2], actualParameters = p[4], returnValues = p[6])
    elif len(p) == 9:
        p[0] = Sys(routine = p[2], actualParameters = p[4], returnValues = p[6], flags = p[8])
    p[0].lineNum = p.lineno(1)
        
def p_tab(p):
    '''tab : TAB_LPAREN expr RPAREN
           | TAB_LPAREN expr COMMA expr RPAREN'''
    if len(p) == 4:
        p[0] = TabH(xCoord = p[2])
    elif len(p) == 6:
        p[0] = TabXY(xCoord = p[2], yCoord = p[4])
    p[0].lineNum = p.lineno(1)
    
def p_tempo_stmt(p):
    '''tempo_stmt : TEMPO expr'''
    if len(p) == 3:
        #TEMPO expression
        p[0] = Tempo(rate = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_tint_stmt(p):
    '''tint_stmt : TINT expr COMMA expr'''
    p[0] = Tint(option = p[3], tint = p[5])
    p[0].lineNum = p.lineno(1)
    
def p_stop_stmt(p):
    '''stop_stmt : STOP'''
    p[0] = Stop()
    p[0].lineNum = p.lineno(1)
    
def p_spc(p):
    '''spc : SPC expr'''
    p[0] = Spc(spaces = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_until_stmt(p):
    '''until_stmt : UNTIL expr'''
    p[0] = Until(condition = p[2])
    p[0].lineNum = p.lineno(1)
    
# VDU
def p_vdu_stmt(p):
    '''vdu_stmt : VDU
                | VDU vdu_list'''
    if len(p) == 2:
        p[0] = Vdu()
    elif len(p) == 3:
        p[0] = Vdu(bytes = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_vdu_list(p):
    '''vdu_list : vdu_item
                | vdu_list vdu_item'''
    if len(p) == 2:
        p[0] = VduList()
        p[0].append(p[1])
    elif len(p) == 3:
        p[1].append(p[2])
        p[0] = p[1]
    
def p_vdu_item(p):
    '''vdu_item : expr vdu_separator
                | expr'''
    if len(p) == 2:
        p[0] = VduItem(item = p[1])
    elif len(p) == 3:
        p[0] = VduItem(item = p[1], length = p[2])
    
def p_vdu_separator(p):
    '''vdu_separator : COMMA
                     | SEMICOLON
                     | PIPE'''
    if p[1] == ',':
        p[0] = 1
    elif p[1] == ';':
        p[0] = 2
    elif p[1] == '|':
        p[0] = 9
    
def p_voices_stmt(p):
    '''voices_stmt : VOICES expr'''
    #VOICES expression
    p[0] = Voices(numberOfVoices = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_while_stmt(p):
    '''while_stmt : WHILE expr'''
    p[0] = While(condition = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_endwhile_stmt(p):
    '''endwhile_stmt : ENDWHILE'''
    p[0] = Endwhile()
    p[0].lineNum = p.lineno(1)
    
def p_width_stmt(p):
    '''width_stmt : WIDTH expr'''
    p[0] = Width(lineWidth = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_wait_stmt(p):
    '''wait_stmt : WAIT
                 | WAIT expr'''
    if len(p) == 2:
        #WAIT
        p[0] = Wait()
    elif len(p) == 3:
        #WAIT expr
        p[0] = Wait(centiseconds = p[2])
    p[0].lineNum = p.lineno(1)
    
#=============================================================================#
# ARGUMENTS
#

def p_actual_arg_list(p):
    '''actual_arg_list : actual_arg
                       | actual_arg_list COMMA actual_arg'''
    if len(p) == 2:
        p[0] = ActualArgList()
        p[0].append(p[1])
    if len(p) == 4:
        p[1].append(p[3])
        p[0] = p[1]
        p[0].lineNum = p.lineno(2)
    
def p_actual_arg(p):
    '''actual_arg : expr
                  | array'''
    p[0] = p[1]
    
def p_formal_arg_list(p):
    '''formal_arg_list : formal_arg
                       | formal_arg_list COMMA formal_arg'''
    if len(p) == 2:
        p[0] = FormalArgList()
        p[0].append(p[1])
    if len(p) == 4:
        p[1].append(p[3])
        p[0] = p[1]
    
def p_formal_arg(p):
    '''formal_arg : variable
                  | array
                  | RETURN variable
                  | RETURN array'''
    if len(p) == 2:
        p[0] = FormalArgument(argument = p[1])
    elif len(p) == 3:
        p[0] = FormalReferenceArgument(argument = p[2])
        p[0].lineNum = p.lineno(1)
    
#=============================================================================#
# FACTORS and EXPRESSIONS
#

# TODO: Removed indexer from factor temporarily
def p_factor(p):
    '''factor : literal
              | variable
              | pseudovariable
              | expr_group
              | expr_function
              | indexer
              | PLUS factor %prec UPLUS
              | MINUS factor %prec UMINUS'''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        if p[1] == '+':
            p[0] = UnaryPlus(factor = p[2])
        elif p[1] == '-':
            p[0] = UnaryMinus(factor = p[2])
        p[0].lineNum = p.lineno(1)

def p_unary_indirection(p):
    '''unary_indirection : QUERY factor %prec UQUERY
                         | PLING factor %prec UPLING
                         | PIPE factor %prec UPIPE
                         | DOLLAR factor %prec UDOLLAR'''
    if p[1] == '?':
        p[0] = UnaryByteIndirection(expression = p[2])
    elif p[1] == '!':
        p[0] = UnaryIntegerIndirection(expression = p[2])
    elif p[1] == '$':
        p[0] = UnaryStringIndirection(expression = p[2])
    elif p[1] == '|':
        p[0] = UnaryFloatIndirection(expression = p[2])
    p[0].lineNum = p.lineno(1)

def p_expr_list(p):
    '''expr_list : expr
                 | expr_list COMMA expr'''
    if len(p) == 2:
        p[0] = ExpressionList()
        p[0].append(p[1])
    elif len(p) == 4:
        p[1].append(p[3])
        p[0] = p[1]
    
def p_nullable_expr(p):
    '''nullable_expr : expr
                     | empty'''
    p[0] = p[1]
    
def p_nullable_expr_list(p):
    '''nullable_expr_list : nullable_expr
                          | nullable_expr_list COMMA nullable_expr'''
    if len(p) == 2:
        p[0] = ExpressionList()
        p[0].append(p[1])
    elif len(p) == 4:
        p[1].append(p[3])
        p[0] = p[1]
    
# TODO : Should any of these expressions take factors rather than expr as operands
def p_expr(p):
    '''expr : factor
            | expr PLUS expr
            | expr MINUS expr
            | expr TIMES expr
            | expr DIVIDE expr
            | expr MOD expr
            | expr DIV expr
            | expr CARET expr
            | expr EQ expr
            | expr NE expr
            | expr LTE expr
            | expr GTE expr
            | expr LT expr
            | expr GT expr
            | expr SHIFT_LEFT expr
            | expr SHIFT_RIGHT expr
            | expr SHIFT_RIGHT_UNSIGNED expr
            | expr AND expr
            | expr OR expr
            | expr EOR expr
            | dyadic_indirection'''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 4:
        if p[2] == '+':
            p[0] = Plus(lhs = p[1], rhs = p[3])
        elif p[2] == '-':
            p[0] = Minus(lhs = p[1], rhs = p[3])
        elif p[2] == '*':
            p[0] = Multiply(lhs = p[1], rhs = p[3])
        elif p[2] == '/':
            p[0] = Divide(lhs = p[1], rhs = p[3])
        elif p[2] == 'DIV':
            p[0] = IntegerDivide(lhs = p[1], rhs = p[3])
        elif p[2] == 'MOD':
            p[0] = IntegerModulus(lhs = p[1], rhs = p[3])
        elif p[2] == '^':
            p[0] = Power(lhs = p[1], rhs = p[3])
        elif p[2] == '=':
            p[0] = Equal(lhs = p[1], rhs = p[3])
        elif p[2] == '<>':
            p[0] = NotEqual(lhs = p[1], rhs = p[3])
        elif p[2] == '<':
            p[0] = LessThan(lhs = p[1], rhs = p[3])
        elif p[2] == '<=':
            p[0] = LessThanEqual(lhs = p[1], rhs = p[3])
        elif p[2] == '>':
            p[0] = GreaterThan(lhs = p[1], rhs = p[3])
        elif p[2] == '>=':
            p[0] = GreaterThanEqual(lhs = p[1], rhs = p[3])
        elif p[2] == '<<':
            p[0] = ShiftLeft(lhs = p[1], rhs = p[3])
        elif p[2] == '>>':
            p[0] = ShiftRight(lhs = p[1], rhs = p[3])
        elif p[2] == '>>>':
            p[0] = ShiftRightUnsigned(lhs = p[1], rhs = p[3])
        elif p[2] == 'AND':
            p[0] = And(lhs = p[1], rhs = p[3])
        elif p[2] == 'OR':
            p[0] = Or(lhs = p[1], rhs = p[3])
        elif p[2] == 'EOR':
            p[0] = Eor(lhs = p[1], rhs = p[3])
        p[0].lineNum = p.lineno(2)

def p_dyadic_indirection(p):
    """dyadic_indirection : variable QUERY factor
                          | variable PLING factor"""
    if p[2] == '?':
        # TODO: Ideally we would want to require that the LHS
        #       of the dyadic indirection operators is a simple
        #       variable.  Doesn't work yet, though.
        p[0] = DyadicByteIndirection(base = p[1], offset = p[3])
    elif p[2] == '!':
        p[0] = DyadicIntegerIndirection(base = p[1], offset = p[3])
    p[0].lineNum = p.lineno(2)
    
def p_expr_group(p):
    'expr_group : LPAREN expr RPAREN'
    p[0] = p[2]
    

#=============================================================================#
# VALUES
#

# This contains all of the lvalues which can occur on the
# left-hand-side on an assignment operator (without the LET).
def p_lvalue(p):
    '''lvalue : writable
              | pseudovariable
              | mid_str_lvalue
              | right_str_lvalue
              | left_str_lvalue'''
    p[0] = p[1]

# This contains values which can be written or assigned to in 
# for example FOR and READ
def p_writable(p):
    '''writable : variable
                | unary_indirection
                | dyadic_indirection'''
    p[0] = p[1]
    
def p_writable_list(p):
    '''writable_list : writable
                     | writable_list COMMA writable'''
    if len(p) == 2:
        p[0] = WritableList()
        p[0].append(p[1])
    elif len(p) == 4:
        p[1].append(p[3])
        p[0] = p[1]
            
def p_mid_str_lvalue(p):
    '''mid_str_lvalue : MID_STR_LPAREN variable COMMA expr RPAREN
                      | MID_STR_LPAREN variable COMMA expr COMMA expr RPAREN'''
    if len(p) == 6:
        p[0] = MidStrLValue(target = p[2], position = p[4])
    elif len(p) == 8:
        p[0] = MidStrLValue(target = p[2], position = p[4], length = p[6])
    p[0].lineNum = p.lineno(1)
    
def p_right_str_lvalue(p):
    '''right_str_lvalue : RIGHT_STR_LPAREN variable RPAREN
                        | RIGHT_STR_LPAREN variable COMMA expr RPAREN'''
    if len(p) == 4:
        p[0] = RightStrLValue(target = p[2])
    elif len(p) == 6:
        p[0] = RightStrLValue(target = p[2], length = p[4])
    p[0].lineNum = p.lineno(1)
        
def p_left_str_lvalue(p):
    '''left_str_lvalue : LEFT_STR_LPAREN variable RPAREN
                       | LEFT_STR_LPAREN variable COMMA expr RPAREN'''
    if len(p) == 4:
        p[0] = LeftStrLValue(target = p[2])
    elif len(p) == 6:
        p[0] = LeftStrLValue(target = p[2], length = p[4])
    p[0].lineNum = p.lineno(1)

#=============================================================================#
# PSEUDOVARIABLES
#

def p_pseudovariable(p):
    '''pseudovariable : end_value
                      | ext_value
                      | himem_value
                      | lomem_value
                      | ptr_value
                      | time_value
                      | time_str_value
                      | page_value'''
    p[0] = p[1]
    
# END is not officially a pseudovariable, although it can be used like one,
# although it may also be used as a statement
def p_end_value(p):
    'end_value : END'
    p[0] = EndValue()
    p[0].lineNum = p.lineno(1)
    
def p_ext(p):
    '''ext_value : EXT channel'''
    p[0] = ExtValue(channel = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_himem_value(p):
    'himem_value : HIMEM'
    p[0] = HimemValue()
    p[0].lineNum = p.lineno(1)
    
def p_lomem_value(p):
    'lomem_value : LOMEM'
    p[0] = LomemValue()
    p[0].lineNum = p.lineno(1)
    
def p_page_value(p):
    'page_value : PAGE'
    p[0] = PageValue()
    p[0].lineNum = p.lineno(1)
    
def p_ptr_value(p):
    'ptr_value : PTR channel'
    p[0] = PtrValue(channel = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_time_value(p):
    'time_value : TIME'
    p[0] = TimeValue()
    p[0].lineNum = p.lineno(1)
    
def p_time_str_value(p):
    'time_str_value : TIME_STR'
    p[0] = TimeStrValue()
    p[0].lineNum = p.lineno(1)
    

#=============================================================================#
# FUNCTIONS
#

# TODO: Functions to be implemented
'''    expr_function :
                     | eval_func
                     | report_str_func
                     | string_str_func
                     | sum_func
                     | usr_func'''

def p_expr_function(p):
    '''expr_function : user_func
                     | adval_func
                     | abs_func
                     | acs_func
                     | asc_func
                     | asn_func
                     | atn_func
                     | beat_func
                     | beats_func
                     | bget_func
                     | chr_str_func
                     | cos_func
                     | count_func
                     | deg_func
                     | dim_func
                     | err_func
                     | erl_func
                     | exp_func
                     | eof_func
                     | false_func
                     | get_func
                     | get_str_func
                     | get_str_file_func
                     | inkey_func
                     | inkey_str_func
                     | instr_func
                     | int_func
                     | left_str_func
                     | len_func
                     | ln_func
                     | log_func
                     | mid_str_func
                     | mod_func
                     | mode_func
                     | not_func
                     | openin_func
                     | openout_func
                     | openup_func
                     | pi_func
                     | pos_func
                     | point_func
                     | sin_func
                     | sgn_func
                     | sqr_func
                     | tan_func
                     | rad_func
                     | right_str_func
                     | rnd_func
                     | str_str_func
                     | sum_func
                     | sumlen_func
                     | tempo_func
                     | tint_func
                     | top_func
                     | true_func
                     | val_func
                     | vpos_func
                     | width_func'''
    p[0] = p[1]
    

def p_user_func(p):
    'user_func : FN_ID LPAREN actual_arg_list RPAREN %prec FUNCTION'
    p[0] = UserFunc(name = p[1], actualParameters = p[3])
    p[0].lineNum = p.lineno(1)

def p_abs_func(p):
    'abs_func : ABS factor %prec FUNCTION'
    p[0] = AbsFunc(factor = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_acs_func(p):
    'acs_func : ACS factor %prec FUNCTION'
    p[0] = AcsFunc(factor = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_adval_func(p):
    'adval_func : ADVAL factor %prec FUNCTION'
    p[0] = AdvalFunc(factor = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_asn_func(p):
    'asn_func : ASN factor %prec FUNCTION'
    p[0] = AsnFunc(factor = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_asc_func(p):
    'asc_func : ASC factor %prec FUNCTION'
    p[0] = AscFunc(factor = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_atn_func(p):
    '''atn_func : ATN factor %prec FUNCTION'''
    p[0] = AtnFunc(factor = p[2] )
    p[0].lineNum = p.lineno(1)

def p_beat_func(p):
    'beat_func : BEAT %prec FUNCTION'
    p[0] = BeatFunc()
    p[0].lineNum = p.lineno(1)

def p_beats_func(p):
    '''beats_func : BEATS %prec FUNCTION'''
    p[0] = BeatsFunc()
    p[0].lineNum = p.lineno(1)

def p_bget_func(p):
    'bget_func : BGET channel %prec FUNCTION'
    p[0] = BgetFunc(channel = p[2])
    p[0].lineNum = p.lineno(1)

def p_chr_str_func(p):
    'chr_str_func : CHR_STR expr %prec FUNCTION'
    p[0] = ChrStrFunc(factor = p[2])
    p[0].lineNum = p.lineno(1)

def p_cos_func(p):
    'cos_func : COS expr %prec FUNCTION'
    p[0] = CosFunc(factor = p[2])
    p[0].lineNum = p.lineno(1)    

def p_count_func(p):
    'count_func : COUNT %prec FUNCTION'
    p[0] = CountFunc()
    p[0].lineNum = p.lineno(1)

def p_deg_func(p):
    'deg_func : DEG factor %prec FUNCTION'
    p[0] = DegFunc(factor = p[2])
    p[0].lineNum = p.lineno(1)

def p_dim_func(p):
    '''dim_func : DIM_LPAREN array RPAREN
                | DIM_LPAREN array COMMA expr RPAREN'''
    if len(p) == 4:
        p[0] = DimensionsFunc(array = p[2])
    elif len(p) == 6:
        p[0] = DimensionSizeFunc(array = p[2], dimension = p[4])
    p[0].lineNum = p.lineno(1)

def p_erl_func(p):
    '''erl_func : ERL %prec FUNCTION'''
    p[0] = ErlFunc()
    p[0].lineNum = p.lineno(1)

def p_eof(p):
    '''eof_func : EOF channel'''
    p[0] = EofFunc(channel = p[2])
    p[0].lineNum = p.lineno(1)

def p_err_func(p):
    '''err_func : ERR %prec FUNCTION'''
    p[0] = ErrFunc()
    p[0].lineNum = p.lineno(1)

def p_exp_func(p):
    '''exp_func : EXP factor %prec FUNCTION'''
    p[0] = ExpFunc(factor = p[2])
    p[0].lineNum = p.lineno(1)

def p_false_func(p):
    '''false_func : FALSE'''
    p[0] = FalseFunc()
    p[0].lineNum = p.lineno(1)

def p_get_func(p):
    '''get_func : GET %prec FUNCTION'''
    p[0] = GetFunc()
    p[0].lineNum = p.lineno(1)

def p_get_str_func(p):
    '''get_str_func : GET_STR %prec FUNCTION'''
    p[0] = GetStrFunc()
    p[0].lineNum = p.lineno(1)

def p_get_str_file_func(p):
    '''get_str_file_func : GET_STR channel %prec FUNCTION'''
    p[0] = GetStrFileFunc(channel = p[2])
    p[0].lineNum = p.lineno(1)

def p_inkey_func(p):
    '''inkey_func : INKEY factor %prec FUNCTION'''
    #if factor 0<= then wait for any key and return keycode
    #if factor 0>  then return true or false on that keycode
    #if factor = -256 return a number for OS version
    p[0] = InkeyFunc(factor = p[2])
    p[0].lineNum = p.lineno(1)

def p_inkey_str_func(p):
    '''inkey_str_func : INKEY_STR factor %prec FUNCTION'''
    p[0] = InkeyStrFunc(factor = p[2])
    p[0].lineNum = p.lineno(1)

def p_instr_func(p):
    '''instr_func : INSTR_LPAREN expr COMMA expr RPAREN
                  | INSTR_LPAREN expr COMMA expr COMMA expr RPAREN'''
    if len(p) == 6:
        #INSTR expr COMMA expr
        p[0] = InstrFunc(source = p[2], subString = p[4] )
    elif len(p) == 8:
        #INSTR expr COMMA expr COMMA expr
        p[0] = InstrFunc(source = p[2], subString = p[4], startPosition = p[6] )
    p[0].lineNum = p.lineno(1)

def p_int_func(p):
    '''int_func : INT factor %prec FUNCTION'''
    p[0] = IntFunc(factor = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_left_str_func(p):
    '''left_str_func : LEFT_STR_LPAREN expr RPAREN
                     | LEFT_STR_LPAREN expr COMMA expr RPAREN'''
    if len(p) == 4:
        p[0] = LeftStrFunc(source = p[2])
    elif len(p) == 6:
        p[0] = LeftStrFunc(source = p[2], length = p[4])
    p[0].lineNum = p.lineno(1)

def p_len_func(p):
    '''len_func : LEN factor %prec FUNCTION'''
    p[0] = LenFunc(factor = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_ln_func(p):
    '''ln_func : LN factor %prec FUNCTION'''
    p[0] = LnFunc(factpr = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_log_func(p):
    '''log_func : LOG factor %prec FUNCTION'''
    p[0] = LogFunc(factor = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_mid_str_func(p):       # note for rob - is this missing %prec FUNCTION
    '''mid_str_func : MID_STR_LPAREN expr COMMA expr RPAREN
                    | MID_STR_LPAREN expr COMMA expr COMMA expr RPAREN'''
    if len(p) == 6:
        p[0] = MidStrFunc(source = p[2], position = p[4])
    elif len(p) == 8:
        p[0] = MidStrFunc(source = p[2], position = p[4], length = p[6])
    p[0].lineNum = p.lineno(1)
    
def p_mod_func(p):
    'mod_func : MOD array %prec FUNCTION'
    p[0] = ArrayRootMeanSquare(p[2])
    p[0].lineNum = p.lineno(1)
    
def p_mode_func(p):
    '''mode_func : MODE %prec FUNCTION'''
    p[0] = ModeFunc()
    p[0].lineNum = p.lineno(1)
    
def p_not_func(p):
    'not_func : NOT factor %prec FUNCTION'
    p[0] = Not(factor = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_openin_func(p):
    '''openin_func : OPENIN factor %prec FUNCTION'''
    p[0] = OpeninFunc(filename = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_openout_func(p):
    '''openout_func : OPENOUT factor %prec FUNCTION'''
    p[0] = OpenoutFunc(filename = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_openup_func(p):
    '''openup_func : OPENUP factor %prec FUNCTION'''
    p[0] = OpenupFunc(filename = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_pos_func(p):
    '''pos_func : POS %prec FUNCTION'''
    p[0] = PosFunc()
    p[0].lineNum = p.lineno(1)
    
def p_pi_func(p):
    '''pi_func : PI %prec FUNCTION'''
    p[0] = PiFunc()
    p[0].lineNum = p.lineno(1)
    
def p_point_func(p):
    '''point_func : POINT_LPAREN expr COMMA expr RPAREN %prec FUNCTION'''
    p[0] = PointFunc(xCoord = p[2] , yCoord = p[4])
    p[0].lineNum = p.lineno(1)
    
def p_rad_func(p):
    'rad_func : RAD factor %prec FUNCTION'
    p[0] = RadFunc(factor = p[2])
    p[0].lineNum = p.lineno(1)

def p_right_str_func(p):
    '''right_str_func : RIGHT_STR_LPAREN expr RPAREN
                      | RIGHT_STR_LPAREN expr COMMA expr RPAREN'''
    if len(p) == 4:
        p[0] = RightStrFunc(source = p[2])
    elif len(p) == 6:
        p[0] = RightStrFunc(source = p[2], length = p[4])
    p[0].lineNum = p.lineno(1)
    
def p_rnd_func(p):
    '''rnd_func : RND %prec FUNCTION
                | RND_LPAREN expr RPAREN %prec FUNCTION'''
    if len(p) == 2:
        #RND
        p[0] = RndFunc(option=None)
    elif len(p) == 4:
        #RND expression
        p[0] = RndFunc(option = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_sin_func(p):
    'sin_func : SIN factor %prec FUNCTION'
    p[0] = SinFunc(factor = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_sgn_func(p):
    'sgn_func : SGN factor %prec FUNCTION'
    p[0] = SgnFunc(factor = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_sqr_func(p):
    'sqr_func : SQR factor %prec FUNCTION'
    p[0] = SqrFunc(factor = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_str_str_func(p):
    '''str_str_func : str_str_dec_func
                    | str_str_hex_func'''
    p[0] = p[1]
    p[0].lineNum = p.lineno(1)
    
def p_str_str_dec_func(p):
    'str_str_dec_func : STR_STR expr %prec FUNCTION'
    p[0] = StrStringFunc(factor = p[2], base = 10)
    p[0].lineNum = p.lineno(1)
    
def p_str_str_hex_func(p):
    'str_str_hex_func : STR_STR TILDE expr %prec FUNCTION'
    p[0] = StrStringFunc(factor = p[2], base = 16)
    p[0].lineNum = p.lineno(1)
    
def p_sum_func(p):
    'sum_func : SUM array %prec FUNCTION'
    p[0] = Sum(array = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_sumlen_func(p):
    'sumlen_func : SUMLEN array %prec FUNCTION'
    p[0] = SumLenFunc(array = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_tan_func(p):
    'tan_func : TAN factor %prec FUNCTION'
    p[0] = TanFunc(factor = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_tempo_func(p):
    '''tempo_func : TEMPO %prec FUNCTION'''
    p[0] = TempoFunc()
    p[0].lineNum = p.lineno(1)
    
def p_tint_func(p):
    # TODO: The first of these is a statement
    '''tint_func : TINT LPAREN expr COMMA expr RPAREN %prec FUNCTION'''
    #TINT ( x, y )
    p[0] = TintFunc(xCoord = p[3] ,yCoord = p[5])
    p[0].lineNum = p.lineno(1)
    
def p_top_func(p):
    '''top_func : TOP'''
    p[0] = TopFunc()
    p[0].lineNum = p.lineno(1)
    
def p_true_func(p):
    '''true_func : TRUE'''
    p[0] = TrueFunc()
    p[0].lineNum = p.lineno(1)
    
def p_val_func(p):
    '''val_func : VAL expr %prec FUNCTION'''
    p[0] = ValFunc(factor = p[2])
    p[0].lineNum = p.lineno(1)
    
def p_vpos_func(p):
    '''vpos_func : VPOS %prec FUNCTION'''
    p[0] = VposFunc()
    p[0].lineNum = p.lineno(1)
    
def p_width_func(p):
    'width_func : WIDTH %prec FUNCTION'
    p[0] = WidthFunc()
    p[0].lineNum = p.lineno(1)
    
#=============================================================================#
# CHANNEL
#

# Channels
def p_channel(p):
    '''channel : HASH factor %prec UHASH'''
    p[0] = Channel(channel = p[2])
    p[0].lineNum = p.lineno(1)
    

#=============================================================================#
# VARIABLE

def p_variable(p):
    'variable : ID'
    p[0] = Variable(identifier = p[1])
    p[0].lineNum = p.lineno(1)

def p_variable_list(p):
    '''variable_list : variable
                     | variable_list COMMA variable'''
    if len(p) == 2:
        p[0] = VariableList()
        p[0].append(p[1])
    elif len(p) == 4:
        p[1].append(p[3])
        p[0] = p[1]
    
def p_nullable_variable(p):
    '''nullable_variable : variable
                         | empty'''
    p[0] = p[1]
    
def p_nullable_variable_list(p):
    '''nullable_variable_list : nullable_variable
                              | nullable_variable_list COMMA nullable_variable'''
    if len(p) == 2:
        p[0] = VariableList()
        p[0].append(p[1])
    elif len(p) == 4:
        p[1].append(p[3])
        p[0] = p[1]

def p_nullable_writable(p):
    '''nullable_writable : writable
                         | empty'''
    p[0] = p[1]
    
def p_nullable_writable_list(p):
    '''nullable_writable_list : nullable_writable
                              | nullable_writable_list COMMA nullable_writable'''
    if len(p) == 2:
        p[0] = WritableList()
        p[0].append(p[1])
    elif len(p) == 4:
        p[1].append(p[3])
        p[0] = p[1]    
#=============================================================================#
# ARRAYS

# Array support
def p_array(p):
    'array : ARRAYID_LPAREN RPAREN'
    p[0] = Array(identifier = p[1])
    p[0].lineNum = p.lineno(1)
    
def p_indexer(p):
    'indexer : ARRAYID_LPAREN expr_list RPAREN'
    p[0] = Indexer(identifier = p[1], indices = p[2])
    p[0].lineNum = p.lineno(1)
    
# TODO: Is PLUS array for unary plus allowed?
def p_array_expr(p):
    # TODO factor here should be factor COMMA expr_list
    '''array_expr : array
                  | factor
                  | expr_list
                  | MINUS array
                  | array PLUS array
                  | array MINUS array
                  | array TIMES array
                  | array DIVIDE array
                  | array PLUS factor
                  | factor PLUS array
                  | array MINUS factor
                  | factor MINUS array
                  | array TIMES factor
                  | factor TIMES array
                  | array DIVIDE factor
                  | factor DIVIDE array
                  | array DOT array'''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        if p[1] == '-':
            p[0] = ArrayUnaryMinus(expression = p[2])
        p[0].lineNum = p.lineno(1)
    elif len(p) == 4:
        if p[2] == '+':
            p[0] = ArrayPlus(lhs = p[1], rhs = p[3])
        elif p[2] == '-':
            p[0] = ArrayMinus(lhs = p[1], rhs = p[3])
        elif p[2] == '*':
            p[0] = ArrayMultiply(lhs = p[1], rhs = p[3])
        elif p[2] == '/':
            p[0] = ArrayDivide(lhs = p[1], rhs = p[3])
        elif p[2] == '.':
            p[0] = MatrixMultiply(lhs = p[1], rhs = p[3])
        p[0].lineNum = p.lineno(2)
    
#=============================================================================#
# LITERALS

def p_literal(p):
    '''literal : literal_string
               | literal_integer
               | literal_float'''
    p[0] = p[1]

def p_literal_string(p):
    'literal_string : LITERAL_STRING'
    p[0] = LiteralString(value = p[1])
    p[0].lineNum = p.lineno(1)

def p_literal_integer(p):
    'literal_integer : LITERAL_INTEGER'
    p[0] = LiteralInteger(value = p[1])
    p[0].lineNum = p.lineno(1)

def p_literal_float(p):
    'literal_float : LITERAL_FLOAT'
    p[0] = LiteralFloat(value = p[1])
    p[0].lineNum = p.lineno(1)

#=============================================================================#
# EMPTY PRODUCTION

def p_empty(p):
    'empty :'
    p[0] = None

#=============================================================================#
# ERRORS

# Error rule for syntax errors
def p_error(p):
    logging.error("Syntax error %s at physical line %s", p, p.lineno)
