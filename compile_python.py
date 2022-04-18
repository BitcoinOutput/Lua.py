import ast
import os
import gen_lua as lg

#      Python AST
#           |
#           V
# Desugared / Simplified AST
#           |
#           V
#       LuaCompiler
#           |
#           V
#        Assembly?
# I plan on soon to make a compiler for lua bytecode to assembly,
# This can make lua & python much, MUCH faster, and paired with the current python to lua
# compiler, it can compile python to assembly!
# so basically, lua bytecode -> native code, and:
# compiled python -> lua -> lua bytecode -> native code!

# Visit the AST and compile to lua

# Dict for keeping track of variable:
# a = 1
# a = 2
#   |
#   V
# local a = 1
# a = 2
#   !=
# local a = 1
# local a = 2

variables = {}

# macro_<NAME> <LUA BODY, NOT AST.>
macros = {}

boilerplate = """
-- to concatenate strings with +
local mt = debug.getmetatable("")
mt.__add = function (op1, op2)
    return op1 .. op2
end


-- https://www.tutorialspoint.com/how-to-split-a-string-in-lua-programming
local split
split = function(inputstr, sep)
   if sep == nil then
      sep = "%s"
   end
   local t={}
   for str in string.gmatch(inputstr, "([^"..sep.."]+)") do
      table.insert(t, str)
   end
   return t
end

mt.__index["split"] = split

local list = {}
list.__index = list

function list:new(args)
    local list_ = {}
    setmetatable(list_, list)
    list_.args = args
    return list_
end

local range
range = function(start, stop, step)
    if not stop then 
        stop = start
        start = 1
    end
    if not step then 
        step = 1
    end
    local index = {}
    for i = start, stop, step do 
        table.insert(index, #index, i)
    end
    return index
end

local idx
function idx(x, y)
    if type(x) == "string" then 
        return string.sub(x, y, y)
    end
    return x[y]
end

local len
len = function(x)
    return #x
end

function list:append(arg) 
    table.insert(self.args, arg)
end

function list:remove(arg) 
    table.remove(self.args, arg)
end

function list:pop() 
    table.remove(self.args, #self.args)
end

"""

def parse_args(x):
    return [arg.arg for arg in x]



