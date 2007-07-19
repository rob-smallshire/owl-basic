import ply.yacc as yacc

# Get the token map from the lexer.  This is required.
from bbc_lexer import tokens
from bbc_ast import *

# Precedence table for the above operators
precedence = (
             ('left', 'EOR', 'OR'),
             ('left', 'AND'),
             ('nonassoc', 'EQ' 'NE', 'LTE', 'GTE', 'LT', 'GT', 'SHIFT_LEFT', 'SHIFT_RIGHT', 'SHIFT_RIGHT_UNSIGNED'),
             ('left', 'PLUS', 'MINUS'),
             ('left', 'TIMES', 'DIVIDE', 'MOD', 'DIV'),
             ('left', 'CARET'),
             ('left', 'PLING', 'QUERY', 'PIPE', 'DOLLAR'),  # Binary indirection operators
             ('right', 'FUNCTION', 'NOT', 'UPLUS', 'UMINUS', 'UPLING', 'UQUERY', 'UPIPE', 'UDOLLAR', 'UHASH'), # Unary operators
             )

def p_program(p):
    'program : statement_list'
    p[0] = Program(p[1])

# TODO: Distinguish single-line compound statements
    
def p_statement_list(p): 
    '''statement_list : statement
                      | statement_list statement'''
    if len(p) == 2:
        p[0] = StatementList(p[1])
    elif len(p) == 3:
        p[1].append(p[2])
        p[0] = p[1]

def p_statement(p):
    '''statement : any_stmt_body stmt_terminator
                 | compound_statement stmt_terminator'''
    p[0] = p[1]

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

def p_statement_separator(p):
    'statement_separator : COLON'
    p[0] = p[1]
    
def p_stmt_terminator(p):
    'stmt_terminator : EOL'
    p[0] = p[1]

#def p_compoundable_stmt_body(p):
#    'compoundable_stmt_body : stmt_body'
#    p[0] = p[1]
#    
#def p_non_compoundable_stmt_body(p):
#    '''non_compoundable_stmt_body : case_stmt'''
#    p[0] = p[1]
                
# TODO: Statements to be implemented
    '''stmt_body : beats_stmt
                 | chain_stmt
                 | dim_stmt
                 | gosub_stmt
                 | goto_stmt       
                 | input_stmt
                 | library_stmt
                 | line_stmt
                 | local_stmt
                 | mode_stmt     IAN needs ATTN commented out
                 | mouse_stmt    IAN needs ATTN commented out
                 | oscli_stmt
                 | proc_stmt
                 | quit_stmt
                 | read_stmt
                 | repeat_stmt
                 | report_stmt
                 | restore_stmt
                 | return_stmt
                 | swap_stmt       IAN
                 | sys_stmt        
                 | tempo_stmt
                 | tint_stmt
                 | trace_stmt
                 | voice_stmt
                 | voices_stmt
                 | while_stmt
                 | width_stmt'''

# All statements
def p_any_stmt_body(p):
    '''any_stmt_body : stmt_body
                     | lone_stmt_body'''
    p[0] = p[1]

# Statements which must appear alone on
# their own line                     
def p_lone_stmt_body(p):
    '''lone_stmt_body : case_stmt'''
    p[0] = p[1]

# Statements which can appear alone,
# or in compound statements on one line
def p_stmt_body(p):
    '''stmt_body : empty_stmt
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
                 | envelope_stmt
                 | fill_stmt
                 | gcol_stmt
                 | if_stmt
                 | for_stmt
                 | let_stmt
                 | move_stmt
                 | origin_stmt
                 | next_stmt
                 | plot_stmt
                 | print_stmt
                 | rectangle_stmt
                 | sound_stmt
                 | vdu_stmt'''
    if p[1]:
        p[0] = Statement(p[1])

# Empty statement
def p_empty_stmt(p):
    '''empty_stmt :'''
    pass

# BPUT statement
def p_bput_stmt(p):
    '''bput_stmt : BPUT channel COMMA expr'''
    p[0] = Bput(p[2], p[4])
    
# CALL statement
def p_call_stmt(p):
    '''call_stmt : CALL actual_arg_list'''
    p[0] = Call(p[2])

    
# TODO CASE stmt
# Not that WHEN clauses which follow the OTHERWISE clause
# a legal, but cannot be executed.
# TODO : Put this into a special class of statements which
# must begin on a new line.
def p_case_stmt(p):
    '''case_stmt : CASE expr OF stmt_terminator when_clause_list ENDCASE'''
    p[0] = Case(p[2], p[5])
    
