import sys
import traceback
from ChessyMoon import Position, ChessBoard, getBestMove, Square

import cProfile

board = None

def main():
    if 'play' in sys.argv:
        if len(sys.argv) > 2:
            return play_ai_vs_human(fen=sys.argv[2])
        return play_ai_vs_human()
    elif 'perf' in sys.argv:
        debug = True if "debug" in sys.argv else False
        return test_fen_eval(debug)
    else:
        print('No arguments supplied')
    exit()
    

def test_fen_eval(debug=False):
    global board

    while True:
        fen = input("Enter Fen => ")

        starting_position = Position(fen=fen)
        board = ChessBoard(starting_position)

        if debug:
            cProfile.run('getBestMove(board)',sort='tottime')

        newBoard, newEval, debug = getBestMove(board)

        print(starting_position)
        print(newBoard)

        print(f"\ncalculated {debug.nodes} nodes, in {debug.duration} seconds")
        print(f"\tEffectively {debug.nodes/debug.duration} nodes/sec")
        print(f"Eval: {newEval}")
        print('\tpre static:',debug.pre_static)
        print('\tpost static:',debug.post_static)
        print('\tpost dynamic:',debug.post_dynamic)
        print('\n\n')



def play_ai_vs_human(fen=None):
    global board
    # Initialization
    if fen is None:
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - www"
        print("Using Starting fen")

    print(fen)
    
    while True:
        starting_position = Position(fen)

        board = ChessBoard(starting_position)
        
        print(starting_position)

        if board.turn:
            result = getBestMove(board)
            board = result[0]
            evaluation:int = result[1]
            fen = board.position.get_fen()
            print(evaluation)
        else:
            move = input("Enter move => ")
            squareFrom = Square(algebraic=move[:2])
            squareTo = Square(algebraic=move[2:])
            board.move(squareFrom, squareTo)
            fen = board.position.fen

        print(board)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(traceback.format_exc())
