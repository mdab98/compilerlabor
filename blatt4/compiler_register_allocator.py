from graph import UndirectedAdjList
from ast import *
from x86_ast import *
from utils import *
import copy
from compiler_var import Compiler

Binding = tuple[Name, expr]
Temporaries = list[Binding]

get_fresh_tmp = lambda: generate_name('tmp')



caller_saved_registers: set[location] = set(
    [
        Reg('rax'),
        Reg('rcx'),
        Reg('rdx'),
        Reg('rsi'),
        Reg('rdi'),
        Reg('r8'),
        Reg('r9'),
        Reg('r10'),
        Reg('r11'),
    ]
)

callee_saved_registers: set[location] = set(
    [Reg('rsp'), Reg('rbp'), Reg('rbx'), Reg('r12'), Reg('r13'), Reg('r14'), Reg('r15')]
)


registers_for_coloring = [
    Reg("rcx"),
    Reg("rdx"),
    Reg("rsi"),
    Reg("rdi"),
    Reg("r8"),
    Reg("r9"),
    Reg("r10"),
    Reg("rbx"),
    Reg("r12"),
    Reg("r13"),
    Reg("r14"),
]

def get_loc_from_arg(a: arg) -> set[location]:
    match a:
        case Reg(_):
            return set([a])
        case Variable(_):
            return set([a])
        case ByteReg(_):
            return set([a])
        case _:
            return set([])


class CompilerReg(Compiler):
    def __init__(self):
        self.stack_size = 0
        self.used_callees = set()
        self.temporary_counter = 0
        self.stack_frame = 0

    ############################################################################
    # Remove Complex Operands
    ############################################################################

    #super covers 

    ############################################################################
    # Select Instructions
    ############################################################################

    #super covers

    ###########################################################################
    # Uncover Live
    ###########################################################################

    def read_vars(self, i: instr) -> set[location]:
        #check for callq stuff
        match i:
            case Instr("movq", args):
                return get_loc_from_arg(args[0])
            case Instr("addq", args):
                return get_loc_from_arg(args[0]) | get_loc_from_arg(args[1]) 
            case Instr("subq", args):
                return get_loc_from_arg(args[0]) | get_loc_from_arg(args[1]) 
            case Instr("negq", args):
                return get_loc_from_arg(args[0]) 
            case Callq("print_int", 1):
                return set()
                #return {Reg("rdi")}
            case Callq("read_int", 0):
                return set()
            case _: 
                raise Exception(f"Nothing matched in reading for {i}")
        return set()

    def write_vars(self, i: instr) -> set[location]:
        #check for callq stuff add all callee_saved_registers
        match i:
            case Instr("movq", args):
                return get_loc_from_arg(args[1]) 
            case Instr("addq", args):
                return get_loc_from_arg(args[1])
            case Instr("subq", args):
                return get_loc_from_arg(args[1])
            case Instr("negq", args):
                return get_loc_from_arg(args[0])
            case Callq("print_int", 1):
                return caller_saved_registers
            case Callq("read_int", 0):
                return caller_saved_registers
            case _: 
                raise Exception(f"Nothing matched in writing for {i}")

        return set()

    def uncover_live(self, p: X86Program) -> dict[instr, set[location]]:
        
        # VORGEGEBEN
        
        result = {}

        l_after = set()
        l_before = set()

        # ungodly traversal due to how we define an X86 program
        for i in reversed(p.body):
            for i in reversed(p.body[i]):
                result[i] = l_after

                l_before = (l_after - self.write_vars(i)) | self.read_vars(i)
                l_after = l_before

        return result
        
        

    ############################################################################
    # Build Interference
    ############################################################################

    def build_interference(
        self, p: X86Program, live_after: dict[instr, set[location]]
    ) -> UndirectedAdjList:


        ### Hilfe zur Benutzung der Graph-Klasse: ###
        # hier wird zunächst ein Graph erzeugt, welcher alle locations als Knoten beinhaltet
        # dies kann so beibehalten werden, lässt sich aber bei einer entsprechenden Lösung auch vereinfachen 

        # label wird nur für die Anzeige der Graphen benötigt, da diese immer strings als Knotenlabel erwartet
        label = lambda v: v.id if isinstance(v, Reg) else str(v)
        graph = UndirectedAdjList(vertex_label=label)

        for (_, vs) in live_after.items():
            #maybe add code to not include registers in the graph
            for v in vs:
                graph.add_vertex(v)

        ######
        for (inst, vs) in reversed(live_after.items()):
            #print(f"{inst}\n life_after {vs}")
            match inst:
                case Instr("movq", args):
                    s = next(iter(get_loc_from_arg(args[0])), None)
                    d = next(iter(get_loc_from_arg(args[1])), None)
                    if d:
                        for v in vs:
                            if v != d and v != s:
                                graph.add_edge(d, v)
                case Instr("addq", args):
                    d = next(iter(get_loc_from_arg(args[1])), None)
                    if d:
                        for v in vs:
                            if v != d:
                                graph.add_edge(d, v)
                case Instr("subq", args):
                    d = next(iter(get_loc_from_arg(args[1])), None)
                    if d:
                        for v in vs:
                            if v != d:
                                graph.add_edge(d, v)
                case Instr("negq", args):
                    d = next(iter(get_loc_from_arg(args[0])), None)
                    if d:
                        for v in vs:
                            if v != d:
                                graph.add_edge(d, v)
                case Callq("print_int", 1):
                    for d in caller_saved_registers:
                        for v in vs:
                            if v != d:
                                graph.add_edge(d, v)
                case Callq("read_int", 0):
                    for d in caller_saved_registers:
                        for v in vs:
                            if v != d:
                                graph.add_edge(d, v)

        #graph.show().view()
        return graph

    ############################################################################
    # Allocate Registers
    ############################################################################

    def color_graph(
        self, graph: UndirectedAdjList, colors: list[location]
    ) -> dict[location, arg]:
        # YOUR CODE HERE
        mapping = dict()
        k = len(colors)
        stack = list()
        dc = copy.deepcopy(graph)

        while graph.vertices():
            for node in graph.vertices():
                print(node)
                if (len(graph.adjacent(node)) < k):
                    stack.append((node, False))
                    graph.remove_vertex(node)
            #here comes spilling
            for node in graph.vertices():
                stack.append((node, True))
                graph.remove_vertex(node)


        while stack:
            node = stack.pop()



        raise Exception('not implemented')
        for node in graph.vertices():
            print(node)
            if (len(graph.adjacent(node)) < k):
                stack.append((node, False))
        while stack:
            print(stack.pop())

        raise Exception('not implemented')

    ############################################################################
    # Assign Homes
    ############################################################################

    def assign_homes_arg(self, a: arg, home: dict[Variable, arg]) -> arg:
        # YOUR CODE HERE
        raise Exception('not implemented')

    def assign_homes_instr(self, i: instr, home: dict[Variable, arg]) -> instr:
        # YOUR CODE HERE
        raise Exception('not implemented')

    def assign_homes_instrs(
        self, ss: list[instr], home: dict[Variable, arg]
    ) -> list[instr]:
        # YOUR CODE HERE
        raise Exception('not implemented')

    def assign_homes(self, p: X86Program) -> X86Program:
        # YOUR CODE HERE
        live_after = self.uncover_live(p)
        graph = self.build_interference(p, live_after)

        mapping = self.color_graph(graph, registers_for_coloring)

        print("this is as far as she goes I'm afraid")
        raise Exception('not implemented')

    ############################################################################
    # Patch Instructions
    ############################################################################

    def patch_instr(self, i: instr) -> list[instr]:
        # YOUR CODE HERE
        raise Exception('not implemented')

    def patch_instrs(self, instrs: list[instr]) -> list[instr]:
        # YOUR CODE HERE
        raise Exception('not implemented')

    def patch_instructions(self, p: X86Program) -> X86Program:
        # YOUR CODE HERE
        raise Exception('not implemented')

    ############################################################################
    # Prelude & Conclusion
    ############################################################################

    def prelude_and_conclusion(self, p: X86Program) -> X86Program:
        # YOUR CODE HERE
        raise Exception('not implemented')

    ##################################################
    # Compiler
    ##################################################

    def compile(self, s: str, logging=False) -> X86Program:
        compiler_passes = {
            'remove complex operands': self.remove_complex_operands,
            'select instructions': self.select_instructions,
            'assign homes': self.assign_homes,
        }
        """
            'patch instructions': self.patch_instructions,
            'prelude & conclusion': self.prelude_and_conclusion,
        }
        """

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