def p_when_clause_list(p):
    '''when_clause_list : when_clause
                        | when_clause_list when_clause'''
    if len(p) == 2:
        p[0] = WhenClauseList(p[1])
    elif len(p) == 3:
        print "p2 = %s" % p[2]
        p[1].append(p[2])
        p[0] = p[1]
    
def p_when_clause(p):
    '''when_clause : WHEN expr_list COLON statement_list
                   | OTHERWISE statement_list'''
    if len(p) == 5:
        p[0] = WhenClause(p[2], p[4])
    elif len(p) == 3:
        p[0] = OtherwiseClause(p[2])

# TODO CHAIN stmt

# CIRCLE stmt
def p_circle_stmt(p):
    '''circle_stmt : CIRCLE expr COMMA expr COMMA expr
                   | CIRCLE FILL expr COMMA expr COMMA expr'''
    if len(p) == 7:
        p[0] = Circle(p[2], p[4], p[6])
    elif len(p) == 8:
        p[0] = Circle(p[3], p[5], p[7], fill=True)

# CLEAR
def p_clear_stmt(p):
    'clear_stmt : CLEAR'
    p[0] = Clear()

# CLOSE    
def p_close_stmt(p):
    'close_stmt : CLOSE channel'
    p[0] = Close(p[2])
    
# CLG    
def p_clg_stmt(p):
    'clg_stmt : CLG'
    p[0] = Clg()
    
# CLS    
def p_cls_stmt(p):
    'cls_stmt : CLS'
    p[0] = Clg() 

# COLOUR
def p_colour_stmt(p):
    '''colour_stmt : COLOUR expr
                   | COLOUR expr COMMA expr
                   | COLOUR expr COMMA expr COMMA expr COMMA expr'''
    if len(p) == 3:
        p[0] = Colour(p[2])
    elif len(p) == 5:
        p[0] = Palette(logical = p[2], physical = p[4])
    elif len(p) == 7:
        p[0] = Palette(logical = p[2], red = p[4], green = p[6], blue = p[8])
                   
# DATA
def p_data_statement(p):
    'data_stmt : DATA data_list'
    p[0] = Data(p[2])

# TODO: There is a serious challenge here, since the DATA list items
#       may consist of unquoted keywords such as PRINT    
def p_data_list(p):
    '''data_list : data_item
                 | data_list COMMA data_item'''
    if len(p) == 2:
        p[0] = DataList(p[1])
    elif len(p) == 4:
        p[0] = DataList(p[1], p[2])

# The manual says that "numeric values may include a calculation
# so long as there are no keywords
def p_data_item(p):
    '''data_item : LITERAL_INTEGER
                 | LITERAL_FLOAT
                 | LITERAL_STRING
                 | ID''' # Symbols converted into non-quoted strings

def p_def_stmt(p):
    '''def_stmt : def_fn_stmt
                | def_proc_stmt'''
    p[0] = p[1]
    
def p_def_fn_stmt(p):
    '''def_fn_stmt : DEF FN ID EQ expr
                   | DEF FN ID LPAREN formal_arg_list RPAREN EQ expr
                   | DEF FN ID LPAREN formal_arg_list RPAREN statement_list EQ expr'''
    if len(p) == 6:
        p[0] = DefineFunction(p[3], None, None, expr)
    elif len(p) == 9:
        p[0] = DefineFunction(p[3], p[5], None, p[8])
    elif len(p) == 10:
        p[0] = DefinieFunction(p[3], p[5], p[7], p[9])
                       
def p_def_proc_stmt(p):
    '''def_proc_stmt : DEF PROC ID statement_list ENDPROC
                     | DEF PROC ID LPAREN formal_arg_list RPAREN statement_list ENDPROC'''
    if len(p) == 6:
        p[0] = DefineFunction(p[3], None, p[4])
    elif len(p) == 9:
        p[0] = DefineFunction(p[3], p[5], p[7])

# DRAW statements
def p_draw_stmt(p):
    '''draw_stmt : DRAW expr COMMA expr
                 | DRAW BY expr COMMA expr'''
    if len(p) == 5:
        p[0] = Draw(p[2], p[4])
    elif len(p) == 6:
        p[0] = Draw(p[3], p[5], True)

