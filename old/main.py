import anarchyvision as AnarchyVision

board = AnarchyVision.Board()
#board.set_fen('rnbqkbnr/pppp1p1p/6p1/4pP2/8/8/PPPPP1PP/RNBQKBNR w KQkq e6 0 3')
board.set_fen('rnbqkbnr/pppp1p1p/6p1/4pP2/2N5/1NBPP3/PPPP2PP/R1BQKBNR')

print(board)
print(board.fen)

# Test move generation

t1 = AnarchyVision.MoveGenerator(board)