import ast
from ast import *
from utils import *
from x86_ast import *
import os

Binding = tuple[Name, expr]
Temporaries = list[Binding]

get_fresh_tmp = lambda: generate_name('tmp')


class Compiler:
    def __init__(self):
        self.stack_size = 0

    ############################################################################
    # Remove Complex Operands
    ############################################################################
    def is_atomic(self, e: expr):
        match e:
            case ast.Constant(value = val):
                return True
            case ast.Name(id = i, ctx = c):
                return True
        return False

    def rco_exp(self, e: expr, need_atomic: bool) -> tuple[expr, Temporaries]:
        match e:
            # Atomic cases: constant or variable
            case ast.Constant() | ast.Name():
                return (e, [])

            # Unary operation: -e
            case ast.UnaryOp(op, operand):
                new_operand, stmts = self.rco_exp(operand, need_atomic=True)
                new_exp = ast.UnaryOp(op, new_operand)
                if need_atomic:
                    tmp = get_fresh_tmp()
                    stmts.append((tmp, new_exp))
                    return (ast.Name(tmp, ctx=ast.Load()), stmts)
                else:
                    return (new_exp, stmts)

            # Binary operation: left + right
            case ast.BinOp(left, op, right):
                new_left, stmts1 = self.rco_exp(left, need_atomic=True)
                new_right, stmts2 = self.rco_exp(right, need_atomic=True)
                all_stmts = stmts1 + stmts2
                new_exp = ast.BinOp(new_left, op, new_right)
                if need_atomic:
                    tmp = get_fresh_tmp()
                    all_stmts.append((tmp, new_exp))
                    return (ast.Name(tmp, ctx=ast.Load()), all_stmts)
                else:
                    return (new_exp, all_stmts)

            # Function calls (e.g., input_int(), print(x))
            case ast.Call(func, args, keywords):
                # Process each argument to be atomic
                new_args = []
                all_stmts = []
                for arg in args:
                    new_arg, arg_stmts = self.rco_exp(arg, need_atomic=True)
                    new_args.append(new_arg)
                    all_stmts.extend(arg_stmts)
                new_call = ast.Call(func, new_args, keywords)
                if need_atomic:
                    tmp = get_fresh_tmp()
                    all_stmts.append((tmp, new_call))
                    return (ast.Name(tmp, ctx=ast.Load()), all_stmts)
                else:
                    return (new_call, all_stmts)

            case _:
                raise NotImplementedError(f"Unhandled expression: {type(e)}")
    def rco_stmt(self, s: stmt) -> list[stmt]:
        match s:
            case ast.Assign(targets, value):
                new_rhs, temps = self.rco_exp(value, need_atomic=False)
                new_assign = ast.Assign(targets, new_rhs)
                result = []
                for tmp_var, tmp_val in temps:
                    tmp_assign = ast.Assign([ast.Name(tmp_var, ctx=ast.Store())], tmp_val)
                    result.append(tmp_assign)
                result.append(new_assign)
                return result

            case ast.Expr(value):
                new_val, temps = self.rco_exp(value, need_atomic=False)  
                result = []
                for tmp_var, tmp_val in temps:
                    tmp_assign = ast.Assign([ast.Name(tmp_var, ctx=ast.Store())], tmp_val)
                    result.append(tmp_assign)
                result.append(ast.Expr(new_val))
                return result

            case _:
                return [s]

    def remove_complex_operands(self, p: Module) -> Module:
        new_body = []
        for stmt in p.body:
            new_body.extend(self.rco_stmt(stmt))
        return ast.Module(body=new_body, type_ignores=[])

    ############################################################################
    # Select Instructions
    ############################################################################

    def select_arg(self, e: expr) -> arg:
        match e:
            # Atomic cases: constant or variable
            case ast.Constant():
                return Immediate(e.value)
            case ast.Name():
                return Variable(e.id)
            case _:
                raise NotImplementedError(f"Not an atomic: {type(e)}")

    def select_stmt(self, s: stmt) -> list[instr]:
        instructions = []
        match s:
            case ast.Assign(targets, value):
                print(targets[0].id)
                match value:
                    case ast.Constant(value = val):
                        instructions.append( Instr("movq", (self.select_arg(value), self.select_arg(targets[0]))))

                    case ast.Name(id = val):
                        instructions.append( Instr("movq", (self.select_arg(value), self.select_arg(targets[0]))))

                    case ast.BinOp(left, op, right):
                        instructions.append( Instr("movq", (self.select_arg(left), self.select_arg(targets[0]))))
                        instructions.append( Instr("addq", (self.select_arg(right), self.select_arg(targets[0]))))
                    case ast.UnaryOp(op, operand):
                        print("messing with unary")
                        match op:
                            case ast.USub():
                                instructions.append( Instr("subq", [self.select_arg(operand)]))
                                instructions.append( Instr("movq", (Reg("rax"),self.select_arg(targets[0]))))
                            case _:
                                raise NotImplementedError("Unsuported unary operator")
                    #need to take care of calls to get int

            case ast.Expr(value):
                #need to handle fruitless code and printing
                pass
        return instructions

    def select_instructions(self, p: Module) -> X86Program:
        new_body = []
        for stmt in p.body:
            new_body.extend(self.select_stmt(stmt))

        return X86Program(new_body)

    ############################################################################
    # Assign Homes
    ############################################################################

    def assign_homes_arg(self, a: arg, home: dict[Variable, arg]) -> arg:
        raise Exception('not implemented')

    def assign_homes_instr(self, i: instr, home: dict[Variable, arg]) -> instr:
        raise Exception('not implemented')

    def assign_homes_instrs(
        self, ss: list[instr], home: dict[Variable, arg]
    ) -> list[instr]:
        raise Exception('not implemented')

    def assign_homes(self, p: X86Program) -> X86Program:
        raise Exception('not implemented')

    ############################################################################
    # Patch Instructions
    ############################################################################

    def patch_instr(self, i: instr) -> list[instr]:
        raise Exception('not implemented')

    def patch_instrs(self, instrs: list[instr]) -> list[instr]:
        raise Exception('not implemented')

    def patch_instructions(self, p: X86Program) -> X86Program:
        raise Exception('not implemented')

    ############################################################################
    # Prelude & Conclusion
    ############################################################################

    def prelude_and_conclusion(self, p: X86Program) -> X86Program:
        raise Exception('not implemented')

    ##################################################
    # Compiler
    ##################################################

    def compile(self, s: str, logging=False) -> X86Program:
        compiler_passes = {
            'remove complex operands': self.remove_complex_operands,
            'select instructions': self.select_instructions,
        }
        '''
            'assign homes': self.assign_homes,
            'patch instructions': self.patch_instructions,
            'prelude & conclusion': self.prelude_and_conclusion,
        }
        '''

        current_program = parse(s)

        if logging == True:
            print()
            print('==================================================')
            print(' Input program')
            print('==================================================')
            print()
            print(s)

        for pass_name, pass_fn in compiler_passes.items():
            current_program = pass_fn(current_program)

            if logging == True:
                print()
                print('==================================================')
                print(f' Output of pass: {pass_name}')
                print('==================================================')
                print()
                print(current_program)

        return current_program


##################################################
# Execute
##################################################

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python compiler.py <source filename>')
    else:
        file_name = sys.argv[1]
        with open(file_name) as f:
            print(f'Compiling program {file_name}...')

            try:
                program = f.read()
                compiler = Compiler()
                x86_program = compiler.compile(program, logging=True)

                with open(file_name + '.s', 'w') as output_file:
                    output_file.write(str(x86_program))

            except:
                print(
                    'Error during compilation! **************************************************'
                )
                import traceback

                traceback.print_exception(*sys.exc_info())
