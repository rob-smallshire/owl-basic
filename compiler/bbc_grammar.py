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
             ('nonassoc', 'EQ' 'NE', 'LTE', 'GTE', 'LT', 'GT', 'SHIFT_LEFT', 'SHIFT_RIGHT', 'SHIFT_RIGHT_UNSIGNED'),
             ('left', 'PLUS', 'MINUS'),
             ('left', 'TIMES', 'DIVIDE', 'MOD', 'DIV'),
             ('left', 'CARET'),
             ('left', 'PLING', 'QUERY'),  # Binary indirection operators
             ('right', 'FUNCTION', 'NOT', 'UPLUS', 'UMINUS', 'UPLING', 'UQUERY', 'UPIPE', 'UDOLLAR', 'UHASH'), # Unary operators
             )

def p_program(p):
    'program : statement_list'
    p[0] = Program(p[1])
    logging.debug("p[0] = %s", p[0])

# TODO: Distinguish single-line compound statements

def p_statement_list(p):
    '''statement_list : statement
                      | statement_list statement'''
    if len(p) == 2:
        p[0] = StatementList(p[1])
    elif len(p) == 3:
        p[1].append(p[2])
        p[0] = p[1]
    logging.debug("p[0] = %s", p[0])

def p_statement(p):
    '''statement : any_stmt_body stmt_terminator
                 | compound_statement stmt_terminator'''
    p[0] = p[1]
    logging.debug("p[0] = %s", p[0])

# TODO: Need to separate statements which can be used within
#       compound statements, from statemenst which can
#       only be used on their own line (e.g. CASE x OF or WHEN)

# A single line statement list - use in single-line IF THEN ELSE oonstruct
# TODO: May need concept of an empty statement to deal with trailing colons
def p_compound_statement(p):
    '''compound_statement : stmt_body
                          | compound_statement statement_separator stmt_body'''
    if len(p) == 2:
        p[0] = StatementList(p[1])
    elif len(p) == 4:
        p[1].append(p[3])
        p[0] = p[1]
    logging.debug("p[0] = %s", p[0])

def p_statement_separator(p):
    'statement_separator : COLON'
    p[0] = p[1]
    logging.debug("p[0] = %s", p[0])

def p_stmt_terminator(p):
    'stmt_terminator : EOL'
    p[0] = p[1]
    logging.debug("p[0] = %s", p[0])

#=============================================================================#
# STATEMENTS

# TODO: Statements to be implemented
    '''stmt_body : chain_stmt
                 | dim_stmt
                 | input_stmt
                 | line_stmt
                 | local_stmt
                 | on_error_stmt
                 | read_stmt
                 | restore_stmt    PAGE 69 BBCBASIC.PDF - RESTORE +offset???
                 | tint_stmt
                 | trace_stmt'''

# All statements
def p_any_stmt_body(p):
    '''any_stmt_body : stmt_body
                     | lone_stmt_body'''
    p[0] = p[1]
    logging.debug("p[0] = %s", p[0])

# Statements which must appear alone on
# their own line
def p_lone_stmt_body(p):
    '''lone_stmt_body : case_stmt'''
    p[0] = p[1]
    logging.debug("p[0] = %s", p[0])

# Statements which can appear alone,
# or in compound statements on one line
def p_stmt_body(p):
    '''stmt_body : empty_stmt
                 | beats_stmt
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
                 | gosub_stmt
                 | install_stmt
                 | if_stmt
                 | for_stmt
                 | library_stmt
                 | let_stmt
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
                 | rectangle_stmt
                 | repeat_stmt
                 | report_stmt
                 | return_stmt
                 | sound_stmt
                 | stop_stmt
                 | stereo_stmt
                 | swap_stmt
                 | sys_stmt
                 | tempo_stmt
                 | until_stmt
                 | vdu_stmt
                 | voices_stmt
                 | while_stmt
                 | width_stmt
                 | wait_stmt
                 | endwhile_stmt'''
    if p[1]:
        p[0] = Statement(p[1])
        logging.debug("p[0] = %s", p[0])

# Empty statement
def p_empty_stmt(p):
    '''empty_stmt :'''
    pass

# BPUT statement
def p_bput_stmt(p):
    '''bput_stmt : BPUT channel COMMA expr
                 | BPUT channel COMMA expr SEMICOLON'''
    if len(p) == 5:
        p[0] = Bput(p[2], p[4], newline=True)
    elif len(p) == 6:
        p[0] = Bput(p[2], p[4], newline=False)
    logging.debug("p[0] = %s", p[0])

# CALL statement
def p_call_stmt(p):
    '''call_stmt : CALL expr
                 | CALL expr COMMA variable_list'''
    if len(p) == 3:
        p[0] = Call(p[2])
    elif len(p) == 5:
        p[0] = Call(p[2], p[4])
    logging.debug("p[0] = %s", p[0])

# TODO CASE stmt
# Not that WHEN clauses which follow the OTHERWISE clause
# a legal, but cannot be executed.
# TODO : Put this into a special class of statements which
# must begin on a new line.
def p_case_stmt(p):
    '''case_stmt : CASE expr OF stmt_terminator when_clause_list ENDCASE'''
    p[0] = Case(p[2], p[5])
    logging.debug("p[0] = %s", p[0])

def p_when_clause_list(p):
    '''when_clause_list : when_clause
                        | when_clause_list when_clause'''
    if len(p) == 2:
        p[0] = WhenClauseList(p[1])
    elif len(p) == 3:
        print "p2 = %s" % p[2]
        p[1].append(p[2])
        p[0] = p[1]
    logging.debug("p[0] = %s", p[0])

def p_when_clause(p):
    '''when_clause : WHEN expr_list COLON statement_list
                   | OTHERWISE statement_list'''
    if len(p) == 5:
        p[0] = WhenClause(p[2], p[4])
    elif len(p) == 3:
        p[0] = OtherwiseClause(p[2])
    logging.debug("p[0] = %s", p[0])

# TODO CHAIN stmt
def p_beats_stmt(p):
    '''beats_stmt : BEATS expr'''
    p[0] = Beats(p[2])
    logging.debug("p[0] = %s", p[0])

# CIRCLE stmt
def p_circle_stmt(p):
    '''circle_stmt : CIRCLE expr COMMA expr COMMA expr
                   | CIRCLE FILL expr COMMA expr COMMA expr'''
    if len(p) == 7:
        p[0] = Circle(p[2], p[4], p[6])
    elif len(p) == 8:
        p[0] = Circle(p[3], p[5], p[7], fill=True)
    logging.debug("p[0] = %s", p[0])

# CLEAR
def p_clear_stmt(p):
    'clear_stmt : CLEAR'
    p[0] = Clear()
    logging.debug("p[0] = %s", p[0])

