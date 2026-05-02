from tokens import *
import lexer

class Parser:
    def __init__(self, input: list[Token]) -> None:
        self.input = input
        self.current_pos = 0
        self.current_token = self.input[self.current_pos]

    ###########################
    #### parser control
    ###########################

    def read_tok(self):
        self.current_pos += 1
        self.current_token = self.input[self.current_pos]

    def reset_pos(self, pos: int):
        self.current_pos = pos
        self.current_token = self.input[self.current_pos]

    def expect(self, type: str) -> bool:
        if self.current_token.type == type:
            self.read_tok()
            return True
        else:
            return False
        
    ########################
    ### grammar
    ########################

    def expr(self):
        pos = self.current_pos
        if self.term() and self.expect('ADD') and self.expr():
            return True
        self.reset_pos(pos)

        if self.term():
            return True
        self.reset_pos(pos)

    def term(self):
        pos = self.current_pos
        if self.factor() and self.expect('MULT') and self.term():
            return True
        self.reset_pos(pos)#important line
        if self.factor() and self.expect('POW') and self.term():
            return True
        self.reset_pos(pos)

        if self.factor():
            return True
        self.reset_pos(pos)

    def factor(self):
        pos = self.current_pos
        if self.expect('USUB') and self.usubt():
            return True
        self.reset_pos(pos)

        if self.usubt():
            return True
        self.reset_pos(pos)

        #
    def usubt(self):
        pos = self.current_pos
        if self.expect('NUM'):
            return True
        if self.expect('FLOAT'):
            return True
        self.reset_pos(pos)

        #start -> expr EOF
    def parse(self):
        if self.expr() and self.current_token.type == 'EOF':
            return True
        else:
            return False
        


if __name__ == '__main__':
    token_list = lexer.Lexer('1+1**2.03+3.01').lex()
    print(token_list)
    out = Parser(token_list).parse()
    print(out)