def p_ellipse_stmt(p):
    '''ellipse_stmt : ELLIPSE expr COMMA expr COMMA expr COMMA expr
                    | ELLIPSE FILL expr COMMA expr COMMA expr COMMA expr'''
    if len(p) == 9:
        p[0] = Ellipse(p[2], p[4], p[6], p[8])
    elif len(p) == 10:
        p[0] = Ellipse(p[3], p[5], p[7], p[9],fill=True)

def p_envelope_stmt(p):
    '''envelope_stmt : ENVELOPE expr COMMA expr COMMA expr COMMA expr COMMA expr COMMA expr COMMA expr COMMA expr COMMA expr COMMA expr COMMA expr COMMA expr COMMA expr COMMA expr'''
    p[0] = Envelope(p[2],p[4],p[6],p[8],p[10],p[12],p[14],p[16],p[18],p[20],p[22],p[24],p[26],p[28] )

def p_fill_stmt(p):
    '''fill_stmt : FILL expr COMMA expr
                 | FILL BY expr COMMA expr'''
    if len(p) == 5:
        p[0] = Fill(p[2], p[4])
    elif len(p) == 6:
        p[0] = Fill(p[3], p[5], True)

def p_gcol_stmt(p):
    '''gcol_stmt : GCOL expr
                 | GCOL expr COMMA expr'''
    if len(p) == 3:
        p[0] = Gcol(p[2])
    elif len(p) == 5:
        p[0] = Gcol(p[4], p[2])

# IF statements

def p_if_stmt(p):
    '''if_stmt : if_single_stmt
               | if_multi_stmt'''
    p[0] = p[1]
    
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

# The clause is only used with IF statements and 
# possible ON statements when the result of an expression
# is interpreted as a line number to GOTO    
def p_clause(p):
    '''clause : compound_statement
              | expr'''
    p[0] = p[1]
                          
def p_if_multi_stmt(p):
    '''if_multi_stmt : IF expr THEN statement_list ENDIF
                     | IF expr THEN statement_list ELSE statement_list ENDIF'''
    if len(p) == 6:
        p[0] = If(p[2], p[4])
    elif len(p) == 8:
        p[0] = If(p[2], p[4], p[5])


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
       
# Rule for dealing with unmatched NEXT statements
def p_next_stmt(p):
    '''next_stmt : NEXT variable_list
                 | NEXT'''
    if len(p) == 3:
        p[0] = Next(p[2])
    elif len(p) == 2:
        p[0] = Next(None)

def p_variable_list(p):
    '''variable_list : variable
                     | variable_list COMMA variable'''
    if len(p) == 2:
        p[0] = VariableList(p[1])
    elif len(p) == 4:
        p[1].append(p[3])
        p[0] = p[1]
    
# Assignment

def p_let_stmt(p):
    '''let_stmt : LET variable EQ expr
                | variable EQ expr'''
    if len(p) == 5:
        p[0] = Assignment(p[2], p[4])
    elif len(p) == 4:
        p[0] = Assignment(p[1], p[3])
        
        # DRAW statements
def p_move_stmt(p):
    '''move_stmt : MOVE expr COMMA expr
                 | MOVE BY expr COMMA expr'''
    if len(p) == 5:
        p[0] = Move(p[2], p[4])
    elif len(p) == 6:
        p[0] = Move(p[3], p[5], True)

#def p_mode_stmt(p):
#    '''mode_stmt : MODE numeric'''    # may need a new type unless i use expr
#    p[0] = Mode(p[2])

#def p_mouse_stmt(p):
#    '''mouse_stmt : MOUSE expr COMMA expr COMMA expr
#                  | MOUSE ON
#                  | MOUSE ON expr
#                  | MOUSE OFF
#                  | MOUSE TO expr COMMA expr
#                  | MOUSE RECTANGLE expr COMMA expr COMMA expr COMMA expr
#                  | MOUSE RECTANGLE OFF'''
#    if len(p) == 7:
#        #MOUSE expr COMMA expr COMMA expr
#        p[0] = Mouse(p[2], p[4], p[6])
#    elif len(p) == 3:
#        #MOUSE ON
#        #MOUSE OFF
#        p[0] = Mouse(onOff = p[2]) # need to detect if it is ON or OFF
#    elif len(p) == 4:
#        #MOUSE ON expr
#        #MOUSE RECTANGLE OFF
#        p[0] = Mouse(shape = p[3]) # need help here. depend on p[2] depends of what params to send 
#    elif len(p) == 6:
#        #MOUSE TO expr COMMA expr
#        p[0] = Mouse(moveX = p[3], moveY = p[5])
#    elif len(p) == 10:
#        #MOUSE RECTANGLE expr COMMA expr COMMA expr COMMA expr
#        p[0] = Mouse(rectL = p[3], rectB = p[5], rectW = p[7], rectH = p[9])

