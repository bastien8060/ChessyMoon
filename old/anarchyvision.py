# Anarchy chess engine
# Chess Engine variant
# Author: Bastien Saidi

# Pieces: Pawn, Knight, Bishop, Rook, Queen, King, Knook (C)

import xxhash
import random
import time
import sys
import os

from movegenerator import MoveGenerator

# Constants
WHITE = 1
BLACK = 0
DEFAULT_BOARD = 'RNBQKBNR/PPPPPPPP/8/8/8/8/pppppppp/rnbqkbnr'

# Utils
def idx_to_algebraic(idx:int) -> str:
    return chr(ord('a') + idx % 8) + str(idx // 8 + 1)

def algebraic_to_idx(algebraic) -> int:
    return (int(algebraic[1]) - 1) * 8 + ord(algebraic[0]) - ord('a')

class Piece:
    def __init__(self, piece = ''):
        self.piece = piece.lower()
        self.color = WHITE if piece.isupper() else BLACK

    @property
    def empty(self):
        return not self.piece
    
    def __str__(self):
        if self.empty:
            return '.'
        return self.piece.upper() if self.color == WHITE else self.piece.lower()
        

class Board:
    def __init__(self, cfg = {}, fen = None):
        self.matrix = [Piece()] * 64
        self.turn = cfg.get('turn', WHITE)
        self.w_king = -1
        self.b_king = -1

        if fen:
            self.set_fen(fen)

    def move(self, src, dst):
        if type(src) == str:
            src = algebraic_to_idx(src)

        if type(dst) == str:
            dst = algebraic_to_idx(dst)

        self.matrix[dst] = self.matrix[src]
        self.matrix[src] = Piece()

    def set_fen(self, fen):
        idx = 0
        for char in fen:
            if char == '/':
                continue
            if char.isdigit():
                idx += int(char)
                continue
            row = 7 - idx // 8
            col = idx % 8
            self.matrix[row*8 + col] = Piece(char)
            if char == 'k':
                self.b_king = row*8 + col
            elif char == 'K':
                self.w_king = row*8 + col
            idx += 1

    @property
    def fen(self):
        fen = ''
        for i in range(8):
            empty = 0
            for j in range(8):
                piece = self.matrix[i * 8 + j]
                if piece.empty:
                    empty += 1
                else:
                    if empty:
                        fen += str(empty)
                        empty = 0
                    fen += str(piece)
            if empty:
                fen += str(empty)
            fen += '/'
        return fen[:-1]
    
    def __str__(self):
        s = ''
        for i in range(7, -1, -1):
            for j in range(8):
                s += str(self.matrix[i * 8 + j]) + ' '
            s += '\n'
        return s

                
        
        
    



        
