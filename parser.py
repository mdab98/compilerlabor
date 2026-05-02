from tokens import *
import lexer

class Parser:
    def __init__(self, input: list[Token]) -> None:
        self.input = input
        self.current_pos = 0
        self.current_token = self.input[self.current_pos]
        self.cache: Dict[Tuple[int, Callable], LeafNode] = {}

    ###########################
    #### parser control
    ###########################

    def read_tok(self):
        self.current_pos += 1
        self.current_token = self.input[self.current_pos]

    def reset_pos(self, pos: int):
        self.current_pos = pos
        self.current_token = self.input[self.current_pos]

    def token_match(self, type: str) -> bool:
        if self.current_token.type == type:
            return True
        else:
            return False
    def expect(self, type: str) -> bool:
        if self.current_token.type == type:
            self.read_tok()
            return True
        else:
            return False
    def invoke(self, where, what):
        key = (where, what)
        if key in self.cache:
            return self.cache[key]
        else:
            res = what()
            self.cache[key] = res
            return res
        
    ########################
    ### grammar
    ########################

    def expr(self):
        pos = self.current_pos
        #res = self.term()
        res = self.invoke(pos, self.term)
        res2 = (False, False)
        exp = False
        if res[0]:
            exp = self.expect('ADD')
            if exp:
                res2 = self.invoke(self.current_pos, self.expr)
        if res[0] and exp and res2[0]:
            return (True, LeafNode(Token('ADD'), res[1], res2[1]))
        self.reset_pos(pos)

        res = self.term()
        if res[0]:
            return (True, res[1])
        self.reset_pos(pos)
        return (False, False)

    def term(self):
        pos = self.current_pos
        res = self.factor()
        res2 = (False, False)
        exp = False
        if res[0]:
            exp = self.expect('MULT')
            if exp:
                res2 = self.term()
        if res[0] and exp and res2[0]:
            return (True, LeafNode(Token('MULT'), res[1], res2[1]))
        self.reset_pos(pos)#important line


        res = self.factor()
        res2 = (False, False)
        exp = False
        if res[0]:
            exp = self.expect('POW')
            if exp:
                res2 = self.term()
        if res[0] and exp and res2[0]:
            return (True, LeafNode(Token('POW'), res[1], res2[1]))
        self.reset_pos(pos)

        res = self.factor()
        if res[0]:
            return (True, res[1])
        self.reset_pos(pos)
        return (False, False)

    def factor(self):
        pos = self.current_pos
        tok = self.current_token

        res = self.usubt()
        if res[0]:
            return (True, res[1])
        self.reset_pos(pos)
        res = self.expect('USUB')
        res2 = self.usubt()
        if res and res2[0]:
            return (True, LeafNode(tok, res2[1]))
        self.reset_pos(pos)
        return (False, False)

    def usubt(self):
        pos = self.current_pos
        tok = self.current_token
        if self.expect('NUM'):
            return (True, LeafNode(tok))
        self.reset_pos(pos)
        if self.expect('FLOAT'):
            return (True, LeafNode(tok))
        self.reset_pos(pos)
        return (False, False)

        #start -> expr EOF
    def parse(self):
        res = self.expr()
        if res[0] and self.current_token.type == 'EOF':
            return LeafNode(res[1], LeafNode(Token('EOF')))
        else:
            return (False, False)
        
class LeafNode:
    def __init__(self, metok: Token, tok: LeafNode = None, tok2: LeafNode = None):
        self.metok = metok
        self.tok = tok
        self.tok2 = tok2
    def __repr__old(self):
        str = "Me: " + self.metok.__repr__()
        str2 = ""
        str3 = ""
        if self.tok is not None:
            if self.tok.metok is not None:
                str += " Child 1: " + self.tok.metok.__repr__()
            str2 = "" + self.tok.__repr__()
        if self.tok2 is not None:
            str += " Child 2: " + self.tok2.metok.__repr__() 
            str3 = "" + self.tok2.__repr__()
        return str + "\n" + str2 + str3
    def __repr__(self):
        if self.tok is None and self.tok2 is None:
            return ""
        str = "Me: " + self.metok.__repr__() + "\n"
        str2 = ""
        str3 = ""
        if self.tok is not None:
            str += self.tok.metok.__repr__() + "\t"
            str2 = "" + self.tok.__repr__()
        if self.tok2 is not None:
            str += self.tok2.metok.__repr__() + "\t"
            str3 = "" + self.tok2.__repr__()
        return str + "\n" + str2 + str3


if __name__ == '__main__':
    token_list = lexer.Lexer('1+1**2.03+3.01+3.001*50').lex()
    print(token_list)
    out = Parser(token_list).parse()

    print(out)