# CLOSE
def p_close_stmt(p):
    'close_stmt : CLOSE channel'
    p[0] = Close(p[2])
    logging.debug("p[0] = %s", p[0])

# CLG
def p_clg_stmt(p):
    'clg_stmt : CLG'
    p[0] = Clg()
    logging.debug("p[0] = %s", p[0])

# CLS
def p_cls_stmt(p):
    'cls_stmt : CLS'
    p[0] = Cls()
    logging.debug("p[0] = %s", p[0])

# COLOUR
def p_colour_stmt(p):
    '''colour_stmt : COLOUR expr
                   | COLOUR expr COMMA expr
                   | COLOUR expr TINT expr
                   | COLOUR expr COMMA expr COMMA expr COMMA expr'''
#                   | COLOUR expr TINT expr
    if len(p) == 3:
        p[0] = Colour(p[2])
    elif len(p) == 5:
        if p[3] == "TINT":
            p[0] = Colour(p[2], p[4])
        else:
            p[0] = Palette(logical = p[2], physical = p[4])
    elif len(p) == 9:
        p[0] = Palette(logical = p[2], red = p[4], green = p[6], blue = p[8])
    logging.debug("p[0] = %s", p[0])

# DATA
def p_data_statement(p):
    'data_stmt : DATA'
    p[0] = Data(p[1])
    logging.debug("p[0] = %s", p[0])

def p_def_stmt(p):
    '''def_stmt : def_fn_stmt
                | def_proc_stmt'''
    p[0] = p[1]
    logging.debug("p[0] = %s", p[0])

# The statement list needs to be modified so there can be more
# than one point of return form functions
def p_def_fn_stmt(p):
    '''def_fn_stmt : DEF FN_ID compound_statement
                   | DEF FN_ID LPAREN formal_arg_list RPAREN compound_statement'''
    if len(p) == 4:
        p[3].prepend(DefineFunction(p[2]))
        p[0] = p[3]
    elif len(p) == 7:
        p[6].prepend(DefineFunction(p[2], p[4]))
        p[0] = p[6]
    logging.debug("p[0] = %s", p[0])

def p_end_fn_stmt(p):
    '''end_fn_stmt : EQ expr %prec UEQUAL'''
    p[0] = ReturnFromFunction(p[2])
    logging.debug("p[0] = %s", p[0])

def p_def_proc_stmt(p):
    '''def_proc_stmt : DEF PROC_ID
                     | DEF PROC_ID LPAREN formal_arg_list RPAREN'''
    if len(p) == 3:
        p[0] = DefineProcedure(p[2])
    elif len(p) == 6:
        p[0] = DefineProcedure(p[2], p[4])
    logging.debug("p[0] = %s", p[0])

def p_endproc_stmt(p):
    '''endproc_stmt : ENDPROC'''
    p[0] = ReturnFromProcedure()
    logging.debug("p[0] = %s", p[0])

def p_proc_stmt(p):
    '''proc_stmt : PROC_ID
                 | PROC_ID LPAREN actual_arg_list RPAREN'''
    if len(p) == 2:
        #PROC id
        p[0] = CallProcedure(p[1])
    elif len(p) == 5:
        #PROC id (parameter-list)
        p[0] = CallProcedure(p[1], p[3])
    logging.debug("p[0] = %s", p[0])

# DRAW statements
def p_draw_stmt(p):
    '''draw_stmt : DRAW expr COMMA expr
                 | DRAW BY expr COMMA expr'''
    if len(p) == 5:
        p[0] = Draw(p[2], p[4])
    elif len(p) == 6:
        p[0] = Draw(p[3], p[5], True)
    logging.debug("p[0] = %s", p[0])

# END statement
def p_end_stmt(p):
    '''end_stmt : END'''
    p[0] = End()
    logging.debug("p[0] = %s", p[0])

def p_ellipse_stmt(p): # BBC BASIC V also supports rotation of an ellipse
    '''ellipse_stmt : ELLIPSE expr COMMA expr COMMA expr COMMA expr
                    | ELLIPSE FILL expr COMMA expr COMMA expr COMMA expr
                    | ELLIPSE expr COMMA expr COMMA expr COMMA expr COMMA expr
                    | ELLIPSE FILL expr COMMA expr COMMA expr COMMA expr COMMA expr'''

    if len(p) == 9:
        p[0] = Ellipse(p[2], p[4], p[6], p[8])
    elif len(p) == 10:
        p[0] = Ellipse(p[3], p[5], p[7], p[9],fill=True)
    elif len(p) == 11:
        p[0] = Ellipse(p[2], p[4], p[6], p[8], p[10])
    elif len(p) == 12:
        p[0] = Ellipse(p[3], p[5], p[7], p[9], p[11], fill=True)
    logging.debug("p[0] = %s", p[0])

def p_error_stmt(p):
    '''error_stmt : ERROR expr COMMA expr
                  | ERROR EXT expr COMMA expr'''
    # TODO: Needs to handle the EXT keyword for returning an external error code
    #       ERROR EXT ERR, REPORT$ : REM pass on the error
    if len(p) == 5:
        p[0] = GenerateError(p[2], p[4])
    elif len(p) == 6:
        p[0] = ReturnError(p[2], p[4])
    logging.debug("p[0] = %s", p[0])

def p_envelope_stmt(p):
    '''envelope_stmt : ENVELOPE expr COMMA expr COMMA expr COMMA expr COMMA expr COMMA expr COMMA expr COMMA expr COMMA expr COMMA expr COMMA expr COMMA expr COMMA expr COMMA expr'''
    p[0] = Envelope(p[2],p[4],p[6],p[8],p[10],p[12],p[14],p[16],p[18],p[20],p[22],p[24],p[26],p[28] )
    logging.debug("p[0] = %s", p[0])

def p_fill_stmt(p):
    '''fill_stmt : FILL expr COMMA expr
                 | FILL BY expr COMMA expr'''
    if len(p) == 5:
        p[0] = Fill(p[2], p[4])
    elif len(p) == 6:
        p[0] = Fill(p[3], p[5], True)
    logging.debug("p[0] = %s", p[0])

def p_gcol_stmt(p):
    '''gcol_stmt : GCOL expr
                 | GCOL expr COMMA expr'''
    if len(p) == 3:
        p[0] = Gcol(p[2])
    elif len(p) == 5:
        p[0] = Gcol(p[4], p[2])
    logging.debug("p[0] = %s", p[0])

def p_install_stmt(p):
    '''install_stmt : INSTALL expr'''
    if len(p) == 3:
        #INSTALL expression
        p[0] = Install(p[2])
    logging.debug("p[0] = %s", p[0])

