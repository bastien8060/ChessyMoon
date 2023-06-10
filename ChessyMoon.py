import json
import math
import random
import time

from StaticAnalysisHelper import PositionTableWeights

DEBUG = True

WHITE = 1
BLACK = 0

WIN = 1
LOSS = 0
DRAW = -1

kingWt = 20000
queenWt = 900
rookWt = 500
knightWt = 320
bishopWt = 330
pawnWt = 100
knookWt = 650

nodes = 0

positionTableWeightFactor = 0.8

mobilityWt = 3.5

piece_point_chart = {
    'p': 1,
    'k': 1000,
    'q': 8,
    'r': 5,
    'b': 3,
    'n': 3,
    'ñ': 6.5,
}


class ResultDebug:
    def __init__(self, debugParams=None):
        if debugParams is not None:
            for key, value in debugParams.items():
                setattr(self, key, value)

class OpeningBook:
    def __init__(self, src="./opening_book.json") -> None:
        self.src = src
        with open(src, 'r') as file: 
            self.variations = json.loads(file.read())

    def count_variation(self, tree, c=0):
        for key in tree:
            if isinstance(tree[key], dict):
                # calls repeatedly
                c = self.count(tree[key], c + 1)
            else:
                c += 1
        return c

class Piece:
    def __init__(self, pieceNotation:str=None) -> None:
        if pieceNotation:
            self.piece:  str  = pieceNotation.lower()
            self.color:  bool = pieceNotation.isupper()
            self.exists: bool = True
        else:
            self.exists = False

    def __str__(self) -> str:
        if self.exists:     
            if self.color:
                return self.piece.upper()
            return self.piece.lower()
        return ""
    
    def __bool__(self):
        return self.exists 
    
    def points(self):
        return piece_point_chart[self.piece]

class Square:
    def __str__(self) -> str:
        return self.algebraic()

    def __repr__(self) -> str:
        return self.algebraic()

    def __init__(self, idx:int=None, col:int=None, row:int=None, algebraic:str=None) -> None:
        if not (idx is None):
            self.idx = idx
            self.row = idx // 8
            self.col = idx %  8

        elif algebraic:
            self.algebraic_str = algebraic.lower()
            self.row = 7 - (int(algebraic[1]) - 1)
            self.col = ord(algebraic[0]) - 97
            self.idx = (8 * (self.row)) + self.col

        else:
            self.col = col
            self.row = row
            self.idx = (8 * (row)) + col

    def algebraic(self):
        if not hasattr(self,"algebraic_str"):
            self.algebraic_str = chr(self.col + 97) + str(8 - self.row)
        return self.algebraic_str

class Squares:
    def __init__(self,  idx=None, col=None, row=None, algebraic=None) -> None:
        squares = []
        if idx:
            for _idx in idx:
                squares.append(Square(idx=_idx))
        elif algebraic:
            for _algebraic in algebraic:
                squares.append(Square(algebraic=_algebraic))
        else:
            for _col, _row in zip(col, row):
                squares.append(Square(col=_col, row=_row))
        self.squares = squares

    def fetch(self) -> list[Square]:
         return self.squares

