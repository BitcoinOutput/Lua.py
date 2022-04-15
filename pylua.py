import compile_python
from sys import argv

if len(argv) <= 1:
    print("usage: pylua <file>")
else:
    ast = compile_python.gen_ast(argv[1])
    compile_python.compile_file(ast)