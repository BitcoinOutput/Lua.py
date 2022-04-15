import ast
import lua_gen as lg
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
# This can make lua&python much, MUCH faster, and paired with the current python to lua
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

pyfuncs = {
    'len': lg.lualen
}

class Compiler:
    def __init__(self, pyast):
        self.pos = 0
        self.ast = pyast
        self.lfile = lg.LuaFile('out.lua')

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
                else:
                    end += str(const)

            elif self.inst(ast.Name):
                end += self.peek().id

            elif self.inst(ast.Expr):
                end += self.isocompile([self.peek().value])
            
            elif self.inst(ast.Call):
                fn = self.peek()
                name = fn.func.id
                args = [self.isocompile([x]) for x in fn.args]
                end += f'{name}({", ".join(args)})'

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
        self.lfile.write()

    def peek(self):
        return self.ast[self.pos]

    def prev(self):
        return self.ast[self.pos-1]

def gen_ast(x):
    tree = ast.parse(open(x).read())
    pprint(ast.dump(tree))

    return tree.body
    

def compile_file(x):
    compiler = Compiler(x)

    compiler.add(compiler.compile())
    compiler.write()