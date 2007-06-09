import ply.yacc as yacc

# Get the token map from the lexer.  This is required.
from bbc_lexer import tokens
from bbc_ast import *

def p_program(p):
    'program : statement_list'
    p[0] = p[1]

# TODO: Distinguish single-line compound statements
    
def p_statement_list(p):
    '''statement_list : statement
                      | statement_list statement'''
    if len(p) == 2:
        p[0] = StatementList(p[1])
    elif len(p) == 3:
        p[0] = StatementList(p[1], p[2])

def p_statement(p):
    '''statement : compound_statement stmt_end'''
    p[0] = p[1]

# A single line statement list - use in single-line IF THEN ELSE oonstruct
# TODO: May need concept of an empty statement to deal with trailing colons
def p_compound_statement(p):
    '''compound_statement : stmt_body
                          | compound_statement statement_separator stmt_body'''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 4:
        p[0] = StatementList(p[1], p[3])

def p_statement_separator(p):
    'statement_separator : COLON'
    p[0] = p[1]
    
def p_stmt_terminator(p):
    'stmt_end : EOL'
    p[0] = p[1]
                
# TODO: Statements to be implemented
    '''stmt_body : beats_stmt
                 | case_stmt
                 | chain_stmt
                 | dim_stmt
                 | draw_stmt
                 | ellipse_stmt
                 | envelope_stmt
                 | fill_stmt
                 | for_stmt
                 | gcol_stmt
                 | gosub_stmt
                 | goto_stmt
                 | input_stmt
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

def p_stmt_body(p):
    '''stmt_body : bput_stmt
                 | call_stmt
                 | circle_stmt
                 | clear_stmt
                 | clg_stmt
                 | cls_stmt
                 | close_stmt
                 | colour_stmt
                 | data_stmt
                 | def_stmt
                 | if_stmt
                 | let_stmt
                 | print_stmt'''
    p[0] = p[1]  

# BPUT statement
def p_bput_stmt(p):
    '''bput_stmt : BPUT channel COMMA expr'''
    p[0] = Bput(p[2], p[4])
    
# CALL statement
def p_call_stmt(p):
    '''call_stmt : CALL actual_arg_list'''
    p[0] = Call(p[2])
    
# TODO CASE stmt

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
    if len(p) == 5:
        p[0] = DefineFunction(p[3], None, p[4])
    elif len(p) == 8:
        p[0] = DefineFunction(p[3], p[5], p[7])
        
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
    
# Assignment

def p_let_stmt(p):
    '''let_stmt : LET variable EQ expr
                | variable EQ expr'''
    if len(p) == 5:
        p[0] = Assignment(p[2], p[4])
    elif len(p) == 4:
        p[0] = Assignment(p[1], p[3])
        
# Print related rules       
        
def p_print_stmt(p):
    '''print_stmt : PRINT print_list
                  | PRINT channel actual_arg_list'''
    if len(p) == 3:
        p[0] = Print(p[2])
    elif len(p) == 4:
        p[0] = PrintFile(p[2], p[3])      
                  
    
def p_print_list(p):
    '''print_list : print_item
                  | print_list print_item'''
    p[0] = PrintList(p[1], p[2])
    
def p_print_item(p):
    '''print_item : expr
                  | tab 
                  | spc
                  | TILDE
                  | APOSTROPHE
                  | COMMA
                  | SEMICOLON'''
    p[0] = p[1]
                    
def p_tab(p):
    '''tab : TAB LPAREN expr RPAREN
           | TAB LPAREN expr COMMA expr RPAREN'''
    if len(p) == 5:
        p[0] = TabH(p[3])
    elif len(p) == 7:
        p[0] = TabXY(p[3], p[5])                           

def p_spc(p):
    '''spc : SPC LPAREN expr RPAREN'''
    p[0] = Spc(p[3])

# Arguments

def p_actual_arg_list(p):
    '''actual_arg_list : expr
                       | actual_arg_list COMMA expr'''
    if len(p) == 2:
        return ActualArgmentList(p[1])
    elif len(p) == 4:
        return ActualArgumentList(p[1], p[3])

def p_formal_arg_list(p):
    '''formal_arg_list : formal_arg
                       | formal_arg_list COMMA formal_arg'''
    if len(p) == 2:
        return FormalArgumentList(p[1])
    if len(p) == 4:
        return FormalArgumentList(p[1], p[3])
    
def p_formal_arg(p):
    '''formal_arg : ID
                  | RETURN ID'''
    if len(p) == 2:
        p[0] = FormalArgument(p[1])
    elif len(p) == 3:
        p[0] = FormalReferenceArgument(p[2]) 

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
    '''unary_op : unary_query
                | unary_pling
                | unary_pipe
                | unary_dollar
                | unary_plus
                | unary_minus
                | unary_not'''
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
    
def p_unary_minus(p):
    'unary_minus : MINUS expr %prec UMINUS'
    p[0] = UnaryMinus(p[2])
    
def p_unary_plus(p):
    'unary_plus : PLUS expr %prec UPLUS'
    p[0] = UnaryPlus(p[2])
    
def p_unary_not(p):
    'unary_not : NOT expr %prec NOT'    

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

# Precedence table for the above operators
precedence = (
             ('left', 'EOR', 'OR'),
             ('left', 'AND'),
             ('nonassoc', 'EQ' 'NE', 'LTE', 'GTE', 'LT', 'GT', 'SHIFT_LEFT', 'SHIFT_RIGHT', 'SHIFT_RIGHT_UNSIGNED'),
             ('left', 'PLUS', 'MINUS'),
             ('left', 'TIMES', 'DIVIDE', 'MOD', 'DIV'),
             ('left', 'CARET'),
             ('left', 'PLING', 'QUERY', 'PIPE', 'DOLLAR'),  # Binary indirection operators
             ('right', 'NOT', 'UPLUS', 'UMINUS', 'UPLING', 'UQUERY', 'UPIPE', 'UDOLLAR') # Unary operators
             )
                 
def p_expr_group(p):
    'expr_group : LPAREN expr RPAREN'
    p[0] = p[2]

# TODO: Functions to be implemented
'''    expr_function : adval_func
                     | asn_func
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
                     | bget_func
                     | chr_str_func
                     | cos_func
                     | count_func
                     | str_str_func'''
    p[0] = p[1]

def p_user_func(p):
    'user_func : FN ID LPAREN actual_arg_list RPAREN'
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
    
def p_cos_func(p):
    'cos_func : COS expr'
    p[0] = CosFunc(p[2])
    
def p_count_func(p):
    'count_func : COUNT'
    p[0] = CountFunc(p[2])  

# Error rule for syntax errors
def p_error(p):
    print "Syntax error in input!"

# Build the parser
yacc.yacc()

