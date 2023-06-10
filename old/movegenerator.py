def idx_to_coord(idx):
    """
    Convert an index to a coordinate tuple
    """
    return (idx % 8, idx // 8)

def coord_to_idx(coord):
    """
    Convert a coordinate tuple to an index
    """
    return coord[0] + coord[1] * 8

def idx_to_algebraic(idx):
    """
    Convert an index to an algebraic notation string
    """
    coord = idx_to_coord(idx)
    return chr(ord('a') + coord[0]) + str(coord[1] + 1)

class Move:
    def __init__(self, src, dst, rule = '', remove = -1):
        self.src = src
        self.dst = dst
        self.rule = rule
        self.remove = remove

    @property
    def notation(self):
        notations = {
            'default': idx_to_algebraic(self.src) + idx_to_algebraic(self.dst),
            'capture': idx_to_algebraic(self.src)[0] + 'x' + idx_to_algebraic(self.dst),
            'enpassant': idx_to_algebraic(self.src)[0] + 'x' + idx_to_algebraic(self.dst) + 'e.p. (forced)',
            'knight_boost': '(N@' + idx_to_algebraic(self.src) + ', R@' + idx_to_algebraic(self.dst) + '; N'+ idx_to_algebraic(self.dst) + '=Ñ)',
            'knight_move': 'N'+ idx_to_algebraic(self.dst),
            'knight_capture': 'N' + 'x' + idx_to_algebraic(self.dst),
            'bishop_move': 'B' + idx_to_algebraic(self.dst),
            'bishop_capture': 'B' + 'x' + idx_to_algebraic(self.dst),

        }

        return notations.get(self.rule, notations['default'])

    def __str__(self):
        return self.notation
    
    def __repr__(self):
        return self.notation

class PawnRays:
    def __init__(self, board, idx, piece):
        self.moves = self._generate_moves(board, idx, piece)

    def get_vector(self, coord, piece, board):
        """
        Return the vector of the given index
        """
        if piece.color:
            if coord[1] == 1:
                vectors = [16, 8]
            elif coord[1] == 4:
                if board.matrix[coord_to_idx((coord[0] - 1, coord[1]))].piece == 'p':
                    vectors = [8, 7]
                elif board.matrix[coord_to_idx((coord[0] + 1, coord[1]))].piece == 'p':
                    vectors = [8, 9]
                else:
                    vectors = [8]
            elif coord[1] == 7:
                vectors = []
            else:
                vectors = [8]
        else:
            if coord[1] == 6:
                vectors = [-16, -8]
            elif coord[1] == 3:
                if board.matrix[coord_to_idx((coord[0] - 1, coord[1]))].piece == 'P':
                    vectors = [-8, -7]
                elif board.matrix[coord_to_idx((coord[0] + 1, coord[1]))].piece == 'P':
                    vectors = [-8, -9]
                else:
                    vectors = [-8]
            elif coord[1] == 0:
                vectors = []
            else:
                vectors = [-8]

        

        return vectors

    def _generate_moves(self, board, idx, piece):
        """
        Generate pawn rays for a given board and piece
        """
        matrix = board.matrix
        coord = idx_to_coord(idx)
        vectors = self.get_vector(coord, piece, board)
        moves = []

        for vector in vectors:
            if not matrix[idx + vector].empty and vector in [7, -7, 9, -9]:
                toremove = idx + vector - 8 if piece.color else idx + vector + 8
                moves.append(Move(idx, idx + vector, 'capture', toremove))
            elif matrix[idx + vector].empty and vector in [8, -8, 16, -16, 7, -7, 9, -9]:
                moves.append(Move(idx, idx + vector, 'move'))

        # Check captures
        if piece.color:
            if matrix[idx + 7].color == 0 and idx % 8 != 0 and not matrix[idx + 7].empty:
                moves.append(Move(idx, idx + 7, 'capture', idx + 7))
            if matrix[idx + 9].color == 0 and idx % 8 != 7 and not matrix[idx + 9].empty:
                moves.append(Move(idx, idx + 9, 'capture', idx + 9))
        else:
            if matrix[idx - 7].color == 1 and idx % 8 != 7 and not matrix[idx - 7].empty:
                moves.append(Move(idx, idx - 7, 'capture', idx - 7))
            if matrix[idx - 9].color == 1 and idx % 8 != 0 and not matrix[idx - 9].empty:
                moves.append(Move(idx, idx - 9, 'capture', idx - 9))

        return {idx_to_algebraic(idx): moves}
    

class KnightRays:
    def __init__(self, board, idx, piece):
        self.moves = self._generate_moves(board, idx, piece)

    def _generate_moves(self, board, idx, piece):
        """
        Generate knight rays for a given board and piece
        """
        matrix = board.matrix
        coord = idx_to_coord(idx)
        piece = matrix[idx]
        moves = []

        # Generate moves
        for vector in [-17, -15, -10, -6, 6, 10, 15, 17]:
            if coord[0] + vector % 8 in range(0,9) and coord[1] + vector // 8 in range(0,9):
                if matrix[idx + vector].empty:
                    moves.append(Move(idx, idx + vector, 'knight_move'))
                elif matrix[idx + vector].color != piece.color:
                    moves.append(Move(idx, idx + vector, 'knight_capture', idx + vector))
                #if rook of own color, add kight_boost move
                elif matrix[idx + vector].piece.lower() == 'r':
                    moves.append(Move(idx, idx + vector, 'knight_boost'))
            else:
                pass
        return {idx_to_algebraic(idx): moves}

class BishopRays:
    def __init__(self, board, idx, piece):
        self.moves = self._generate_moves(board, idx, piece)

    def _generate_moves(self, board, idx, piece):
        col = idx % 8
        row = idx // 8
        matrix = board.matrix
        moves = []

        

        # Generate moves
        for vector in [7, 9, -9, -7]:
            current_col = col
            current_row = row
            current_idx = idx
            for i in range(1,8):
                current_col += vector % 8
                current_row += vector // 8
                current_idx += vector
                if current_col in range(0,8) and current_row in range(0,8):
                    if matrix[current_idx].empty:
                        moves.append(Move(idx, current_idx, 'bishop_move'))
                    elif matrix[current_idx].color != piece.color:
                        moves.append(Move(idx, current_idx, 'bishop_capture', current_idx))
                        break
                    else:
                        break
                else:
                    break
                

        return {idx_to_algebraic(idx): moves}

class RookRays:
    pass

class QueenRays:    
    pass

class KingRays:
    pass

class KnookRays:
    pass


        

class MoveGenerator:
    def __init__(self, board):
        """
        Class to generate moves for a given board
        """
        
        self.turn = board.turn
        self.matrix = board.matrix
        self.squares = []

        for i in range(64):
            if self.matrix[i].color == self.turn:
                self.squares.append(i)

        for square in self.squares:
            piece = self.matrix[square]
            if piece.piece == 'p':
                print(PawnRays(board, square, piece).moves)
            elif piece.piece == 'n':
                print(KnightRays(board, square, piece).moves)
            elif piece.piece == 'b':
                print(BishopRays(board, square, piece).moves)
