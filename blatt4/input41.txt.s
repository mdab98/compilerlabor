	.globl main
main:
    pushq %rbp
    movq %rsp, %rbp
    subq $0, %rsp
    movq $1, %rcx
    movq $42, %rdx
    movq %rcx, %rcx
    addq $7, %rcx
    movq %rcx, %rcx
    movq %rcx, %rsi
    addq %rdx, %rsi
    movq %rcx, %rcx
    negq %rcx
    addq %rcx, %rsi
    movq %rsi, %rdi
    callq print_int
    addq $0, %rsp
    popq %rbp
    retq 