# GOTO statement
def p_goto_stmt(p):
    '''goto_stmt : GOTO factor'''
    p[0] = Goto(p[2])
    logging.debug("p[0] = %s", p[0])

# GOSUB statement
def p_gosub(p):
    '''gosub_stmt : GOSUB factor'''
    p[0] = Gosub(p[2])
    logging.debug("p[0] = %s", p[0])

def p_return_stmt(p):
    '''return_stmt : RETURN
                   | RETURN variable
                   | RETURN array'''
    if len(p) == 2:
        #RETURN
        p[0] = Return()
    elif len(p) == 3: # used in DEF PROC/FN to return params (not sure if it is needed here)
        #RETURN variable
        #RETURN array
        p[0] = Return(p[2])
    logging.debug("p[0] = %s", p[0])

# IF statements
def p_if_stmt(p):
    '''if_stmt : if_single_stmt
               | if_multi_stmt'''
    p[0] = p[1]
    logging.debug("p[0] = %s", p[0])

def p_if_single_stmt(p):
    '''if_single_stmt : IF expr clause
                      | IF expr THEN clause
                      | IF expr clause ELSE clause
                      | IF expr THEN clause ELSE clause'''
    if len(p) == 4:
        p[0] = If(p[2], p[3])
    elif len(p) == 5:
        p[0] = If(p[2], p[4])
    elif len(p) == 6:
        p[0] = If(p[2], p[3], p[5])
    elif len(p) == 7:
        p[0] = If(p[2], p[4], p[6])
    logging.debug("p[0] = %s", p[0])

# The clause is only used with IF statements and
# possible ON statements when the result of an expression
# is interpreted as a line number to GOTO
def p_clause(p):
    '''clause : compound_statement
              | implicit_goto'''
    p[0] = p[1]
    logging.debug("p[0] = %s", p[0])

def p_implicit_goto(p):
    '''implicit_goto : factor'''
    p[0] = Goto(p[1])
    logging.debug("p[0] = %s", p[0])

def p_if_multi_stmt(p):
    '''if_multi_stmt : IF expr THEN statement_list ENDIF
                     | IF expr THEN statement_list ELSE statement_list ENDIF'''
    if len(p) == 6:
        p[0] = If(p[2], p[4])
    elif len(p) == 8:
        p[0] = If(p[2], p[4], p[6])
    logging.debug("p[0] = %s", p[0])

# The syntax ruls for FOR..NEXT loops are not implemented by the
# grammar owing to the fact that NEXT is treated as a statement,
# rather than as a loop terminator.  A later analysis of the parse
# tree will attempt to match each NEXT with its corresponding FOR
def p_for_stmt(p):
    '''for_stmt : FOR variable EQ expr TO expr
                | FOR variable EQ expr TO expr STEP expr'''
    if len(p) == 7:
        p[0] = ForToStep(p[2], p[4], p[6], LiteralInteger(1))
    elif len(p) == 9:
        p[0] = ForToStep(p[2], p[4], p[6], p[8])
    logging.debug("p[0] = %s", p[0])

# Rule for dealing with unmatched NEXT statements
def p_next_stmt(p):
    '''next_stmt : NEXT nullable_variable_list
                 | NEXT'''
    if len(p) == 3:
        p[0] = Next(p[2])
    elif len(p) == 2:
        p[0] = Next(None)
    logging.debug("p[0] = %s", p[0])

def p_library_stmt(p):
    '''library_stmt : LIBRARY expr'''
    p[0] = AddLibrary(p[2])

    logging.debug("p[0] = %s", p[0])

def p_let_stmt(p):
    '''let_stmt : assignment
                | increment
                | decrement'''
    p[0] = p[1]
    logging.debug("p[0] = %s", p[0])

def p_assignment(p):
    '''assignment : LET variable EQ expr
                  | LET array EQ array_expr
                  | LET indexer EQ expr
                  | lvalue EQ expr
                  | array EQ array_expr
                  | indexer EQ expr
                  | '''
    if len(p) == 5:
        p[0] = Assignment(p[2], p[4])
    elif len(p) == 4:
        p[0] = Assignment(p[1], p[3])
    logging.debug("p[0] = %s", p[0])

def p_increment(p):
    '''increment : LET variable PLUS_ASSIGN expr
                 | LET array PLUS_ASSIGN expr
                 | LET indexer PLUS_ASSIGN expr
                 | variable PLUS_ASSIGN expr
                 | array PLUS_ASSIGN expr
                 | indexer PLUS_ASSIGN expr'''
    if len(p) == 5:
        p[0] = Increment(p[2], p[4])
    elif len(p) == 4:
        p[0] = Increment(p[1], p[3])
    logging.debug("p[0] = %s", p[0])

def p_decrement(p):
    '''decrement : LET variable MINUS_ASSIGN expr
                 | LET array MINUS_ASSIGN expr
                 | LET indexer MINUS_ASSIGN expr
                 | variable MINUS_ASSIGN expr
                 | array MINUS_ASSIGN expr
                 | indexer MINUS_ASSIGN expr'''
    if len(p) == 5:
        p[0] = Decrement(p[2], p[4])
    elif len(p) == 4:
        p[0] = Decrement(p[1], p[3])
    logging.debug("p[0] = %s", p[0])

# MOVE statement
def p_move_stmt(p):
    '''move_stmt : MOVE expr COMMA expr
                 | MOVE BY expr COMMA expr'''
    if len(p) == 5:
        p[0] = Move(p[2], p[4])
    elif len(p) == 6:
        p[0] = Move(p[3], p[5], True)
    logging.debug("p[0] = %s", p[0])

def p_mode_stmt(p):
    '''mode_stmt : MODE expr'''
    p[0] = Mode(p[2])
    logging.debug("p[0] = %s", p[0])

