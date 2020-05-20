import os, sys

## graph

class Object:

    def __init__(self, V):
        self.val = V
        self.slot = {}
        self.nest = []
        self.id = '%x' % id(self)

    ## dump

    def __repr__(self): return self.dump()

    def dump(self, cycle=[], depth=0, prefix=''):
        # header
        tree = self.pad(depth) + self.head(prefix)
        # block cycles
        if self in cycle:
            return tree + ' _/'
        # slot{}s
        for i in self.slot:
            tree += self.slot[i].dump(cycle + [self], depth + 1,
                                      prefix='%s = ' % i)
        # nest[]ed
        idx = 0
        for j in self.nest:
            tree += j.dump(cycle + [self], depth + 1,
                           prefix='%s = ' % idx)
            idx += 1
        # subtree
        return tree

    def head(self, prefix=''):
        return '%s<%s:%s> @%s' % (prefix, self._type(), self._val(), self.id)

    def pad(self, depth): return '\n' + '\t' * depth

    def _type(self): return self.__class__.__name__.lower()
    def _val(self): return '%s' % self.val

    ## operator

    def __getitem__(self, key):
        return self.slot[key]

    def __setitem__(self, key, that):
        self.slot[key] = that
        return self

    def __lshift__(self, that):
        return Object.__setitem__(self, that._type(), that)

    def __rshift__(self, that):
        return Object.__setitem__(self, that._val(), that)

    def __floordiv__(self, that):
        assert isinstance(that, Object)
        self.nest.append(that)
        return self

    ## evaluate

    def eval(self, ctx):
        return ctx // self


## primitive

class Primitive(Object):
    pass

class Symbol(Primitive):
    def eval(self, ctx):
        return ctx[self.val]

class String(Primitive):
    pass

## active

class Active(Object):
    pass

class VM(Active):
    pass


vm = VM(__file__[:-3])
vm << vm

class Command(Active):
    def __init__(self, F):
        Active.__init__(self, F.__name__)
        self.fn = F

    def eval(self, ctx):
        return self.fn(ctx)

    def apply(self,that,ctx):
        return self.fn(that)

def QQ(ctx): print(ctx); sys.exit(0)


vm['??'] = Command(QQ)

## meta

class Meta(Object):
    pass

class Op(Meta):
    def eval(self, ctx):
        if self.val == '`':
            return self.nest[0]
        if self.val == '@':
            a = self.nest[0].eval(ctx)
            b = self.nest[1].eval(ctx)
            return a.apply(b, ctx)
        if self.val == ':':
            a = self.nest[0].eval(ctx)
            b = self.nest[1].eval(ctx)
            return a.apply(b, ctx)
        if self.val == '>>':
            a = self.nest[0].eval(ctx)
            b = self.nest[1].eval(ctx)
            return a >> b
        return Meta.eval(self, ctx)


vm >> Op('>>')

class Class(Meta):
    def __init__(self, C):
        Meta.__init__(self, C.__name__.lower())
        self.cls = C

    def apply(self, that, ctx):
        return self.cls(that.val)

class Section(Meta):
    pass


vm >> Class(Section)

## lexer


import ply.lex as lex

tokens = ['nl', 'symbol',
          'tick', 'lshift', 'rshift', 'push', 'colon']

t_ignore = ' \t\r'
t_ignore_comment = '\#.*'

def t_nl(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    return t

def t_tick(t):
    r'`'
    t.value = Op(t.value)
    return t
def t_lshift(t):
    r'<<'
    t.value = Op(t.value)
    return t
def t_rshift(t):
    r'>>'
    t.value = Op(t.value)
    return t
def t_push(t):
    r'//'
    t.value = Op(t.value)
    return t
def t_colon(t):
    r':'
    t.value = Op(t.value)
    return t

def t_symbol(t):
    r'[^ \t\r\n\#\:\<\>\/]+'
    t.value = Symbol(t.value)
    return t

def t_ANY_error(t): raise SyntaxError(t)


lexer = lex.lex()

## parser

import ply.yacc as yacc

precedence = (
    # ('right', 'eq'),
    # ('left', 'push'),
    ('left', 'apply'),
    ('left', 'lshift', 'rshift'),
    ('nonassoc', 'colon'),
    ('nonassoc', 'tick'),
)

def p_REPL_none(p):
    r' REPL : '
def p_REPL_nl(p):
    r' REPL : REPL nl '
def p_REPL_recur(p):
    r' REPL : REPL ex '
    # ex = p[2]
    # print(ex)
    # ex = ex.eval(vm)
    # print(ex)
    # if isinstance(ex, Command):
    #     ex = ex.eval(vm)
    # print(ex)
    print(p[2])
    print(p[2].eval(vm))
    print(vm)
    print('-' * 66)

def p_op_tick(p):
    r' ex : tick ex '
    p[0] = p[1] // p[2]
def p_op_lshift(p):
    r' ex : ex lshift ex '
    p[0] = p[2] // p[1] // p[3]
def p_op_rshift(p):
    r' ex : ex rshift ex '
    p[0] = p[2] // p[1] // p[3]
def p_op_push(p):
    r' ex : ex push ex '
    p[0] = p[2] // p[1] // p[3]
def p_op_colon(p):
    r' ex : ex colon ex '
    p[0] = p[2] // p[1] // p[3]

def p_apply(p):
    r' ex : ex ex %prec apply '
    p[0] = Op('@') // p[1] // p[2]

def p_ex_symbol(p):
    r' ex : symbol '
    p[0] = p[1]

def p_error(p): raise SyntaxError(p)


parser = yacc.yacc(debug=False, write_tables=False)

## init

if __name__ == '__main__':
    for srcfile in sys.argv[1:]:
        with open(srcfile) as src:
            lexer.file = srcfile
            parser.parse(src.read())