class Compiler:
    def __init__(self, pyast, klass=None):
        self.pos = 0
        self.ast = pyast
        self.lfile = lg.LuaFile('out.lua')
        self.klass = klass
        self.add(boilerplate)

        
    def errast(self, node, msg):
        print(f'[compiler {node.lineno}:{node.col_offset}]: {msg}')


    def cmp(self, op, left, right):
        if isinstance(op, ast.Eq):
            return lg.eq(left, right)
        if isinstance(op, ast.NotEq):
            return lg.noteq(left, right)
        if isinstance(op, ast.Gt):
            return lg.greater(left, right)
        if isinstance(op, ast.GtE):
            return lg.greatereq(left, right)
        if isinstance(op, ast.Lt):
            return lg.less(left, right)
        if isinstance(op, ast.LtE):
            return lg.lesseq(left, right)
        self.errast(op, f"Unsupported operator {op}")

    def extract(self, if_stmt, elseifs, else_):
        for i in if_stmt.orelse:
            if isinstance(i, ast.If):
                test = self.isocompile([i.test])
                elbody = self.isocompile(i.body)
                elseifs.append([test, elbody])
                if i.orelse != []:
                    self.extract(i, elseifs, else_)
            else:
                else_.append(self.isocompile(if_stmt.orelse))
                return

    def binop(self, op, x, y):
        if isinstance(op, ast.Add):
            return lg.add(x, y)
        if isinstance(op, ast.Sub):
            return lg.sub(x, y)
        if isinstance(op, ast.Mult):
            return lg.mul(x, y)
        if isinstance(op, ast.Div):
            return lg.div(x, y)
        self.errast(op, f"Unsupported operator {op}")

    def compile(self):
        end = ''
        while not self.at_end():
            if self.inst(ast.Assign):
                var = self.peek()
                name = self.isocompile(var.targets)
                val = self.isocompile([var.value])

                if not name in variables:
                    end += lg.vardef(name, val)
                    variables.update({name: val})
                else:
                    end += lg.varset(name, val)

            elif self.inst(ast.Constant):
                const = self.peek().value
                if isinstance(const, str):
                    const = const.replace('\n', '\\n').replace('\r', '\\r')
                    end += f'"{const}"'
                elif isinstance(const, bool):
                    end += str(const).lower()
                else:
                    end += str(const)
            
            elif self.inst(ast.Dict):
                dict_ = self.peek()
                keys = dict_.keys
                values = dict_.values
                end_dict = {}
                for key, val in zip(keys, values):
                    end_dict.update({self.isocompile([key]): self.isocompile([val])})
                end += lg.convert_dicttable(end_dict)
                
            elif self.inst(ast.Subscript):
                sub = self.peek()
                value = self.isocompile([sub.value])
                slice = self.isocompile([sub.slice])
                end += lg.call('idx', [value, slice])
                
            elif self.inst(ast.For):
                for_ = self.peek()
                target = for_.target
                targets = []
                if isinstance(target, ast.Tuple):
                    for i in target.elts:
                        targets.append(i.id)
                else:
                    targets.append(target.id)
                iter = self.isocompile([for_.iter])
                body = self.isocompile(for_.body)
                
                end += lg.for_loop(targets, iter, body)
            
            elif self.inst(ast.AugAssign):
                var = self.peek()
                target = var.target.id
                end += lg.varset(target, self.binop(var.op, target, self.isocompile([var.value])))
            
            elif self.inst(ast.BinOp):
                binop = self.peek()
                left = self.isocompile([binop.left])
                right = self.isocompile([binop.right])
                
                end += self.binop(binop.op, left, right)
                
            
            elif self.inst(ast.Name):
                name = self.peek().id
                if name == 'args':
                    end += '...'
                else:
                    end += name

            elif self.inst(ast.Expr):
                end += self.isocompile([self.peek().value])+'\n'
            
            elif self.inst(ast.Call ):
                fn = self.peek()
                name = self.isocompile([fn.func])
                args = [self.isocompile([x]) for x in fn.args]
                if name in macros:
                    # It is a macro
                    end += macros[name]
                else:
                    if name == "__lua__":
                        if not self.list_string_check(args):
                            self.errast(fn, '__lua__ requires string arguments')
                        end += '\n'.join([x[1:-1] for x in args])
                    else:
                        name_ = name.split(".")
                        if len(name_) == 1:
                            end += lg.call(name, args).strip()
                        else:
                            last = name_.pop()
                            end += lg.selfcall('.'.join(name_), last, args).strip()
            
            elif self.inst(ast.While):
                while_stmt = self.peek()
                test = self.isocompile([while_stmt.test])
                body = self.isocompile(while_stmt.body)
                end += lg.while_stmt(test, body)
                
            elif self.inst(ast.Return):
                end += lg.return_stmt(self.isocompile([self.peek().value]))
                
            elif self.inst(ast.Attribute):
                attr = self.peek()
                attr1 = self.isocompile([attr.value])
                attr2 = attr.attr
                end += f'{attr1}.{attr2}'
            
            elif self.inst(ast.Import):
                import_ = self.peek()
                name    = import_.names[0].name
                asname  = name
                if name.startswith('lualib.'):
                    fname = os.path.join(os.path.dirname(__file__), os.path.join('lib', name.split('.', 1)[1]+'.py'))
                    prog = self.isocompile(gen_ast(fname))
                    end += prog+'\n'
                        
                else:
                    end += lg.require(name, asname)
                    try:
                        asname = import_.names[0].asname
                    except: pass
            
            elif self.inst(ast.Compare):
                test  = self.peek()
                left  = self.isocompile([test.left])
                op    = test.ops[0]
                right = self.isocompile([test.comparators[0]])
                
                end += self.cmp(op, left, right)
            
            elif self.inst(ast.List):
                list_ = self.peek()
                elts  = [self.isocompile([x]) for x in list_.elts]
                print(elts)
                end  += lg.selfcall('list', 'new', [lg.table(elts)])
            elif self.inst(ast.If):
                If      = self.peek()
                test    = self.isocompile([If.test])
                body    = self.isocompile(If.body)
                elseifs = []
                else_   = []
                self.extract(If, elseifs, else_)
                end += lg.if_stmt([test, body], elseifs, else_)
                        
            
            elif self.inst(ast.FunctionDef):
                fn = self.peek()
                name = fn.name
                args = parse_args(fn.args.args)
                body = self.isocompile(fn.body)
                if name.startswith('macro_'):
                    # It is a macro
                    macros.update({name: body})
                else:
                    if fn.args.vararg:
                        args.append('...')
                    if not self.klass:
                        end += lg.function(name, args, body)
                    else:
                        end += lg.method(self.klass, name, args, body)
                    
            elif self.inst(ast.ClassDef):
                klass = self.peek()
                name = klass.name
                body = self.isocompile(klass.body, name)
                end += lg.class_def(name, body)
            
            elif self.inst(ast.UnaryOp):
                return self.unaryize(self.peek())
            self.advance()
        return end
    # ----------
    # | Utils  |
    # ----------
    
    def unaryize(self, x):
        op = ''
        if isinstance(x.op, ast.USub):
            op = '-'
        return f'{op}{self.isocompile([x.operand])}'
    
    def string_check(self, item):
        return (item[0] == '"' and item[-1] == '"') or (item[0] == "'" and item[-1] == "'")

    def list_string_check(self, item):
        return [self.string_check(x) for x in item] == [True for i in range(len(item))]

    def isocompile(self, *args):
        return Compiler(*args).compile()

    def inst(self, x):
        return isinstance(self.peek(), x)

    def advance(self):
        self.pos += 1

    def at_end(self):
        return self.pos >= len(self.ast)

    def devance(self):
        self.pos -= 1

    def add(self, item):
        self.lfile.append(item)

    def write(self):
        self.lfile.strip_excess()
        self.lfile.write()

    def peek(self):
        return self.ast[self.pos]

    def prev(self):
        return self.ast[self.pos-1]


def gen_ast(x):
    tree = ast.parse(open(x).read())
    return tree.body
    

def compile_file(x):
    compiler = Compiler(x)

    compiler.add(compiler.compile())
    compiler.write()