def p_mouse_stmt(p):
    '''mouse_stmt : MOUSE variable COMMA variable COMMA variable
                  | MOUSE variable COMMA variable COMMA variable COMMA variable
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
            p[0] = MousePointer(pointer = 0) # default if not supplied =0
        elif len(p) == 4:
            #MOUSE ON expr
            p[0] = MousePointer(pointer = p[3])
    elif str(p[2]) == 'OFF':
        #MOUSE OFF
        p[0] = MousePointer(off = True)
    elif str(p[2]) == 'TO':
        #MOUSE TO
        p[0] = MousePointer(toX = p[3], toY = p[5])
    elif str(p[2]) == 'RECTANGLE':
        if len(p) == 10:
            #MOUSE RECTANGLE
            p[0] = MouseRectangle(p[3], p[5], p[7], p[9])
        elif len(p) == 4:
            #MOUSE RECTANGLE OFF
            p[0] = MouseRectangle(off=True)
    elif str(p[2]) == 'STEP':
        if len(p) == 4:
            #MOUSE STEP expr
            p[0] = MouseStep(p[3])
        if len(p) == 6:
            #MOUSE STEP expr COMMA expr
            p[0] = MouseStep(p[3], p[5])
    elif str(p[2]) == 'COLOUR':    #Not sure if i need to check for COLOR
        #MOUSE COLOUR expr COMMA expr COMMA expr COMMA expr
        p[0] = MouseColour(p[3], p[5], p[7], p[9])
    else:
        if len(p) == 7:
            #MOUSE variable COMMA variable COMMA variable
            p[0] = Mouse(p[2], p[4], p[6])
        elif len(p) == 9:
            #MOUSE variable COMMA variable COMMA variable COMMA variable
            p[0] = Mouse(p[2], p[4], p[6], p[8])
    logging.debug("p[0] = %s", p[0])

def p_on_stmt(p):
    '''on_stmt : ON'''
    p[0] = On()
    logging.debug("p[0] = %s", p[0])

def p_off_stmt(p):
    '''off_stmt : OFF'''
    p[0] = Off()
    logging.debug("p[0] = %s", p[0])

def p_origin_stmt(p):
    '''origin_stmt : ORIGIN expr COMMA expr'''
    p[0] = Origin(p[2], p[4])
    logging.debug("p[0] = %s", p[0])

def p_oscli_stmt(p):
    '''oscli_stmt : OSCLI expr'''
    p[0] = Oscli(p[2] )
    logging.debug("p[0] = %s", p[0])

def p_plot_stmt(p):
    '''plot_stmt : PLOT expr COMMA expr
                 | PLOT expr COMMA expr COMMA expr
                 | PLOT BY expr COMMA expr'''
    if len(p) == 5:
        #PLOT expr COMMA expr
        p[0] = Plot(p[2], p[4])
    elif len(p) == 6:
        #PLOT BY expr COMMA expr
        p[0] = Plot(p[3], p[5], relative=True)
    elif len(p) == 7:
        #PLOT expr COMMA expr COMMA expr
        p[0] = Plot(p[4], p[6], p[2])
    logging.debug("p[0] = %s", p[0])

def p_point_stmt(p):
    '''point_stmt : POINT expr COMMA expr
                  | POINT BY expr COMMA expr
                  | POINT TO expr COMMA expr'''
    if len(p) == 5:
        #POINT x COMMA y
        p[0] = Point(p[2] ,p[4] )
    elif len(p) == 6:
        #POINT BY x COMMA y
        #POINT TO x COMMA y
        p[0] = Point(p[3] ,p[5] ,p[2] )
    logging.debug("p[0] = %s", p[0])

def p_print_stmt(p):
    '''print_stmt : PRINT
                  | PRINT print_list
                  | PRINT channel COMMA actual_arg_list'''
    if len(p) == 2:
        p[0] = Print()
    elif len(p) == 3:
        p[0] = Print(p[2])
    elif len(p) == 4:
        p[0] = PrintFile(p[2], p[3])
    logging.debug("p[0] = %s", p[0])

def p_print_list(p):
    '''print_list : print_item
                  | print_list print_item'''
    if len(p) == 2:
        p[0] = PrintList(p[1])
    elif len(p) == 3:
        p[1].append(p[2])
        p[0] = p[1]
    logging.debug("p[0] = %s", p[0])

def p_print_item(p):
    '''print_item : expr
                  | tab
                  | spc
                  | print_manipulator'''
    p[0] = PrintItem(p[1])
    logging.debug("p[0] = %s", p[0])

def p_print_manipulator(p):
    '''print_manipulator : TILDE
                         | APOSTROPHE
                         | COMMA
                         | SEMICOLON'''
    p[0] = PrintManipulator(p[1])
    logging.debug("p[0] = %s", p[0])

def p_quit_stmt(p):
    '''quit_stmt : QUIT'''
    p[0] = Quit()
    logging.debug("p[0] = %s", p[0])

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

    if len(p) == 7:
        #RECTANGLE expr COMMA expr COMMA expr
        p[0] = Rectangle(p[2], p[4], p[6], None)
    elif len(p) == 9:
        #RECTANGLE expr COMMA expr COMMA expr COMMA expr
        p[0] = Rectangle(p[2], p[4], p[6], p[8])
    elif len(p) == 11:
        #RECTANGLE expr COMMA expr COMMA expr TO expr COMMA expr
        p[0] = Rectangle(p[2], p[4], p[6], None, p[8], p[10])
    elif len(p) == 13:
        #RECTANGLE expr COMMA expr COMMA expr COMMA expr TO expr COMMA expr
        p[0] = Rectangle(p[2], p[4], p[6], p[8], p[10], p[12])
    elif len(p) == 8:    #unsure if this is how to impliment this
        #RECTANGLE FILL expr COMMA expr COMMA expr
        p[0] = Rectangle(p[3], p[5], p[7], None, rectType = p[2])
    elif len(p) == 10:
        #RECTANGLE FILL expr COMMA expr COMMA expr COMMA expr
        p[0] = Rectangle(p[3], p[5], p[7], p[9], rectType = p[2])
    elif len(p) == 12:
        #RECTANGLE FILL expr COMMA expr COMMA expr TO expr COMMA expr
        #RECTANGLE SWAP expr COMMA expr COMMA expr TO expr COMMA expr
        p[0] = Rectangle(p[3], p[5], p[7], None, p[9], p[11], p[2])
    elif len(p) == 14:
        #RECTANGLE FILL expr COMMA expr COMMA expr COMMA expr TO expr COMMA expr
        #RECTANGLE SWAP expr COMMA expr COMMA expr COMMA expr TO expr COMMA expr
        p[0] = Rectangle(p[3], p[5], p[7], p[9], p[11], p[13], p[2])
    logging.debug("p[0] = %s", p[0])

def p_report_stmt(p):
    '''report_stmt : REPORT'''
    p[0] = Report()
    logging.debug("p[0] = %s", p[0])

def p_repeat_stmt(p):
    '''repeat_stmt : REPEAT compound_statement'''
    p[2].prepend(Repeat())
    p[0] = p[2]
    logging.debug("p[0] = %s", p[0])

def p_sound_stmt(p):
    '''sound_stmt : SOUND expr COMMA expr COMMA expr COMMA expr
                  | SOUND OFF'''
    if len(p) == 9:
        p[0] = Sound(p[2], p[4], p[6], p[8])
    elif len(p) == 3:
        p[0] = Sound(off=True)
    logging.debug("p[0] = %s", p[0])

def p_stereo_stmt(p):
    '''stereo_stmt : STEREO expr COMMA expr'''
    p[0] = Stereo(p[2] ,p[4] )
    logging.debug("p[0] = %s", p[0])

def p_swap_stmt(p):
    '''swap_stmt : SWAP variable COMMA variable
                 | SWAP array COMMA array'''
    #SWAP var1 COMMA var2
    #SWAP array1 COMMA array2
    p[0] = Swap(p[2] ,p[4] )
    logging.debug("p[0] = %s", p[0])

def p_sys_stmt(p):
    '''sys_stmt : SYS nullable_expr_list
                | SYS nullable_expr_list TO nullable_variable_list
                | SYS nullable_expr_list TO nullable_variable_list SEMICOLON variable'''
    if len(p) == 3:
        p[0] = Sys(p[2])
    elif len(p) == 5:
        p[0] = Sys(p[2], p[4])
    elif len(p) == 7:
        p[0] = Sys(p[2], p[4], p[6])
    logging.debug("p[0] = %s", p[0])
    
def p_tab(p):
    '''tab : TAB_LPAREN expr RPAREN
           | TAB_LPAREN expr COMMA expr RPAREN'''
    if len(p) == 4:
        p[0] = TabH(p[2])
    elif len(p) == 6:
        p[0] = TabXY(p[2], p[4])
    logging.debug("p[0] = %s", p[0])

def p_tempo_stmt(p):
    '''tempo_stmt : TEMPO expr'''
    if len(p) == 3:
        #TEMPO expression
        p[0] = Tempo(p[2] )
    logging.debug("p[0] = %s", p[0])

def p_stop_stmt(p):
    '''stop_stmt : STOP'''
    p[0] = Stop()
    logging.debug("p[0] = %s", p[0])

def p_spc(p):
    '''spc : SPC expr'''
    p[0] = Spc(p[2])
    logging.debug("p[0] = %s", p[0])

def p_until_stmt(p):
    '''until_stmt : UNTIL expr'''
    #UNTIL expression
    p[0] = Until(p[2] )
    logging.debug("p[0] = %s", p[0])

# VDU
def p_vdu_stmt(p):
    '''vdu_stmt : VDU
                | VDU vdu_list'''
    if len(p) == 2:
        p[0] = Vdu()
    elif len(p) == 3:
        p[0] = Vdu(p[2])
    logging.debug("p[0] = %s", p[0])

def p_vdu_list(p):
    '''vdu_list : vdu_item
                | vdu_list vdu_item'''
    if len(p) == 2:
        p[0] = VduList(p[1])
    elif len(p) == 3:
        p[1].append(p[2])
        p[0] = p[1]
    logging.debug("p[0] = %s", p[0])

def p_vdu_item(p):
    '''vdu_item : expr vdu_separator
                | expr'''
    if len(p) == 2:
        p[0] = VduItem(p[1])
    elif len(p) == 3:
        p[0] = VduItem(p[1], p[2])
    logging.debug("p[0] = %s", p[0])

def p_vdu_separator(p):
    '''vdu_separator : COMMA
                     | SEMICOLON
                     | PIPE'''
    p[0] = p[1]
    logging.debug("p[0] = %s", p[0])

def p_voices_stmt(p):
    '''voices_stmt : VOICES expr'''
    #VOICES expression
    p[0] = Voices(p[2] )
    logging.debug("p[0] = %s", p[0])

def p_while_stmt(p):
    '''while_stmt : WHILE expr'''
    p[0] = While(p[2] )
    logging.debug("p[0] = %s", p[0])

def p_endwhile_stmt(p):
    '''endwhile_stmt : ENDWHILE'''
    p[0] = Endwhile()
    logging.debug("p[0] = %s", p[0])

def p_width_stmt(p):
    '''width_stmt : WIDTH expr'''
    p[0] = Width(p[2] )
    logging.debug("p[0] = %s", p[0])

def p_wait_stmt(p):
    '''wait_stmt : WAIT
                 | WAIT expr'''
    if len(p) == 2:
        #WAIT
        p[0] = Wait()
    elif len(p) == 3:
        #WAIT expr
        p[0] = Wait(expr=p[2] )
    logging.debug("p[0] = %s", p[0])

#=============================================================================#
# ARGUMENTS
#

def p_actual_arg_list(p):
    '''actual_arg_list : actual_arg
                       | actual_arg_list COMMA actual_arg'''
    if len(p) == 2:
        p[0] = ActualArgList(p[1])
    if len(p) == 4:
        p[1].append(p[3])
        p[0] = p[1]
    logging.debug("p[0] = %s", p[0])

def p_actual_arg(p):
    '''actual_arg : expr
                  | array'''
    p[0] = p[1]
    logging.debug("p[0] = %s", p[0])

def p_formal_arg_list(p):
    '''formal_arg_list : formal_arg
                       | formal_arg_list COMMA formal_arg'''
    if len(p) == 2:
        p[0] = FormalArgList(p[1])
    if len(p) == 4:
        p[1].append(p[3])
        p[0] = p[1]
    logging.debug("p[0] = %s", p[0])

def p_formal_arg(p):
    '''formal_arg : variable
                  | array
                  | RETURN variable
                  | RETURN array'''
    if len(p) == 2:
        p[0] = FormalArgument(p[1])
    elif len(p) == 3:
        p[0] = FormalReferenceArgument(p[2])
    logging.debug("p[0] = %s", p[0])

#=============================================================================#
# FACTORS and EXPRESSIONS
#

def p_factor(p):
    '''factor : literal
              | variable
              | pseudovariable
              | expr_group
              | expr_function
              | indexer
              | QUERY expr %prec UQUERY
              | PLING expr %prec UPLING
              | PIPE expr %prec UPIPE
              | DOLLAR expr %prec UDOLLAR
              | PLUS expr %prec UPLUS
              | MINUS expr %prec UMINUS'''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        if p[1] == '+':
            p[0] = UnaryPlus(p[2])
        elif p[1] == '-':
            p[0] = UnaryMinus(p[2])
        elif p[1] == '?':
            p[0] = UnaryByteIndirection(p[2])
        elif p[1] == '!':
            p[0] = UnaryIntegerIndirection(p[2])
        elif p[1] == '$':
            p[0] = UnaryStringIndirection(p[2])
        elif p[1] == '|':
            p[0] = UnaryFloatIndirection(p[2])
    logging.debug("p[0] = %s", p[0])

def p_expr_list(p):
    '''expr_list : expr
                 | expr_list COMMA expr'''
    if len(p) == 2:
        p[0] = ExpressionList(p[1])
    elif len(p) == 4:
        p[1].append(p[3])
        p[0] = p[1]
    logging.debug("p[0] = %s", p[0])

def p_nullable_expr(p):
    '''nullable_expr : expr
                     | empty_expr'''
    p[0] = p[1]
    logging.debug("p[0] = %s", p[0])

def p_empty_expr(p):
    '''empty_expr :'''
    logging.debug("p[0] = %s", p[0])
    pass

def p_nullable_expr_list(p):
    '''nullable_expr_list : nullable_expr
                          | nullable_expr_list COMMA nullable_expr'''
    if len(p) == 2:
        p[0] = ExpressionList(p[1])
    elif len(p) == 4:
        p[1].append(p[3])
        p[0] = p[1]
    logging.debug("p[0] = %s", p[0])


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
            | expr QUERY expr
            | expr PLING expr'''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 4:
        if p[2] == '+':
            p[0] = Plus(p[1], p[3])
        elif p[2] == '-':
            p[0] = Minus(p[1], p[3])
        elif p[2] == '*':
            p[0] = Multiply(p[1], p[3])
        elif p[2] == '/':
            p[0] = Divide(p[1], p[3])
        elif p[2] == 'DIV':
            p[0] = IntegerDivide(p[1], p[3])
        elif p[2] == 'MOD':
            p[0] = IntegerModulus(p[1], p[3])
        elif p[2] == '^':
            p[0] = Power(p[1], p[3])
        elif p[2] == '=':
            p[0] = Equal(p[1], p[3])
        elif p[2] == '<>':
            p[0] = NotEqual(p[1], p[3])
        elif p[2] == '<':
            p[0] = LessThan(p[1], p[3])
        elif p[2] == '<=':
            p[0] = LessThanEqual(p[1], p[3])
        elif p[2] == '>':
            p[0] = GreaterThan(p[1], p[3])
        elif p[2] == '>=':
            p[0] = GreaterThanEqual(p[1], p[3])
        elif p[2] == '<<':
            p[0] = ShiftLeft(p[1], p[3])
        elif p[2] == '>>':
            p[0] = ShiftRight(p[1], p[3])
        elif p[2] == '>>>':
            p[0] = ShiftRightUnsigned(p[1], p[3])
        elif p[2] == '?':
            # TODO: Ideally we would want to require that the LHS
            #       of the dyadic indirection operators is a simple
            #       variable.  Doesn't work yet, though.
            p[0] = DyadicByteIndirection(p[1], p[3])
        elif p[2] == '!':
            p[0] = DyanicIntegerIndirection(p[1], p[3])
        elif p[2] == 'AND':
            p[0] = And(p[1], p[3])
        elif p[2] == 'OR':
            p[0] = Or(p[1], p[3])
        elif p[2] == 'EOR':
            p[0] = Eor(p[1], p[3])
    logging.debug("p[0] = %s", p[0])

