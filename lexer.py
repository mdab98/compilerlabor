from lexererror import *
from tokens import *

class Lexer:
    def __init__(self,input):
        self.pos = 0
        #nice cheat to cleanse the input
        self.text = input.replace(" ", "").replace("\t","").replace("\n","")
        self.current_sym = self.text[self.pos]

    ####################################
    ### Automaton Control
    ####################################

    def move(self):
        '''Moves the head one position, if possible.'''

        if self.pos+1 < len(self.text):
            self.pos+=1
            while self.text[self.pos] == ' ' or self.text[self.pos] == '\t' or self.text[self.pos] == '\n':
                self.pos+=1

            self.current_sym = self.text[self.pos]
        else:
            self.current_sym = None
    def peek(self):
        '''Returns next char without moving, if possible.'''

        if self.pos+1 < len(self.text):
            return self.text[self.pos+1]
        else:
            return None

    
    ####################################
    ### Token implementation
    ####################################
        
    def num(self):
        '''Matches (maxmatch) and returns NUM-tokens.'''
        value = ''
        floater = False
        leadingZero = False
        trailingZero = False
        distance = 0
        #pre comma loop
        while not floater and self.current_sym is not None and (self.current_sym.isdigit() or self.current_sym == '.'):
            if leadingZero and self.current_sym != '.':
                raise LexerError("Leading zero in a number", self)
            if distance == 0 and self.current_sym == '0':
                leadingZero = True
            if self.current_sym == '.':
                floater = True
            value += self.current_sym
            distance += 1
            self.move()
        #post comma loop

        distance = 0
        while floater and self.current_sym is not None and self.current_sym.isdigit():
            if self.current_sym == '0':
                trailingZero = True
            else: trailingZero = False
            value += self.current_sym
            distance += 1
            self.move()
        if distance == 0 and floater:
            raise LexerError("expected a number, float with no digits after comma", self)
        if trailingZero:
            raise LexerError("expected a non-zero token, trailing zero", self)
        if floater:
            return Token(FLOAT,value)
        return Token(NUM,value)
    def star(self):
        if self.peek() == '*':
            self.move()
            return Token(POW)
        return Token(MULT)

        
    ####################################
    ### main
    ####################################

    def lex(self):
        '''Scans the input symbolwise and returns a list of matched tokens.'''
        token_list = []

        while self.current_sym is not None:

            match self.current_sym:
                case '0'|'1'|'2'|'3'|'4'|'5'|'6'|'7'|'8'|'9':
                    token_list.append(self.num())
                case '+':
                    token_list.append(Token(ADD))
                    self.move()
                case '-':
                    token_list.append(Token(USUB))
                    self.move()
                case '*':
                    #token_list.append(Token(MULT))
                    token_list.append(self.star())
                    self.move()
                case '(':
                    token_list.append(Token(LPAR))
                    self.move()
                case ')':
                    token_list.append(Token(RPAR))
                    self.move()
                case _:
                    raise SyntaxError('Unexpected Token!')
        
        token_list.append(Token(EOF))

        return token_list

if __name__ == '__main__':
    print(Lexer('0.5').lex())


"""
    if expr then if expr then other else other end

"""
