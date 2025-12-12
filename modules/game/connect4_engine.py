ROWS = 6
COLS = 7

EMPTY = 0
PLAYER_PIECE = 1
AI_PIECE = 2


def create_empty_board():
    """Return an empty 6x7 board."""
    return [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]


def is_valid_move(board, col):
    """A move is valid if the top cell of the column is empty."""
    return 0 <= col < COLS and board[0][col] == EMPTY


def get_next_open_row(board, col):
    """Return the lowest available row index in this column."""
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == EMPTY:
            return r
    return None


def drop_piece(board, row, col, piece):
    """Place a piece on the board."""
    board[row][col] = piece


def check_winner(board, piece):
    """Check if the given piece has four in a row."""

    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            if all(board[r][c + i] == piece for i in range(4)):
                return True

    # Vertical
    for c in range(COLS):
        for r in range(ROWS - 3):
            if all(board[r + i][c] == piece for i in range(4)):
                return True

    # Positive diagonal (\)
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if all(board[r + i][c + i] == piece for i in range(4)):
                return True

    # Negative diagonal (/)
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            if all(board[r - i][c + i] == piece for i in range(4)):
                return True

    return False


def is_draw(board):
    """Draw if top row has no empty cells."""
    return all(board[0][c] != EMPTY for c in range(COLS))