def p_expr_group(p):
    'expr_group : LPAREN expr RPAREN'
    p[0] = p[2]
    logging.debug("p[0] = %s", p[0])

#=============================================================================#
# VALUES
#

# This contains all of the lvalues which can occur on the
# left-hand-side on an assignment operator (without the LET).
def p_lvalue(p):
    '''lvalue : variable
              | pseudovariable
              | mid_str_lvalue'''
    #         | right_str_lvalue
    #         | left_str_lvalue'''
    p[0] = p[1]
    logging.debug("p[0] = %s", p[0])

def p_mid_str_lvalue(p):
    '''mid_str_lvalue : MID_STR_LPAREN variable COMMA expr RPAREN
                      | MID_STR_LPAREN variable COMMA expr COMMA expr RPAREN'''
    if len(p) == 6:
        p[0] = MidStringValue(p[2], p[4])
    elif len(p) == 8:
        p[0] = MidStringValue(p[2], p[4], p[6])
    logging.debug("p[0] = %s", p[0])

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
    logging.debug("p[0] = %s", p[0])

# END is not officially a pseudovariable, although it can be used like one,
# although it may also be used as a statement
def p_end_value(p):
    'end_value : END'
    p[0] = EndValue()
    logging.debug("p[0] = %s", p[0])