def p_origin_stmt(p):
    '''origin_stmt : ORIGIN expr COMMA expr'''
    p[0] = Origin(p[2], p[4])

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
# Print related rules       
        
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
                  
    
def p_print_list(p):
    '''print_list : print_item
                  | print_list print_item'''
    if len(p) == 2:
        p[0] = PrintList(p[1])
    elif len(p) == 3:
        p[1].append(p[2])
        p[0] = p[1]
    
def p_print_item(p):
    '''print_item : expr
                  | tab 
                  | spc
                  | print_manipulator'''
    p[0] = PrintItem(p[1])
    
def p_print_manipulator(p):
    '''print_manipulator : TILDE
                         | APOSTROPHE
                         | COMMA
                         | SEMICOLON'''
    p[0] = PrintManipulator(p[1])
    
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

def p_sound_stmt(p):
    '''sound_stmt : SOUND expr COMMA expr COMMA expr COMMA expr
                  | SOUND OFF'''
    if len(p) == 9:
        p[0] = Sound(p[2], p[4], p[6], p[8])
    elif len(p) == 3:
        p[0] = Sound(off=True)
                    
def p_tab(p):
    '''tab : TAB_LPAREN expr RPAREN
           | TAB_LPAREN expr COMMA expr RPAREN'''
    if len(p) == 4:
        p[0] = TabH(p[2])
    elif len(p) == 6:
        p[0] = TabXY(p[2], p[4])                           

def p_spc(p):
    '''spc : SPC expr'''
    p[0] = Spc(p[2])

# VDU

def p_vdu_stmt(p):
    '''vdu_stmt : VDU
                | VDU vdu_list'''
    if len(p) == 2:
        p[0] = Vdu()
    elif len(p) == 3:    
        p[0] = Vdu(p[2])
    
def p_vdu_list(p):
    '''vdu_list : vdu_item
                | vdu_list vdu_item'''
    if len(p) == 2:
        p[0] = VduList(p[1])
    elif len(p) == 3:
        p[1].append(p[2])
        p[0] = p[1]

def p_vdu_item(p):
    '''vdu_item : expr vdu_separator
                | expr'''
    if len(p) == 2:
        p[0] = VduItem(p[1])
    elif len(p) == 3:
        p[0] = VduItem(p[1], p[2])


def p_vdu_separator(p):
    '''vdu_separator : COMMA
                     | SEMICOLON
                     | PIPE'''
    p[0] = p[1]

# Arguments

def p_actual_arg_list(p):
    '''actual_arg_list : expr_list'''
    p[0] = p[1]

def p_formal_arg_list(p):
    '''formal_arg_list : formal_arg
                       | formal_arg_list COMMA formal_arg'''
    if len(p) == 2:
        p[0] = FormalArgumentList(p[1])
    if len(p) == 4:
        p[0] = FormalArgumentList(p[1], p[3])
    
def p_formal_arg(p):
    '''formal_arg : ID
                  | RETURN ID'''
    if len(p) == 2:
        p[0] = FormalArgument(p[1])
    elif len(p) == 3:
        p[0] = FormalReferenceArgument(p[2]) 

# Expressions

def p_expr_list(p):
    '''expr_list : expr
                 | expr_list COMMA expr'''
    if len(p) == 2:
        p[0] = ExpressionList(p[1])
    elif len(p) == 4:
        p[1].append(p[3])
        p[0] = p[1]

def p_expr(p):
    '''expr : expr_function
            | expr_group
            | expr_unary_op
            | expr_binary_op
            | variable
            | literal'''
    p[0] = p[1]

def p_expr_unary_op(p):
    'expr_unary_op : unary_op expr'
    p[0] = UnaryOp(p[1], p[2]) # TODO: Use an operator factory here

def p_unary_op(p):
    '''unary_op : unary_query
                | unary_pling
                | unary_pipe
                | unary_dollar
                | unary_not'''
#                | unary_plus
#                | unary_minus
    p[0] = p[1]
    
def p_unary_query(p):
    'unary_query : QUERY expr %prec UQUERY'
    p[0] = IndirectByte(p[2])
    
def p_unary_pling(p):
    'unary_pling : PLING expr %prec UPLING'
    p[0] = IndirectInteger(p[2])
    
