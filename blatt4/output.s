	.globl main
main:
    pushq %rbp
    movq %rsp, %rbp
    subq $24, %rsp
    movq $6, -8(%rbp)
    movq -8(%rbp), %rax
    movq %rax, -16(%rbp)
    subq $2, -16(%rbp)
    movq $2, -24(%rbp)
    movq -24(%rbp), %rax
    negq %rax
    movq %rax, -24(%rbp)
    movq -24(%rbp), %rax
    addq %rax, -16(%rbp)
    movq -16(%rbp), %rax
    movq %rax, -16(%rbp)
    subq $2, -16(%rbp)
    movq -16(%rbp), %rax
    movq %rax, %rdi
    callq print_int
    addq $24, %rsp
    popq %rbp
    retq 