def p_ext(p):
    '''ext_value : EXT channel'''
    p[0] = ExtValue(p[2])
    logging.debug("p[0] = %s", p[0])

def p_himem_value(p):
    'himem_value : HIMEM'
    p[0] = HimemValue()
    logging.debug("p[0] = %s", p[0])

def p_lomem_value(p):
    'lomem_value : LOMEM'
    p[0] = LomemValue()
    logging.debug("p[0] = %s", p[0])

def p_page_value(p):
    'page_value : PAGE'
    p[0] = PageValue()
    logging.debug("p[0] = %s", p[0])

def p_ptr_value(p):
    'ptr_value : PTR channel'
    p[0] = PtrValue(p[2])
    logging.debug("p[0] = %s", p[0])

def p_time_value(p):
    'time_value : TIME'
    p[0] = TimeValue()
    logging.debug("p[0] = %s", p[0])

def p_time_str_value(p):
    'time_str_value : TIME_STR'
    p[0] = TimeStrValue()
    logging.debug("p[0] = %s", p[0])

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
    '''expr_function : adval_func
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
                     | int_func
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
    logging.debug("p[0] = %s", p[0])

#def p_user_func(p):
#    'user_func : FN ID LPAREN actual_arg_list RPAREN %prec FUNCTION'
#    p[0] = UserFunc(p[2], p[3])

def p_abs_func(p):
    'abs_func : ABS factor %prec FUNCTION'
    p[0] = AbsFunc(p[2])
    logging.debug("p[0] = %s", p[0])

def p_acs_func(p):
    'acs_func : ACS factor %prec FUNCTION'
    p[0] = AcsFunc(p[2])
    logging.debug("p[0] = %s", p[0])

def p_adval_func(p):
    'adval_func : ADVAL factor %prec FUNCTION'
    p[0] = AdvalFunc(p[2])
    logging.debug("p[0] = %s", p[0])

def p_asn_func(p):
    'asn_func : ASN factor %prec FUNCTION'
    p[0] = AsnFunc(p[2])
    logging.debug("p[0] = %s", p[0])

def p_asc_func(p):
    'asc_func : ASC expr %prec FUNCTION'
    p[0] = AscFunc(p[2])
    logging.debug("p[0] = %s", p[0])

def p_atn_func(p):
    '''atn_func : ATN factor %prec FUNCTION'''
    p[0] = AtnFunc(p[2] )
    logging.debug("p[0] = %s", p[0])

def p_beat_func(p):
    'beat_func : BEAT %prec FUNCTION'
    p[0] = BeatFunc()
    logging.debug("p[0] = %s", p[0])

def p_beats_func(p):
    '''beats_func : BEATS %prec FUNCTION'''
    p[0] = BeatsFunc()
    logging.debug("p[0] = %s", p[0])

def p_bget_func(p):
    'bget_func : BGET channel %prec FUNCTION'
    p[0] = BgetFunc(p[2])
    logging.debug("p[0] = %s", p[0])

def p_chr_str_func(p):
    'chr_str_func : CHR_STR expr %prec FUNCTION'
    p[0] = ChrStrFunc(p[2])
    logging.debug("p[0] = %s", p[0])

def p_cos_func(p):
    'cos_func : COS expr %prec FUNCTION'
    p[0] = CosFunc(p[2])
    logging.debug("p[0] = %s", p[0])

def p_count_func(p):
    'count_func : COUNT %prec FUNCTION'
    p[0] = CountFunc(p[2])
    logging.debug("p[0] = %s", p[0])

def p_deg_func(p):
    'deg_func : DEG factor %prec FUNCTION'
    p[0] = DegFunc(p[2])
    logging.debug("p[0] = %s", p[0])

def p_dim_func(p):
    '''dim_func : DIM_LPAREN array RPAREN
                | DIM_LPAREN array COMMA expr RPAREN'''
    if len(p) == 4:
        p[0] = DimensionsFunc(p[2])
    elif len(p) == 6:
        p[0] = DimensionSizeFunc(p[2], p[4])
    logging.debug("p[0] = %s", p[0])

def p_erl_func(p):
    '''erl_func : ERL %prec FUNCTION'''
    p[0] = ErlFunc()
    logging.debug("p[0] = %s", p[0])

def p_eof(p):
    '''eof_func : EOF channel'''
    p[0] = EofFunc(p[2])
    logging.debug("p[0] = %s", p[0])

def p_err_func(p):
    '''err_func : ERR %prec FUNCTION'''
    p[0] = ErrFunc()
    logging.debug("p[0] = %s", p[0])

def p_exp_func(p):
    '''exp_func : EXP factor %prec FUNCTION'''
    p[0] = ExpFunc(p[2] )
    logging.debug("p[0] = %s", p[0])

def p_false_func(p):
    '''false_func : FALSE'''
    p[0] = FalseFunc()
    logging.debug("p[0] = %s", p[0])

def p_get_func(p):
    '''get_func : GET %prec FUNCTION'''
    p[0] = GetFunc()
    logging.debug("p[0] = %s", p[0])

def p_get_str_func(p):
    '''get_str_func : GET_STR %prec FUNCTION'''
    p[0] = Get_strFunc()
    logging.debug("p[0] = %s", p[0])

def p_get_str_file_func(p):
    '''get_str_file_func : GET_STR channel %prec FUNCTION'''
    p[0] = Get_strFileFunc(p[2])
    logging.debug("p[0] = %s", p[0])

def p_inkey_func(p):
    '''inkey_func : INKEY factor %prec FUNCTION'''
    #if factor 0<= then wait for any key and return keycode
    #if factor 0>  then return true or false on that keycode
    #if factor = -256 return a number for OS version
    p[0] = InkeyFunc(p[2] )
    logging.debug("p[0] = %s", p[0])

def p_inkey_str_func(p):
    '''inkey_str_func : INKEY_STR factor %prec FUNCTION'''
    p[0] = Inkey_strFunc(p[2] )
    logging.debug("p[0] = %s", p[0])

def p_int_func(p):
    '''int_func : INT factor %prec FUNCTION'''
    p[0] = IntFunc(p[2] )
    logging.debug("p[0] = %s", p[0])

def p_len_func(p):
    '''len_func : LEN factor %prec FUNCTION'''
    if len(p) == 3:
        #LEN factor
        p[0] = LenFunc(p[2] )
    logging.debug("p[0] = %s", p[0])

def p_ln_func(p):
    '''ln_func : LN factor %prec FUNCTION'''
    p[0] = LnFunc(p[2] )
    logging.debug("p[0] = %s", p[0])

def p_log_func(p):
    '''log_func : LOG factor %prec FUNCTION'''
    p[0] = LogFunc(p[2] )
    logging.debug("p[0] = %s", p[0])

def p_mid_str_func(p):       # note for rob - is this missing %prec FUNCTION
    '''mid_str_func : MID_STR_LPAREN expr COMMA expr RPAREN
                     | MID_STR_LPAREN expr COMMA expr COMMA expr RPAREN'''
    if len(p) == 6:
        p[0] = MidStringFunc(p[2], p[4])
    elif len(p) == 8:
        p[0] = MidStringFunc(p[2], p[4], p[6])
    logging.debug("p[0] = %s", p[0])

def p_mod_func(p):
    'mod_func : MOD array %prec FUNCTION'
    p[0] = ArrayRootMeanSquare(p[2])
    logging.debug("p[0] = %s", p[0])

def p_mode_func(p):
    '''mode_func : MODE %prec FUNCTION'''
    p[0] = ModeFunc()
    logging.debug("p[0] = %s", p[0])

def p_not_func(p):
    'not_func : NOT factor %prec FUNCTION'
    p[0] = Not(p[2])
    logging.debug("p[0] = %s", p[0])

def p_openin_func(p):
    '''openin_func : OPENIN factor %prec FUNCTION'''
    p[0] = OpeninFunc(p[2])
    logging.debug("p[0] = %s", p[0])

def p_openout_func(p):
    '''openout_func : OPENOUT factor %prec FUNCTION'''
    p[0] = OpenoutFunc(p[2])
    logging.debug("p[0] = %s", p[0])

def p_openup_func(p):
    '''openup_func : OPENUP factor %prec FUNCTION'''
    p[0] = OpenupFunc(p[2])
    logging.debug("p[0] = %s", p[0])

def p_pos_func(p):
    '''pos_func : POS %prec FUNCTION'''
    p[0] = PosFunc()
    logging.debug("p[0] = %s", p[0])

def p_pi_func(p):
    '''pi_func : PI %prec FUNCTION'''
    p[0] = PiFunc()
    logging.debug("p[0] = %s", p[0])

def p_point_func(p):
    '''point_func : POINT_LPAREN expr COMMA expr RPAREN %prec FUNCTION'''
    p[0] = PointFunc(p[2] ,p[4] )
    logging.debug("p[0] = %s", p[0])

def p_rad_func(p):
    'rad_func : RAD factor %prec FUNCTION'
    p[0] = RadFunc(p[2])
    logging.debug("p[0] = %s", p[0])

def p_rnd_func(p):
    '''rnd_func : RND %prec FUNCTION
                | RND expr %prec FUNCTION'''
    if len(p) == 2:
        #RND
        p[0] = RndFunc()
    elif len(p) == 3:
        #RND expression
        p[0] = RndFunc(expression=p[2] )
    logging.debug("p[0] = %s", p[0])

def p_sin_func(p):
    'sin_func : SIN factor %prec FUNCTION'
    p[0] = SinFunc(p[2])
    logging.debug("p[0] = %s", p[0])

def p_sgn_func(p):
    'sgn_func : SGN factor %prec FUNCTION'
    p[0] = SgnFunc(p[2])
    logging.debug("p[0] = %s", p[0])

def p_sqr_func(p):
    'sqr_func : SQR factor %prec FUNCTION'
    p[0] = SqrFunc(p[2])
    logging.debug("p[0] = %s", p[0])

def p_str_str_func(p):
    '''str_str_func : str_str_dec_func
                    | str_str_hex_func'''
    if len(p) == 3:
        p[0] = StrStringFunc(p[2])
    elif len(p) == 4:
        p[0] = StrStringFunc(p[3], 16) # Base 16 conversion
    logging.debug("p[0] = %s", p[0])

def p_str_str_dec_func(p):
    'str_str_dec_func : STR_STR expr %prec FUNCTION'
    p[0] = StrStringFunc(p[2], 10)
    logging.debug("p[0] = %s", p[0])

def p_str_str_hex_func(p):
    'str_str_hex_func : STR_STR TILDE expr %prec FUNCTION'
    p[0] = StrStringFunc(p[2], 16)
    logging.debug("p[0] = %s", p[0])

def p_sum_func(p):
    'sum_func : SUM array %prec FUNCTION'
    p[0] = ArraySum(p[2])
    logging.debug("p[0] = %s", p[0])

def p_sumlen_func(p):
    'sumlen_func : SUMLEN array %prec FUNCTION'
    p[0] = ArraySumLen(p[2])
    logging.debug("p[0] = %s", p[0])

def p_tan_func(p):
    'tan_func : TAN factor %prec FUNCTION'
    p[0] = TanFunc(p[2])
    logging.debug("p[0] = %s", p[0])

def p_tempo_func(p):
    '''tempo_func : TEMPO %prec FUNCTION'''
    p[0] = TempoFunc()
    logging.debug("p[0] = %s", p[0])

def p_tint_func(p):
    '''tint_func : TINT expr COMMA expr %prec FUNCTION
                 | TINT LPAREN expr COMMA expr RPAREN %prec FUNCTION'''
    if len(p) == 5:
        #TINT layer COMMA tint
        p[0] = TintFunc(layer=p[2] ,tint=p[4] )
    elif len(p) == 7:
        #TINT ( x COMMA y )
        p[0] = TintFunc(x=p[3] ,y=p[5] )
    logging.debug("p[0] = %s", p[0])

def p_top_func(p):
    '''top_func : TOP'''
    p[0] = TopFunc()
    logging.debug("p[0] = %s", p[0])

def p_true_func(p):
    '''true_func : TRUE'''
    p[0] = TrueFunc()
    logging.debug("p[0] = %s", p[0])

def p_val_func(p):
    '''val_func : VAL expr %prec FUNCTION'''
    p[0] = ValFunc(p[2] )
    logging.debug("p[0] = %s", p[0])

def p_vpos_func(p):
    '''vpos_func : VPOS %prec FUNCTION'''
    p[0] = VposFunc()
    logging.debug("p[0] = %s", p[0])

def p_width_func(p):
    'width_func : WIDTH %prec FUNCTION'
    p[0] = WidthFunc()
    logging.debug("p[0] = %s", p[0])

#=============================================================================#
# CHANNEL
#

# Channels
def p_channel(p):
    '''channel : HASH factor %prec UHASH'''
    p[0] = Channel(p[2])
    logging.debug("p[0] = %s", p[0])

#=============================================================================#
# VARIABLE

def p_variable(p):
    'variable : ID'
    p[0] = Variable(p[1])
    logging.debug("p[0] = %s [%s]", p[0], str(p[1]))

def p_variable_list(p):
    '''variable_list : variable
                     | variable_list COMMA variable'''
    if len(p) == 2:
        p[0] = VariableList(p[1])
    elif len(p) == 4:
        p[1].append(p[3])
        p[0] = p[1]
    logging.debug("p[0] = %s", p[0])

def p_empty_variable(p):
    '''empty_variable :'''
    logging.debug("p[0] = %s", p[0])
    pass

def p_nullable_variable(p):
    '''nullable_variable : variable
                         | empty_variable'''
    p[0] = p[1]
    logging.debug("p[0] = %s", p[0])

def p_nullable_variable_list(p):
    '''nullable_variable_list : nullable_variable
                              | nullable_variable_list COMMA nullable_variable'''
    if len(p) == 2:
        p[0] = VariableList(p[1])
    elif len(p) == 4:
        p[1].append(p[3])
        p[0] = p[1]
    logging.debug("p[0] = %s", p[0])


#=============================================================================#
# ARRAYS

# Array support
def p_array(p):
    'array : ARRAYID_LPAREN RPAREN'
    p[0] = Array(p[1])
    logging.debug("p[0] = %s", p[0])

def p_array_indexer(p):
    'indexer : ARRAYID_LPAREN expr_list RPAREN'
    p[0] = Indexer(p[1], p[2])
    logging.debug("p[0] = %s", p[0])

# TODO: Is PLUS array for unary plus allowed?
def p_array_expr(p):
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
                  | array DOT array
                  | '''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        if p[1] == '-':
            p[0] = UnaryMinus(p[2])
    elif len(p) == 4:
        if p[2] == '+':
            p[0] = Plus(p[1], p[3])
        elif p[2] == '-':
            p[0] = Minus(p[1], p[3])
        elif p[2] == '*':
            p[0] = Multiply(p[1], p[3])
        elif p[2] == '/':
            p[0] = Divide(p[1], p[3])
        elif p[2] == '.':
            p[0] = MatrixMultiply(p[1], p[3])
    logging.debug("p[0] = %s", p[0])

#=============================================================================#
# LITERALS

def p_literal(p):
    '''literal : literal_string
               | literal_integer
               | literal_float'''
    p[0] = p[1]
    logging.debug("p[0] = %s [%s]", p[0], p[1])

def p_literal_string(p):
    'literal_string : LITERAL_STRING'
    p[0] = LiteralString(p[1])

def p_literal_integer(p):
    'literal_integer : LITERAL_INTEGER'
    p[0] = LiteralInteger(p[1])

def p_literal_float(p):
    'literal_float : LITERAL_FLOAT'
    p[0] = LiteralFloat(p[1])

#=============================================================================#
# ERRORS

# Error rule for syntax errors
def p_error(p):
    logging.error("Syntax error %s at physical line %s", p, p.lineno)
