import os
from x86_ast import (Instr, instr, Reg, Variable, arg,
                     X86Program, Callq, Deref, Immediate)
from utils import *
from ast import (Module, Assign, Expr, BinOp, UnaryOp, Add, Sub, USub,
                 expr, Name, Constant, Call, stmt)

Binding = tuple[Name, expr]
emporaries = list[Binding]


def get_fresh_tmp(): return generate_name("tmp")


class Compiler:
    def __init__(self):
        self.stack_size = 0
        self.temporary_counter = 0
        self.stack_frame = 0

    ###########################
    # Remove Complex Operands #
    ###########################

    def rco_exp(self, e: expr, needs_to_be_atomic: bool) -> tuple[expr, Temporaries]:
        match e:
            case Constant(_):
                return (e, [])

            case Name(_):
                return (e, [])

            case Call(Name("input_int"), []):
                tmp_n = self.temporary_counter
                self.temporary_counter += 1
                name = Name(f"tmp_{tmp_n}")
                return (name, [(name, e)])

            case UnaryOp(op, expr):
                atm, temps = self.rco_exp(expr, True)
                if needs_to_be_atomic:
                    match atm:
                        case Constant(_):
                            tmp_n = self.temporary_counter
                            self.temporary_counter += 1
                            name = Name(f"tmp_{tmp_n}")
                            return (name, temps + [(name, UnaryOp(op, atm))])
                        case Name(_):
                            return (atm, temps + [(atm, UnaryOp(op, atm))])
                else:
                    return (UnaryOp(op, atm), temps)

            case BinOp(expr1, op, expr2):
                atm_1, temps_1 = self.rco_exp(expr1, True)
                atm_2, temps_2 = self.rco_exp(expr2, True)

                if needs_to_be_atomic:
                    match atm_1:
                        case Constant(_):
                            tmp_n = self.temporary_counter
                            self.temporary_counter += 1
                            name = Name(f"tmp_{tmp_n}")
                            return (name, temps_1 + temps_2 + [(name, BinOp(atm_1, op, atm_2))])
                        case Name(_):
                            return (atm_1, temps_1 + temps_2 + [(atm_1, BinOp(atm_1, op, atm_2))])
                else:
                    return (BinOp(atm_1, op, atm_2), temps_1 + temps_2)

        return (e, [])

    def rco_stmt(self, s: stmt) -> list[stmt]:
        statements = []
        match s:
            case Expr(Call(Name("print"), expr)):
                atm, temp = self.rco_exp(expr[0], True)
                statements = (
                    statements
                    + [Assign([name], expr) for name, expr in temp]
                    + [Expr(Call(Name("print"), args=[atm], keywords=[]))]
                )
            case Assign(name, exp):
                atm, temp = self.rco_exp(exp, False)
                statements = (
                    statements
                    + [Assign([name], exp) for name, exp in temp]
                    + [Assign(name, atm)]
                )
            case Expr(exp):
                # A statement thats an expression without
                # assignment can be optimized out
                statements += []

        return statements

    def remove_complex_operands(self, p: Module) -> Module:
        new_statements = []
        for s in p.body:
            new_statements += self.rco_stmt(s)

        p.body = new_statements

        return p

    #######################
    # Select Instructions #
    #######################

    def select_arg(self, e: expr) -> arg:
        match e:
            case Constant(c):
                return Immediate(c)
            case Name(name):
                return Variable(name)
            case _:
                raise RuntimeError(f"Unable to convert argument {e}!")

    def select_stmt(self, s: stmt) -> list[instr]:
        match s:
            case Assign([Name(name)], BinOp(atm1, Add(), atm2)):
                arg1 = self.select_arg(atm1)
                arg2 = self.select_arg(atm2)
                var = Variable(name)

                if arg1 == var:
                    return [
                        Instr("addq", [arg2, var]),
                    ]
                elif arg2 == var:
                    return [
                        Instr("addq", [arg1, var]),
                    ]
                else:
                    return [
                        Instr("movq", [arg1, var]),
                        Instr("addq", [arg2, var]),
                    ]

            case Assign([Name(name)], BinOp(atm1, Sub(), atm2)):
                arg1 = self.select_arg(atm1)
                arg2 = self.select_arg(atm2)
                var = Variable(name)

                if arg1 == var:
                    return [
                        Instr("subq", [arg2, var]),
                    ]
                elif arg2 == var:
                    return [
                        Instr("subq", [arg1, var]),
                    ]
                else:
                    return [
                        Instr("movq", [arg1, var]),
                        Instr("subq", [arg2, var]),
                    ]

            case Assign([Name(name)], UnaryOp(USub(), atm)):
                arg = self.select_arg(atm)
                var = Variable(name)
                return [
                    Instr("movq", [arg, var]),
                    Instr("negq", [var]),
                ]
            case Assign([Name(name)], Call(Name("input_int"), [])):
                return [
                    Callq("read_int", 0),
                    Instr("movq", [Reg("rax"), Variable(name)]),
                ]
            case Assign([Name(name)], Constant(c)):
                return [
                    Instr("movq", [Immediate(c), Variable(name)])
                ]
            case Assign([Name(name1)], Name(name2)):
                return [
                    Instr("movq", [Variable(name2), Variable(name1)])
                ]

            case Expr(Call(Name("print"), [exp])):
                match exp:
                    case Constant(c):
                        return [
                            Instr("movq", [Immediate(c), Reg("rdi")]),
                            Callq("print_int", 1),
                        ]
                    case Name(var):
                        return [
                            Instr("movq", [Variable(var), Reg("rdi")]),
                            Callq("print_int", 1),
                        ]
            case _:
                raise RuntimeError(f"Unable to convert statement {
                    s} to instruction")

    def select_instructions(self, p: Module) -> X86Program:
        instructions = []

        for s in p.body:
            instructions += self.select_stmt(s)

        return X86Program({"main": instructions})

    ################
    # Assign Homes #
    ################

    def assign_homes_arg(self, a: arg, home: dict[Variable, arg]) -> arg:
        match a:
            case Variable(name):
                if a in home:
                    return home[a]
                else:
                    self.stack_frame += 8
                    home[a] = Deref("rbp", -self.stack_frame)
                    return home[a]
        return a

    def assign_homes_instr(self, i: instr, home: dict[Variable, arg]) -> instr:
        match i:
            case Instr(s, [a1, a2]):
                return Instr(s, [
                    self.assign_homes_arg(a1, home),
                    self.assign_homes_arg(a2, home)
                ])
            case Instr(s, [a]):
                return Instr(s, [
                    self.assign_homes_arg(a, home),
                ])
        return i

    def assign_homes_instrs(
        self, ss: list[instr], home: dict[Variable, arg]
    ) -> list[instr]:
        new_instructions: list[instr] = []
        for ins in ss:
            new_instructions.append(self.assign_homes_instr(ins, home))
        return new_instructions

    def assign_homes(self, p: X86Program) -> X86Program:
        name_table: dict[Variable, arg] = {}
        new_program: dict[str, list[instr]] = {}
        for f in p.body:
            new_program[f] = self.assign_homes_instrs(
                p.body[f], name_table)

        if self.stack_frame % 16 != 0:
            self.stack_frame += 16 - self.stack_frame % 16

        return X86Program(new_program)

    ######################
    # Patch Instructions #
    ######################

    def patch_instr(self, i: instr) -> list[instr]:
        match i:
            case Instr(s, [a1, a2]):
                match a1:
                    case Deref(_):
                        return [
                            Instr("movq", [a1, Reg("rax")]),
                            Instr(s, [Reg("rax"), a2]),
                        ]
            case Instr(s, [a]):
                match a:
                    case Deref(_):
                        return [
                            Instr("movq", [a, Reg("rax")]),
                            Instr(s, [Reg("rax")]),
                            Instr("movq", [Reg("rax"), a]),
                        ]
        return [i]

    def patch_instrs(self, instrs: list[instr]) -> list[instr]:
        new_instructions: list[instr] = []
        for ins in instrs:
            new_instructions += self.patch_instr(ins)
        return new_instructions

    def patch_instructions(self, p: X86Program) -> X86Program:
        new_program: dict[str, list[instr]] = {}
        for f in p.body:
            new_program[f] = self.patch_instrs(p.body[f])
        return X86Program(new_program)

    ############################################################################
    # Prelude & Conclusion
    ############################################################################

    def prelude_and_conclusion(self, p: X86Program) -> X86Program:
        new_program: dict[str, list[instr]] = []

        for f in p.body:
            prelude = [
                Instr("pushq", [Reg("rbp")]),
                Instr("movq", [Reg("rsp"), Reg("rbp")]),
                Instr("subq", [Immediate(self.stack_frame), Reg("rsp")]),
            ]

            conclusion = [
                Instr("addq", [Immediate(self.stack_frame), Reg("rsp")]),
                Instr("popq", [Reg("rbp")]),
                Instr("retq", [])
            ]

            new_program += prelude + p.body[f] + conclusion

        return X86Program(new_program)

    ##################################################
    # Compiler
    ##################################################

    def compile(self, s: str, logging=False) -> X86Program:
        compiler_passes = {
            "remove complex operands": self.remove_complex_operands,
            "select instructions": self.select_instructions,
            "assign homes": self.assign_homes,
            "patch instructions": self.patch_instructions,
            "prelude & conclusion": self.prelude_and_conclusion,
        }

        current_program = parse(s)

        if logging == True:
            print()
            print("==================================================")
            print(" Input program")
            print("==================================================")
            print()
            print(s)

        for pass_name, pass_fn in compiler_passes.items():
            current_program = pass_fn(current_program)

            if logging == True:
                print()
                print("==================================================")
                print(f" Output of pass: {pass_name}")
                print("==================================================")
                print()
                print(current_program)

        return current_program


##################################################
# Execute
##################################################

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python compiler.py <source filename>")
    else:
        file_name = sys.argv[1]
        with open(file_name) as f:
            print(f"Compiling program {file_name}...")

            try:
                program = f.read()
                compiler = Compiler()
                x86_program = compiler.compile(program, logging=True)

                with open(file_name + ".s", "w") as output_file:
                    output_file.write(str(x86_program))

            except:
                print(
                    "Error during compilation! **************************************************"
                )
                import traceback

                traceback.print_exception(*sys.exc_info())