def produce44() -> X86Program:
    #testing program from the book with easy to check solutions
    list_instr = list()
    list_instr.append(Instr("movq", (Immediate(1), Variable("v"))))
    list_instr.append(Instr("movq", (Immediate(42), Variable("w"))))
    list_instr.append(Instr("movq", (Variable("v"), Variable("x"))))
    list_instr.append(Instr("addq", (Immediate(7), Variable("x"))))
    list_instr.append(Instr("movq", (Variable("x"), Variable("y"))))
    list_instr.append(Instr("movq", (Variable("x"), Variable("z"))))
    list_instr.append(Instr("addq", (Variable("w"), Variable("z"))))

    list_instr.append(Instr("movq", (Variable("y"), Variable("tmp_0"))))
    list_instr.append(Instr("negq", [Variable("tmp_0")]))
    list_instr.append(Instr("movq", (Variable("z"), Variable("tmp_1"))))
    list_instr.append(Instr("addq", (Variable("tmp_0"), Variable("tmp_1"))))
    list_instr.append(Instr("movq", (Variable("tmp_1"), Reg("rdi"))))
    list_instr.append(Callq("print_int", 1))
    dc = dict()
    dc["main"] = list_instr
    book_example = X86Program(dc)


    return book_example



if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python compiler_register_allocator.py <source filename>')
    else:
        book_example = produce44()

        print(book_example)

        compiler = CompilerReg()
        lafter = compiler.uncover_live(book_example)
        compiler.build_interference(book_example, lafter)
        compiler.assign_homes(book_example)
        



        exit()
        file_name = sys.argv[1]
        with open(file_name) as f:
            print(f'Compiling program {file_name}...')

            try:
                program = f.read()
                compiler = CompilerReg()
                x86_program = compiler.compile(program, logging=True)

                with open(file_name + '.s', 'w') as output_file:
                    output_file.write(str(x86_program))

            except:
                print(
                    'Error during compilation! **************************************************'
                )
                import traceback

                traceback.print_exception(*sys.exc_info())