def p_unary_pipe(p):
    'unary_pipe : PIPE expr %prec UPIPE'
    p[0] = IndirectFloat(p[2])
    
def p_unary_dollar(p):
    'unary_dollar : DOLLAR expr %prec UDOLLAR'
    p[0] = IndirectString(p[2])
    
#def p_unary_minus(p):
#    'unary_minus : MINUS expr %prec UMINUS'
#    p[0] = UnaryMinus(p[2])
    
#def p_unary_plus(p):
#    'unary_plus : PLUS expr %prec UPLUS'
#    p[0] = UnaryPlus(p[2])
    
def p_unary_not(p):
    'unary_not : NOT expr %prec NOT'
    p[0] = Not(p[2])    

def p_expr_binary_op(p):
    '''expr_binary_op : binary_indirection_op
                      | binary_math_op'''
    p[0] = p[1]

def p_binary_indirection_op(p):
    '''binary_indirection_op : variable QUERY expr
                             | variable PLING expr
                             | variable PIPE expr
                             | variable DOLLAR expr'''
    p[0] = BinaryIndirectionOp(p[2], p[1], p[3])

def p_binary_math_op(p):
    '''binary_math_op : expr PLUS expr'''
    p[0] = BinaryMathOp(p[2], p[1], p[3])

#def p_binary_math_op(p):
#    '''binary_math_op : binary_plus_expr
#                      | binary_minus_expr
#                      | binary_times_expr
#                      | binary_divide_expr
#                      | binary_mod_expr
#                      | binary_div_expr
#                      | binary_power_expr
#                      | binary_eq_expr
#                      | binary_ne_expr
#                      | binary_lte_expr
#                      | binary_gte_expr
#                      | binary_lt_expr
#                      | binary_gt_expr
#                      | binary_shift_left_expr
#                      | binary_shift_right_expr
#                      | binary_shift_right_unsigned_expr
#                      | binary_and_expr
#                      | binary_or_expr
#                      | binary_eor_expr'''
#    p[0] = p[1]

#def binary_plus_expr(p):
#    'binary_plus_expr : expr PLUS expr'
#    p[0] = BinaryPlus(p[1], p[3])
#    
#def binary_minus_expr(p):
#    'binary_minus_expr : expr MINUS expr'
#    p[0] = BinaryMinus(p[1], p[3])
#
#def binary_times_expr(p):
#    'binary_times_expr : expr TIMES expr'
#    p[0] = BinaryTimes(p[1], p[3])
#     
#def binary_divide_expr(p):
#    'binary_divide_expr : expr DIVIDE expr'
#    p[0] = BinaryDivide(p[1], p[3])
#    
#def binary_mod_expr(p):
#    'binary_mod_expr : expr MOD expr'
#    p[0] = BinaryMod(p[1], p[3])
#
#def binary_div_expr(p):
#    'binary_div_expr : expr DIV expr'
#    p[0] = BinaryDiv(p[1], p[3])
#
#def binary_power_expr(p):
#    'binary_power_expr : expr CARET expr'
#    p[0] = BinaryPower(p[1], p[3])
#
#def binary_eq_expr(p):
#    'binary_eq_expr : expr EQ expr'
#    p[0] = BinaryEqual(p[1], p[3])
#
#def binary_ne_expr(p):
#    'binary_ne_expr : expr NE expr'
#    p[0] = BinaryNotEqual(p[1], p[3])
#
#def binary_lte_expr(p):
#    'binary_lte_expr : expr LTE expr'
#    p[0] = BinaryLessThanEqual(p[1], p[3])
#
#def binary_gte_expr(p):
#    'binary_gte_expr : expr GTE expr'
#    p[0] = BinaryGreaterThanEqual(p[1], p[3])
#
#def binary_lt_expr(p):
#    'binary_lt_expr : expr LT expr'
#    p[0] = BinaryLessThan([1], p[3])
#
#def binary_gt_expr(p):
#    'binary_gt_expr : expr GT expr'
#    p[0] = BinaryGreaterThan(p[1], p[3])
#
#def binary_shift_left_expr(p):
#    'binary_shift_left_expr : expr SHIFT_LEFT expr'
#    p[0] = BinaryShiftLeft(p[1], p[3])
#
#def binary_shift_right_expr(p):
#    'binary_shift_right_expr : expr SHIFT_RIGHT expr'
#    p[0] = BinaryPlus(p[1], p[3])
#
#def binary_shift_right_unsigned_expr(p):
#    'binary_shift_right_unsigned_expr : expr SHIFT_RIGHT_UNSIGNED expr'
#    p[0] = BinaryShiftRightUnsigned(p[1], p[3])
#
#def binary_and_expr(p):
#    'binary_and_expr : expr AND expr'
#    p[0] = BinaryAnd(p[1], p[3])
#
#def binary_or_expr(p):
#    'binary_or_expr : expr OR expr'
#    p[0] = BinaryOr(p[1], p[3])
#
#def binary_eor_expr(p):
#    'binary_eor_expr : expr EOR expr'
#    p[0] = BinaryEor(p[1], p[3])
#    
def p_expr_group(p):
    'expr_group : LPAREN expr RPAREN'
    p[0] = p[2]

