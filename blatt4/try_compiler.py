from ast import *
from utils import *
from compiler_var import Compiler

compiler = Compiler()

prog = """
x = 6
y = x - 2
y = -2 + y
print(y - 2)
"""

if __name__ == "__main__":

    ast = parse(prog)
    print(ast)

    ast = compiler.remove_complex_operands(ast)
    ast = compiler.select_instructions(ast)
    ast = compiler.assign_homes(ast)
    ast = compiler.patch_instructions(ast)
    ast = compiler.prelude_and_conclusion(ast)

    file = open("output.s", "w")
    file.write(str(ast))
    file.flush()
    file.close()

    os.system("gcc -g -c -m64 output.s")
    os.system("gcc -g runtime.o output.o")

    print(str(ast))
