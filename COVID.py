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

    def dump(self, cycle=[], depth=0, prefix='', test=False):
        # header
        tree = self.pad(depth) + self.head(prefix, test)
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

    def head(self, prefix='', test=False):
        hdr = '%s<%s:%s>' % (prefix, self._type(), self._val())
        if not test:
            hdr += ' @%s' % self.id
        return hdr

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

    ## stack

    def dropall(self): self.nest = []; return self

    ## evaluate

    def eval(self, ctx):
        return ctx // self


## primitive

class Primitive(Object):
    def eval(self, ctx): return self

class Symbol(Primitive):
    def eval(self, ctx):
        return ctx[self.val]

class String(Primitive):
    pass

class Number(Primitive):
    pass

class Integer(Number):
    def __init__(self, V):
        Primitive.__init__(self, int(V))

## active

class Active(Object):
    pass

class VM(Active):
    pass


vm = VM(__file__.split('/')[-1][:-3])
vm << vm

class Command(Active):
    def __init__(self, F):
        Active.__init__(self, F.__name__)
        self.fn = F

    def eval(self, ctx):
        return self.fn(ctx)

    def apply(self, that, ctx):
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
        if self.val == '=':
            a = self.nest[0].eval(ctx)
            b = self.nest[1].eval(ctx)
            ctx[a.val] = b
            return b
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

tokens = ['nl', 'symbol', 'str',
          'tick', 'lshift', 'rshift', 'push', 'colon', 'eq', 'semicolon']

t_ignore = ' \t\r'
t_ignore_comment = '\#.*'

states = (('str', 'exclusive'),)

t_str_ignore = ''

def t_str(t):
    r'\''
    t.lexer.push_state('str')
    t.lexer.string = ''
def t_str_str(t):
    r'\''
    t.lexer.pop_state()
    t.value = String(t.lexer.string)
    return t
def t_str_any(t):
    r'.'
    t.lexer.string += t.value

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
def t_eq(t):
    r'='
    t.value = Op(t.value)
    return t

def t_semicolon(t):
    r';'
    return t

def t_symbol(t):
    r'[^ \t\r\n\#\:\;\<\>\/]+'
    t.value = Symbol(t.value)
    return t

def t_ANY_error(t): raise SyntaxError(t)


lexer = lex.lex()

## parser

import ply.yacc as yacc

precedence = (
    ('right', 'eq'),
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
def p_REPL_semicolon(p):
    r' REPL : REPL semicolon '
    vm.dropall()
def p_REPL_recur(p):
    r' REPL : REPL ex '
    vm // p[2].eval(vm)
    # print(p[2])
    # print(p[2].eval(vm))
    # print(vm)
    # print('-' * 66)

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
def p_op_eq(p):
    r' ex : ex eq ex '
    p[0] = p[2] // p[1] // p[3]

def p_apply(p):
    r' ex : ex ex %prec apply '
    p[0] = Op('@') // p[1] // p[2]

def p_ex_symbol(p):
    r' ex : symbol '
    p[0] = p[1]
def p_ex_str(p):
    r' ex : str '
    p[0] = p[1]

def p_error(p): raise SyntaxError(p)


parser = yacc.yacc(debug=False, write_tables=False)

## web interface

class Net(Object):
    pass
class IP(Net):
    pass
class Port(Net, Integer):
    pass


import flask

class Web(Net):
    def __init__(self, V):
        Net.__init__(self, V)
        self.app = flask.Flask(V)
        self << IP(os.environ['IP'])
        self << Port(os.environ['PORT'])

    def eval(self, ctx):

        @self.app.route('/')
        def index():
            return flask.render_template('index.html', ctx=ctx, web=self)

        @self.app.route('/<path:path>.css')
        def css(path):
            return self.app.send_static_file(path + '.css')

        @self.app.route('/<path:path>.js')
        def js(path):
            return self.app.send_static_file(path + '.js')

        @self.app.route('/<path:path>.map')
        def map(path):
            return self.app.send_static_file(path + '.map')

        @self.app.route('/<path:path>.png')
        def png(path):
            return self.app.send_static_file(path + '.png')

        @self.app.route('/manifest')
        def manifest():
            return self.app.send_static_file('manifest')

        self.app.run(debug=True, host=self['ip'].val, port=self['port'].val,
                     extra_files=[sys.argv[0][:-3] + '.ini'])


def WEB(ctx): web = ctx['WEB'] = Web(ctx.val); return web.eval(ctx)


vm >> Command(WEB)

## init

if __name__ == '__main__':
    for srcfile in sys.argv[1:]:
        with open(srcfile) as src:
            lexer.file = srcfile
            parser.parse(src.read())