# TODO: Functions to be implemented
'''    expr_function : adval_func
                     | deg_func
                     | dim_func
                     | end_func
                     | eof_func
                     | erl_func
                     | err_func
                     | eval_func
                     | exp_func
                     | get_func
                     | get_str_func
                     | inkey_func
                     | inkey_str_func
                     | int_func
                     | len_func
                     | ln_func
                     | log_func
                     | openin_func
                     | openout_func
                     | openup_func
                     | pi_func
                     | point_func
                     | pos_func
                     | rad_func
                     | report_str_func
                     | rnd_func
                     | sgn_func
                     | sin_func
                     | sqr_func
                     | string_str_func
                     | sum_func
                     | tan_func
                     | tempo_func
                     | usr_func
                     | val_func
                     | vpos_func'''
    
def p_expr_function(p):
    '''expr_function : user_func
                     | abs_func
                     | acs_func
                     | asc_func
                     | asn_func
                     | bget_func
                     | chr_str_func
                     | cos_func
                     | count_func
                     | str_str_func'''
    p[0] = p[1]

def p_user_func(p):
    'user_func : FN ID LPAREN actual_arg_list RPAREN %prec FUNCTION'
    p[0] = UserFunc(p[2], p[3])
     
def p_abs_func(p):
    'abs_func : ABS expr %prec FUNCTION'
    p[0] = AbsFunc(p[2])
    
def p_acs_func(p):
    'acs_func : ACS expr %prec FUNCTION'
    p[0] = AcsFunc(p[2])

def p_asn_func(p):
    'asn_func : ASN expr %prec FUNCTION'
    p[0] = AsnFunc(p[2])

def p_str_str_func(p):
    '''str_str_func : str_str_dec_func
                    | str_str_hex_func'''
    if len(p) == 3:
        p[0] = StrStringFunc(p[2])
    elif len(p) == 4:
        p[0] = StrStringFunc(p[3], 16) # Base 16 conversion

def p_str_str_dec_func(p):
    'str_str_dec_func : STR_STR expr %prec FUNCTION'
    p[0] = StrStringFunc(p[2], 10)
    
def p_str_str_hex_func(p):
    'str_str_hex_func : STR_STR TILDE expr %prec FUNCTION'
    p[0] = StrStringFunc(p[2], 16)
           
def p_asc_func(p):
    'asc_func : ASC expr %prec FUNCTION'
    p[0] = AscFunc(p[2])
    
def p_bget_func(p):
    'bget_func : BGET channel %prec FUNCTION'
    p[0] = BgetFunc(p[2])
    
def p_chr_str_func(p):
    'chr_str_func : CHR_STR expr %prec FUNCTION'
    p[0] = ChrStrFunc(p[2])
    
def p_cos_func(p):
    'cos_func : COS expr %prec FUNCTION'
    p[0] = CosFunc(p[2])
    
def p_count_func(p):
    'count_func : COUNT %prec FUNCTION'
    p[0] = CountFunc(p[2])  

def p_channel(p):
    '''channel : HASH expr %prec UHASH'''
    p[0] = Channel(p[2])

def p_literal(p):
    '''literal : literal_string
               | literal_integer
               | literal_float'''
    p[0] = p[1]

def p_literal_string(p):
    'literal_string : LITERAL_STRING'
    p[0] = LiteralString(p[1])
    
def p_literal_integer(p):
    'literal_integer : LITERAL_INTEGER'
    p[0] = LiteralInteger(p[1])
    
def p_literal_float(p):
    'literal_float : LITERAL_FLOAT'
    p[0] = LiteralFloat(p[1])

def p_variable(p):
    'variable : ID'
    p[0] = Variable(p[1])


# Error rule for syntax errors
def p_error(p):
    print "Syntax error in input!"

        
