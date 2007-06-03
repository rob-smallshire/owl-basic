import ply.yacc as yacc

# Get the token map from the lexer.  This is required.
from bbc_lexer import tokens

def p_program(p):
    'program : statements'
    p[0] = p[1]
    
def p_statements(p):
    'statements : statements statement'
    p[0] = 

def p_statement(p):
    '''statement : stmt_body EOL'''

# TODO: Need to handle compound statements separated by a colon
# TODO: Need to handle continued statements with a backslash

def p_stmt_body(p):
    '''stmt_body : beats_stmt
                 | bput_stmt
                 | call_stmt
                 | case_stmt
                 | chain_stmt
                 | circle_stmt
                 | clg_stmt
                 | colour_stmt
                 | data_stmt
                 | def_stmt
                 | dim_stmt
                 | draw_stmt
                 | ellipse_stmt
                 | envelope_stmt
                 | fill_stmt
                 | fn_stmt
                 | for_stmt
                 | gcol_stmt
                 | gosub_stmt
                 | goto_stmt
                 | if_stmt
                 | input_stmt
                 | let_stmt
                 | library_stmt
                 | line_stmt
                 | local_stmt
                 | mode_stmt
                 | mouse_stmt
                 | move_stmt
                 | origin_stmt
                 | oscli_stmt
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
                 | swap_stmt
                 | sys_stmt
                 | tempo_stmt
                 | tint_stmt
                 | trace_stmt
                 | vdu_stmt
                 | voice_stmt
                 | voices_stmt
                 | while_stmt
                 | width_stmt'''

def p_if_stmt(p):
    '''if_stmt : if_single_stmt
               | if_multi_stmt'''
    p[0] = p[1]
    
def p_if_single_stmt(p):
    '''if_single_stmt : IF expr then_clause
                      | IF expr THEN then_clause
                      | IF expr then_clause ELSE else_clause
                      | IF expr THEN then_clause ELSE else_clause'''
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
    '''then_clause : stmt
                   | expr'''
    p[0] = p[1]
                          
def p_if_multi_stmt(p):
    '''if_multi_stmt : IF expr THEN statements ENDIF
                     | IF expr THEN statements ELSE statements ENDIF'''
    if len(p) == 6:
        p[0] = If(p[2], p[4])
    elif len(p) == 8:
        p[0] = If(p[2], p[4), p[5])
    

def p_let_stmt(p):
    '''let_stmt : LET variable EQ expr
                | variable EQ expr'''
    if len(p) == 5:
        p[0] = Assignment(p[2], p[4])
    elif len(p) == 4:
        p[0] = Assignment(p[1], p[3])
        
# Print        
        
def p_print_stmt(p):
    '''print_stmt : PRINT print_list
                  | PRINT channel arg_list'''
    if len(p) == 3:
        p[0] = Print(p[2])
    elif len(p) == 4:
        p[0] = PrintFile(p[2], p[3])      
                  
    
def p_print_list(p):
    '''print_list | print_list print_item'''
    
def p_print_item(p):
    '''print_item : expr
                  | tab 
                  | spc
                  | TILDE
                  | APOSTROPHE
                  | COMMA
                  | SEMICOLON'''
                    
def p_tab(p):
    '''tab : TAB LPAREN expr RPAREN
           | TAB LPAREN expr COMMA expr RPAREN'''
    if len(p) == 5:
        p[0] = TabH(p[3])
    elif len(p) == 7:
        p[] = TabXY(p[3], p[5])                           

def p_spc(p):
    '''spc : SPC LPAREN expr RPAREN'''
    p[0] = Spc(p[3])

# Expressions

def p_expr(p):
    '''expr : literal
            | variable
            | expr_unary_op
            | expr_binary_op
            | expr_group
            | expr_function'''
    p[0] = p[1]

def p_literal(p):
    '''literal : LITERAL_STRING
               | LITERAL_INTEGER
               | LITERAL_FLOAT'''
    p[0] = p[1]

def p_channel(p):
    '''channel : HASH expr'''
    p[0] = Channel(p[2])

def p_variable(p):
    'variable : ID'
    p[0] = p[1]

def p_expr_unary_op(p):
    'expr_unary_op : unary_op expr'
    p[0] = UnaryOp(p[1], p[2]) # TODO: Use an operator factory here
    
def p_unary_op(p):
    '''unary_op : QUERY
                | PLING
                | PIPE
                | DOLLAR
                | PLUS
                | MINUS
                | NOT'''
    p[0] = p[1]
    
def p_expr_binary_op(p):
    'expr_binary_op : expr binary_op expr'
    p[0] = BinaryOp(p[2], p[1], p[3]) # TODO: Use an operator factory here

def p_binary_op(p):
    '''binary_op : QUERY
                 | PLING
                 | PIPE
                 | DOLLAR
                 | PLUS
                 | MINUS
                 | TIMES
                 | DIVIDE
                 | MOD
                 | DIV
                 | CARET
                 | EQ
                 | NE
                 | LTE
                 | GTE
                 | LT
                 | GT
                 | SHIFT_LEFT
                 | SHIFT_RIGHT
                 | SHIFT_RIGHT_UNSIGNED
                 | AND
                 | OR
                 | EOR'''
     p[0] = p[1]
                 
def p_expr_group(p):
    'expr_group : LPAREN expr RPAREN'
    p[0] = p[2]
    
def p_expr_function(p):
    '''expr_function : user_func
                     | abs_func
                     | acs_func
                     | adval_func
                     | asc_func
                     | asn_func
                     | bget_func
                     | chr_str_func
                     | cos_func
                     | count_func
                     | deg_func
                     | dim_func
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
                     | str_str_func
                     | string_str_func
                     | sum_func
                     | tan_func
                     | tempo_func
                     | usr_func
                     | val_func
                     | vpos_func'''
     p[0] = p[1]

def p_user_func(p):
    'user_func : FN ID LPAREN arg_list RPAREN'
    p[0] = UserFunc(p[2], p[3])
     
def p_abs_func(p):
    'abs_func : ABS expr'
    p[0] = AbsFunc(p[2])
    
def p_acs_func(p):
    'acs_func : ACS expr'
    p[0] = AcsFunc(p[2])
    
def p_str_str_func(p):
    '''str_str_func : STR_STR expr
                    | STR_STR TILDE expr'''
    if len(p) == 3:
        p[0] = StrStringFunc(p[2])
    elif len(p) == 4:
        p[0] = StrStringFunc(p[3], 16) # Base 16 conversion
           
def p_asc_func(p):
    'asc_func : ASC expr'
    p[0] = AscFunc(p[2])
    
def p_bget_func(p):
    'bget_func : BGET channel'
    p[0] = BgetFunc(p[2])
    
def p_chr_str_func(p):
    'chr_str_func : CHR_STR expr'
    p[0] = ChrStrFunc(p[2])

# Error rule for syntax errors
def p_error(p):
    print "Syntax error in input!"

# Build the parser
yacc.yacc()