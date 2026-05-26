	.globl main
main:
    pushq %rbp
    pushq %rbx
    pushq %r12
    pushq %r13
    pushq %r14
    pushq %r15
    movq %rsp, %rbp
    subq $0, %rsp
    movq $5, %rcx
    movq $5, %rdx
    addq $5, %rdx
    movq %rdx, %rcx
    movq %rcx, %rdx
    addq %rcx, %rdx
    callq read_int
    movq %rax, %rcx
    movq %rcx, %rcx
    movq %rcx, %rdi
    callq print_int
    movq %rdx, %rcx
    addq $0, %rsp
    popq %r15
    popq %r14
    popq %r13
    popq %r12
    popq %rbx
    popq %rbp
    retq 

