from lexer import *
class LexerError(Exception):
    def __init__(self, msg, lexer: Lexer):
        self.msg = msg
        self.pos = lexer.pos
        self.text = lexer.text
        self.message = f"Lexer error at pos:{self.pos} in {self.text}: {self.msg}"
        super().__init__(self.message)