class Position:
    def __init__(self, fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", matrix=None) -> None:
        self.fen = fen
        self.fen_calc = None
        self.turn  : bool   = WHITE
        self.w_king: Square = Square(idx=0)
        self.b_king: Square = Square(idx=0)
        if not matrix:
            self.matrix = self.fenLoader()
        else:
            self.matrix = matrix

    def deep_copy(self):
        position = Position(matrix=self.matrix.copy())

        position.fen = self.fen
        position.fen_calc = self.fen_calc
        position.turn = self.turn
        position.w_king = self.w_king
        position.b_king = self.b_king

        return position

    def get_fen(self, simplify=False):
        turn = self.turn
        if not self.fen_calc:
            matrix = self.matrix
            fen = ''
            for row in range(0,8):
                emptySquares = 0
                for col in range(0,8):
                    piece = matrix[ (8 * (row)) + col ]
                    if not piece:
                        emptySquares += 1
                    else:
                        if emptySquares:
                            fen += str(emptySquares)
                            emptySquares = 0
                        fen += str(piece)
                if emptySquares:
                    fen += str(emptySquares)
                if row != 7:
                    fen += '/'
            self.fen = fen
            self.fen_calc = fen
        else:
            fen = self.fen_calc

        if simplify:
            marker = 'w' if turn else 'b'
            fen = fen + f" {marker}"
        else:
            marker = 'w' if turn else 'b'
            fen = fen + f" {marker} - - 0 1"

        return fen

    def __str__(self):
        visual = ""
        col, row = -1,-1
        for row in range(0,8):
            for col in range(0,8):
                visual += "  "
                idx = (8 * (row)) + col
                piece = self.matrix[idx]
                col += 1
                if piece:
                    visual += str(piece)
                    continue
                visual += " "
            row += 1
            visual += "\n"
        return visual
    
    def get_pieces_by_color(self, color:bool):
        matrix = self.matrix
        squares: list[Square] = []
        this = self

        for idx in range (0,63):
            if matrix[idx]:
                if matrix[idx].color == color:
                    square = Square(idx=idx)
                    rays = Rays(this,square).squares
                    if rays:
                        squares.append(square)
        return squares


    def fenLoader(self) -> list[Piece]:
        position = [None] * 64
        idx = 0

        for char in self.fen:
            if idx >= 64:
                if char == 'w':
                    self.turn = WHITE
                    break
                if char == 'b':
                    self.turn = BLACK
                    break
                continue
            if char == '/':
                continue
            if char.isnumeric():
                idx += int(char)
                continue
            if char.lower() == 'k':
                if char.isupper():
                    self.w_king = Square(idx=idx)
                else:
                    self.b_king = Square(idx=idx)
            position[idx] = Piece(char)
            idx += 1
        return position
    
class Move:
    def __init__(self, position:Position, squares:tuple[Square, Square], move_type="none") -> str:
        self.src = squares[0]
        self.dst = squares[1]
        self.move_type = move_type

        self.notation = self.render_notation(position.matrix[self.src.idx])

    def render_notation(self, piece:Piece) -> str:
        functions = {
            "pawn_move": (self.pawn_notation, "move"),
            "pawn_capture": (self.pawn_notation, "capture"),
            "knight_move": (self.knight_notation, "move"),
            "knight_capture": (self.knight_notation, "capture"),
            "bishop_move": (self.bishop_notation, "move"),
            "bishop_capture": (self.bishop_notation, "capture"),
            "rook_move": (self.rook_notation, "move"),
            "rook_capture": (self.rook_notation, "capture"),
            "queen_move": (self.queen_notation, "move"),
            "queen_capture": (self.queen_notation, "capture"),
            "king_move": (self.king_notation, "move"),
            "king_capture": (self.king_notation, "capture"),
            
            "knooklear_fusion": (self.knooklear_notation, "fusion"),
            "knooklear_move": (self.knooklear_notation, "move"),
            "knooklear_capture": (self.knooklear_notation, "capture"),
        }

        function, arg = functions.get(self.move_type, (self.default_notation, "none"))

        if function:
            return function(piece, arg)
        
        return self.default_notation(piece, arg)
    
    def default_notation(self, piece:Piece, arg:str) -> str:
        suffix = piece.piece.upper() if piece.piece != 'p' else ''
        return f"{suffix}{self.src}{self.dst}"    

    def __str__(self) -> str:
        pass# to do

class ChessBoard:
    def __str__(self):
        return self.position.__str__()

    def __repr__(self) -> str:
        return self.position.get_fen()

    def __deepcopy__(self, memodict={}):
        position = Position(self.position.get_fen())

        this_position = self.position

        position.fen = this_position.fen
        position.w_king = this_position.w_king
        position.b_king = this_position.b_king
        position.turn = this_position.turn

        board = ChessBoard(position, opening_book=self.opening_book)
        board.turn = self.turn
        board.moves = self.moves
        board.last_position = None
        board.last_move = None
        #board.history = [old for old in self.history]
        #board.history = self.history

        board.position = position

        

        return board

    def __init__(self, position, opening_book:OpeningBook = None) -> None:
        self.position:          Position    = position
        self.turn:              bool        = self.position.turn
        self.moves:             float       = 0
        self.last_position:     Position    = None
        self.last_move:         Move        = None

        if opening_book:
            self.opening_book = opening_book
        else:
            self.opening_book = OpeningBook()

    def get_theory_move(self):
        theory = self.opening_book

        current_fen = self.position.get_fen(simplify=True)

        if current_fen not in theory.variations:
            return None

        possible_moves = theory.variations[current_fen]

        random.shuffle(possible_moves)

        if possible_moves:
            move = possible_moves[0]
            squareFrom = Square(algebraic=move.split(' ')[0])
            squareTo = Square(algebraic=move.split(' ')[1])
            
            child = self.__deepcopy__()
            child.move(squareFrom, squareTo)
            return child
        return None
  
    def get_possible_moves(self, color = None):

        if color is None:
            color = self.turn

        matrix = self.position.matrix

        position = self.position

        fen = position.get_fen(simplify=True) + str(color)
        cached = moveDiscoveryCache.get(fen)

        if cached:
            return cached

        possible_moves: list[tuple[Square, Square]] = []

        for idx in range (0,63):
            piece = matrix[idx]
            if piece:
                if piece.color == color:
                    movable_piece = Square(idx=idx)

                    moves = Rays(position, movable_piece).squares

                    for move in moves:
                        _from = movable_piece
                        _to   = move

                        possible_moves.append((_from, _to))  
            
        #moveDiscoveryCache.add(fen, possible_moves)

        return possible_moves

    def evaluate_position(self) -> float:
        material_count = {
            'K':0,
            'Q':0,
            'N':0,
            'B':0,
            'R':0,
            'P':0,
            'Ñ':0,

            'k':0,
            'q':0,
            'r':0,
            'n':0,
            'b':0,
            'p':0,
            'ñ':0,
        }

        position = self.position

        whitePositionScore, blackPositionScore = 0,0

        for idx, piece in enumerate(position.matrix):
            if not piece:
                continue
            if piece.color:
                whitePositionScore += PositionTableWeights[piece.piece][idx]
            else:
                blackPositionScore += PositionTableWeights[piece.piece][63-idx]
            if str(piece) not in material_count:
                material_count[str(piece)] = 0
            material_count[str(piece)] += 1
        
        materialScore = (queenWt * (material_count['Q']-material_count['q']))
        materialScore += (kingWt * (material_count['K']-material_count['k']))
        materialScore += rookWt  * (material_count['R']-material_count['r'])
        materialScore += knightWt* (material_count['N']-material_count['n'])
        materialScore += bishopWt* (material_count['B']-material_count['b'])
        materialScore += pawnWt  * (material_count['P']-material_count['p'])
        materialScore += knookWt* (material_count['Ñ']-material_count['ñ'])

        positionScore = positionTableWeightFactor * (whitePositionScore - blackPositionScore)

        wMobility = len(self.get_possible_moves(WHITE))
        bMobility = len(self.get_possible_moves(BLACK))

        mobilityScore = mobilityWt * (wMobility-bMobility)

        if position.w_king:
            checkingWhiteKing = 150 if Rays(position, position.w_king,'incheck').squares else 0
        else:
            checkingWhiteKing = -150
        if position.b_king:
            checkingBlackKing = 150 if Rays(position, position.b_king,'incheck').squares else 0
        else:
            checkingBlackKing = -150

        checkingKingScore = checkingWhiteKing - checkingBlackKing

        return (materialScore + mobilityScore + positionScore + checkingKingScore)

    def move(self, squareFrom:Square, squareTo:Square, check_semi_legal=True):
        self.last_position = self.position.deep_copy()
        self.last_move = (squareFrom, squareTo)

        pieceFrom = self.position.matrix[squareFrom.idx]
        pieceTo   = self.position.matrix[squareTo.idx]
        if check_semi_legal:
            if not pieceFrom:
                invalid_move_text = f"Invalid Move ({squareFrom.algebraic()}{squareTo.algebraic()}):"
                raise Exception(f"{invalid_move_text} No pieces on square {squareFrom.algebraic()}")
            
            if pieceFrom.color != self.turn:
                invalid_move_text = f"Invalid Move ({squareFrom.algebraic()}{squareTo.algebraic()}):"
                color_turn = "WHITE" if self.turn else "BLACK"
                raise Exception(f"{invalid_move_text} It is {color_turn}'s turn to play, but {squareFrom.algebraic()} is not a {color_turn} piece.")
            
            if pieceTo:
                if pieceTo.color == pieceFrom.color:
                    invalid_move_text = f"Invalid Move ({squareFrom.algebraic()}{squareTo.algebraic()}):"
                    raise Exception(f"{invalid_move_text} Piece cannot capture a piece of the same color.")

                if pieceTo.piece == 'k':
                    if pieceTo.color == WHITE:
                        self.position.w_king = None
                    else:
                        self.position.b_king = None
            
        #self.history.append(self.deepcopy())
         
        if pieceFrom.piece == 'p' and pieceFrom.color and squareTo.row == 0:
            self.position.matrix[squareFrom.idx].piece = 'q'

        elif pieceFrom.piece == 'p' and not pieceFrom.color and squareTo.row == 7:
            self.position.matrix[squareFrom.idx].piece = 'q'

        if pieceFrom.piece == 'k':
            if pieceFrom.color == WHITE:
                self.position.w_king = squareTo
            else:
                self.position.b_king = squareTo

        self.position.matrix[squareTo.idx] = self.position.matrix[squareFrom.idx]
        self.position.matrix[squareFrom.idx] = None

        self.position.turn = not self.turn
        self.turn = not self.turn
        
        self.moves += 0.5

        self.position.get_fen()

        #self.position.fen = self.position.get_fen()

class RookRays:
    def __init__(self, position:Position, square:Square):
        #self.square = square
        #self.matrix = position.matrix

        self.squares = self.calculateContinuousLines(square, position.matrix, paddings=[(-1, 0), ( 1, 0), ( 0,-1), ( 0, 1)])
    
    def calculateContinuousLines(self, square, matrix, paddings):
        squares:list[Square] = []
        
        piece = matrix[(8 * (square.row)) + square.col]    
        
        for padding in paddings:
            col = square.col
            row = square.row

            idx = (8 * (row)) + col

            for _i in range(8):
                col += padding[0]
                row += padding[1] 
                idx = (8 * (row)) + col
                if  col < 0 or col >= 8 or row < 0 or row >= 8:
                    break
                if matrix[idx]:    
                    if matrix[idx].color == piece.color:
                        break
                    else:
                        squares.append(Square(idx=idx))
                        break
                squares.append(Square(idx=idx))
            
        return squares

class QueenRays:
    def __init__(self, position:Position, square:Square):
        #self.square = square
        #self.matrix = position.matrix
        
        self.squares: list[Square] = self.calculateContinuousLines(square, position.matrix, 
            paddings=[(-1,-1), (-1, 1), ( 1,-1), ( 1, 1), (-1, 0), ( 1, 0), ( 1, 0), ( 0,-1), ( 0, 1)])

    def calculateContinuousLines(self, square, matrix, paddings):
        squares:list[Square] = []

        piece = matrix[(8 * (square.row)) + square.col]

        for padding in paddings:

            col = square.col
            row = square.row
            idx = (8 * (row)) + col
            
            for _i in range(8):
                col += padding[0]
                row += padding[1] 
                idx = (8 * (row)) + col
                if  col < 0 or col >= 8 or row < 0 or row >= 8:
                    break

                if matrix[idx]:    
                    if matrix[idx].color == piece.color:
                        break
                    else:
                        squares.append(Square(idx=idx))
                        break

                squares.append(Square(idx=idx))
            
        return squares

class BishopRays:
    def __init__(self, position:Position, square:Square):
        #self.square = square
        #self.matrix = position.matrix
        
        self.squares = self.calculateContinuousLines(square, position.matrix, paddings=[(-1,-1), (-1, 1), ( 1,-1), ( 1, 1)])

    
    def calculateContinuousLines(self, square, matrix, paddings):
        squares:list[Square] = []

        piece = matrix[(8 * (square.row)) + square.col]

        for padding in paddings:
            col = square.col
            row = square.row
            idx = (8 * (row)) + col

            for _i in range(8):
                col += padding[0]
                row += padding[1] 
                idx = (8 * (row)) + col
                if  col < 0 or col >= 8 or row < 0 or row >= 8:
                    break
                if matrix[idx]:    
                    if matrix[idx].color == piece.color:
                        break
                    else:
                        squares.append(Square(idx=idx))
                        break
                squares.append(Square(idx=idx))
            
        return squares

class KnightRays:
    def __init__(self, position:Position, square:Square):
        self.squares = self.add_vectors(square, position.matrix, [( 1, 2), (-1, 2), ( 1,-2), (-1,-2), ( 2, 1), (-2, 1), ( 2,-1), (-2,-1)] )


    def add_vectors(self, square, matrix, vectors):
        squares = []

        for vector in vectors:
            col = vector[0] + square.col
            row = vector[1] + square.row

            if col < 0 or col >= 8 or row < 0 or row >= 8:
                continue
            
            new_square = Square(col=col, row=row)

            if matrix[new_square.idx]:
                if matrix[square.idx].color == matrix[new_square.idx].color:
                    continue
            
            squares.append(new_square)
        return squares

class KingRays:
    def __init__(self, position:Position, square:Square):
        self.squares = self.add_vectors(square, position.matrix,
         [(-1,-1), (-1, 1), (-1, 0), ( 0,-1), ( 0, 1), ( 1,-1), ( 1, 1), ( 1, 0)])
   

    def add_vectors(self, square, matrix, vectors, debug=False):
        squares = []

        for vector in vectors:
            col = vector[0] + square.col
            row = vector[1] + square.row

            if col < 0 or col >= 8 or row < 0 or row >= 8:
                continue
            
            new_square = Square(col=col, row=row)

            if matrix[new_square.idx]:
                if matrix[square.idx].color == matrix[new_square.idx].color:
                    continue
            
            squares.append(new_square)
        return squares

class PawnRays:
    def __init__(self, position:Position, square:Square):
        piece = position.matrix[square.idx]
        add_vectors = self.add_vectors

        squares: list[Square] = []

        if piece.color == WHITE:
            squares.extend(add_vectors(square, position.matrix, [(-1,-1), ( 1,-1)] , invert_flag=True))
            squares.extend(add_vectors(square, position.matrix, [( 0,-1)] ))
        else:
            squares.extend(add_vectors(square, position.matrix, [( 1, 1), (-1, 1)] , invert_flag=True))
            squares.extend(add_vectors(square, position.matrix, [( 0, 1)] ))

        self.squares = squares

    def add_vectors(self, square, matrix, vectors, invert_flag = False):
        squares = []

        for vector in vectors:
            col = vector[0] + square.col
            row = vector[1] + square.row

            if col < 0 or col >= 8 or row < 0 or row >= 8:
                continue
            
            new_square = Square(col=col, row=row)


            if matrix[new_square.idx]:
                if matrix[new_square.idx].color == matrix[square.idx].color:
                    continue
                if not invert_flag:
                    continue
            else:
                if invert_flag:
                    continue
            
        
            squares.append(new_square)
        return squares

class Rays:
    def __init__(self, position:Position, square:Square, type='move') -> None:
        matrix = position.matrix

        piece = matrix[square.idx]
        
        if type == 'incheck':
            self.squares = KingCheckRays(position, square).squares
        elif piece.piece == 'p':
            if type == 'move' or 'attack':
                self.squares = PawnRays(position, square).squares
        elif piece.piece == 'b':
            self.squares = BishopRays(position, square).squares
        elif piece.piece == 'q':
            self.squares = QueenRays(position, square).squares
        elif piece.piece == 'n':
            self.squares = KnightRays(position, square).squares
        elif piece.piece == 'r':
            self.squares = RookRays(position, square).squares
        elif piece.piece == 'k':
            self.squares = KingRays(position, square).squares
            

class TranspositionCache:
    def __init__(self) -> None:
        self.store = {}

    def add(self, fen, result:tuple[ChessBoard, float]):
        self.store[fen] = result

    def get(self, fen) -> tuple[ChessBoard, float] | None:
        store = self.store
        if fen in store:
            return store[fen]
        return None

class MoveDiscoveryCache:
    def __init__(self) -> None:
        self.store = {}

    def add(self, fen, result:list):
        self.store[fen] = result

    def get(self, fen) -> list | None:
        store = self.store
        if fen in store:
            return store[fen]
        return None

class KingCheckRays:
    def __init__(self, position:Position, square:Square):
        matrix = position.matrix
        piece = matrix[square.idx]

        calculateContinuousLines = self.calculateContinuousLines
        add_vectors = self.add_vectors

        squares: list[Square] = []

        squares.extend(calculateContinuousLines(square, matrix, piece, ['b','q'], paddings=[(-1,-1), (-1, 1), ( 1,-1), ( 1, 1)]))
        squares.extend(calculateContinuousLines(square, matrix, piece, ['r','q'], paddings=[(-1, 0),( 1, 0), ( 0,-1), ( 0, 1)]))

        squares.extend(add_vectors(square, matrix, piece, [( 1, 2),(-1, 2),( 1,-2),(-1,-2),( 2, 1),(-2, 1),( 2,-1),(-2,-1)], ['n'] ))
      

        if piece.color:
            squares.extend(add_vectors(square, matrix, piece, [(-1,-1),( 1,-1)], ['p'] ))
        else:
            squares.extend(add_vectors(square, matrix, piece, [(-1,1),( 1,1)], ['p'] ))


        self.squares = squares

    def add_vectors(self, square, matrix, piece, vectors, pieces):
        squares = []

        for vector in vectors:
            col = vector[0] + square.col
            row = vector[1] + square.row

            if col < 0 or col >= 8 or row < 0 or row >= 8:
                continue
            
            new_square = Square(col=col, row=row)

            if matrix[new_square.idx]:
                if piece.color == matrix[new_square.idx].color:
                    continue
                if matrix[new_square.idx].piece in pieces:
                    squares.append(new_square)
            
        return squares
    
    def calculateContinuousLines(self, square, matrix, piece, pieces, paddings):
        squares:list[Square] = []
        col = square.col
        row = square.row
        idx = (8 * (row)) + col

        for padding in paddings:
            col = square.col
            row = square.row
            for _i in range(8):
                col += padding[0]
                row += padding[1] 
                idx = (8 * (row)) + col
                if  col < 0 or col >= 8 or row < 0 or row >= 8:
                    break

                if matrix[idx]:    
                    if matrix[idx].color == piece.color:
                        break
                    else:
                        if matrix[idx].piece in pieces:
                            squares.append(Square(idx=idx))
                        break

                #self.piece
            
        return squares

def minimax(board:ChessBoard, depth, alpha, beta, maximizingPlayer):
    global nodes
    #print("depth:",depth)
    """if not board.position.w_king:
        return None, -10000
    if not board.position.b_king:
        return None, 10000"""

    nodes += 1

    possible_moves = board.get_possible_moves()

    if depth is None:
        if len(possible_moves) < 10:
            depth = 5
        else:
            depth = 4

    if depth == 4 and DEBUG:
        print(possible_moves)

    if not board.position.b_king:
        return None, math.inf

    if not board.position.w_king:
        return None, -math.inf

    #random.shuffle(possible_moves)

    if depth == 0 or not possible_moves:
        return None, board.evaluate_position()

    bestMove: ChessBoard = None

    if maximizingPlayer:
        maxEval = -math.inf

        for move in possible_moves:
            squareFrom, squareTo = move
            
            key = board.position.get_fen(simplify=True) + str(squareFrom.idx) + '_' + str(squareTo.idx) + str(depth)
            cached = transpositionCache.get(key)
            if cached:
                childboard = cached[0]
                evaluation = cached[1]
                nodes += 1
            else:
                childboard = board.__deepcopy__()
                childboard.move(squareFrom, squareTo)
                _gameobject, evaluation = minimax(childboard, depth-1, alpha, beta, not maximizingPlayer)
                transpositionCache.add(key,(childboard, evaluation))

            if evaluation > maxEval:
                maxEval = evaluation
                bestMove = childboard

            alpha = max(alpha, maxEval)

            if beta <= alpha:
                break  

            
        
        return bestMove, maxEval
    
    else:
        minEval = math.inf

        for move in possible_moves:
            squareFrom, squareTo = move


            key = board.position.get_fen(simplify=True) + str(squareFrom.idx) + '_' + str(squareTo.idx) + str(depth)
            cached = transpositionCache.get(key)
            if cached:
                childboard = cached[0]
                evaluation = cached[1]
            else:
                childboard = board.__deepcopy__()
                childboard.move(squareFrom, squareTo)
                _gameobject, evaluation = minimax(childboard, depth-1, alpha, beta, not maximizingPlayer)
                transpositionCache.add(key,(childboard, evaluation))

            #minEval = min(minEval, evaluation)
            if evaluation < minEval:
                minEval = evaluation
                bestMove = childboard

            beta = min(beta, evaluation) #min(beta, minEval)

            if beta <= alpha:
                break   
        
        return bestMove, minEval

def getBestMove(game:ChessBoard) -> tuple[ChessBoard, float, ResultDebug]:
    global nodes

    nodes = 0

    theory_move = game.get_theory_move()

    if theory_move:
        return [theory_move, theory_move.evaluate_position()]

    depth = None

    t0 = time.monotonic()

    bestMove, bestMoveValue = minimax(
        game,
        depth,
        -math.inf,
        math.inf,
       True
    )

    
    t1 = time.monotonic()

    duration = t1-t0

    if not duration:
        duration = 0.001

    debug = ResultDebug({
        'nodes': nodes,
        'duration': duration,
        'pre_static': game.evaluate_position(),
        'post_static': bestMove.evaluate_position(),
        'post_dynamic': bestMoveValue
    })


    return (bestMove, bestMoveValue, debug)


transpositionCache = TranspositionCache()
moveDiscoveryCache = MoveDiscoveryCache()
