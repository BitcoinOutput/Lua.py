import ast
import lua_gen as lg
import prettyast as ps
from pprint import pprint

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


def parse_args(x):
    return [arg.arg for arg in x]


def errast(self, node, msg):
    print(f'[compiler {node.lineno}:{node.col_offset}]: {msg}')


class Compiler:
    def __init__(self, pyast):
        self.pos = 0
        self.ast = pyast
        self.lfile = lg.LuaFile('out.lua')

    def cmp(self, op, left, right):
        if isinstance(op, ast.Eq):
            return lg.eq(left, right)
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

    def compile(self):
        end = ''
        while not self.at_end():
            if self.inst(ast.Assign):
                var = self.peek()
                name = var.targets[0].id
                val = self.isocompile([var.value])

                if not name in variables:
                    end += lg.vardef(name, val)
                    variables.update({name: val})
                else:
                    end += lg.varset(name, val)

            elif self.inst(ast.Constant):
                const = self.peek().value
                if isinstance(const, str):
                    end += f'"{const}"'
                elif isinstance(const, bool):
                    end += str(const).lower()
                else:
                    end += str(const)

            elif self.inst(ast.Name):
                end += self.peek().id

            elif self.inst(ast.Expr):
                end += self.isocompile([self.peek().value])
            
            elif self.inst(ast.Call):
                fn = self.peek()
                name = self.isocompile([fn.func])
                args = [self.isocompile([x]) for x in fn.args]
                if name == "__lua__":
                    if not [(x[0] == '"' and x[0] == '"') or (x[0] == "'" and x[0] == "'")  for x in args] == [True]*len(args):
                        self.errast(fn, '__lua__ requires string arguments')
                    end += '\n'.join([x[1:-1] for x in args])
                else:
                    end += lg.call(name, args)
                
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
                try:
                    asname = import_.names[0].asname
                except: pass
                end += lg.require(name, asname)
            
            elif self.inst(ast.Compare):
                test  = self.peek()
                left  = self.isocompile([test.left])
                op    = test.ops[0]
                print(op)
                right = self.isocompile([test.comparators[0]])
                
                end += self.cmp(op, left, right)
            
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
                end += lg.function(name, args, body)
            self.advance()
        return end
    # ----------
    # | Utils  |
    # ----------

    def isocompile(self, ast):
        return Compiler(ast).compile()

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
    for node in tree.body:
        ps.pprint(node)

    return tree.body
    

def compile_file(x):
    compiler = Compiler(x)

    compiler.add(compiler.compile())
    compiler.write()