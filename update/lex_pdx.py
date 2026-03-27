"""
PLY Lexer for Paradox script files (Stellaris).
Extended from the techtree lexer to handle event files.
Supports: colons in identifiers (event_target:name), @variables, comparisons.
"""

from ply.lex import lex

tokens = (
    'BAREWORD', 'STRING', 'VARIABLE', 'NUMBER',
    'EQUALS', 'GTHAN', 'LTHAN', 'GTEQ', 'LTEQ',
    'LBRACE', 'RBRACE',
)

t_GTEQ = r'>='
t_LTEQ = r'<='
t_EQUALS = r'='
t_GTHAN = r'>'
t_LTHAN = r'<'
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_ignore = ' \t'


def t_comment(token):
    r'[#][^\r\n]*'
    pass


def t_newline(token):
    r'(?:\r?\n)+'
    token.lexer.lineno += token.value.count('\n')


def t_BAREWORD(token):
    r'[a-zA-Z_][-\w.:]*'
    return token


def t_VARIABLE(token):
    r'@[a-zA-Z_]\w*'
    return token


def t_STRING(token):
    r'\"([^\\"]|(\\.))*\"'
    escaped = False
    s = token.value[1:-1]
    new_str = []
    for c in s:
        if escaped:
            if c == 'n':
                new_str.append('\n')
            elif c == 't':
                new_str.append('\t')
            else:
                new_str.append(c)
            escaped = False
        else:
            if c == '\\':
                escaped = True
            else:
                new_str.append(c)
    token.value = ''.join(new_str)
    return token


def t_NUMBER(token):
    r'-?\d+(?:\.\d+)?'
    return token


def t_error(token):
    token.lexer.skip(1)


def create_lexer():
    return lex()
