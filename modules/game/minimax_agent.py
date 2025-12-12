from math import inf
from copy import deepcopy

from .connect4_engine import (
    ROWS,
    COLS,
    EMPTY,
    PLAYER_PIECE,
    AI_PIECE,
    is_valid_move,
    get_next_open_row,
    drop_piece,
    check_winner,
    is_draw,
)


def evaluate_window(window, piece):
    score = 0
    opp_piece = PLAYER_PIECE if piece == AI_PIECE else AI_PIECE

    if window.count(piece) == 4:
        score += 100
    elif window.count(piece) == 3 and window.count(EMPTY) == 1:
        score += 5
    elif window.count(piece) == 2 and window.count(EMPTY) == 2:
        score += 2

    if window.count(opp_piece) == 3 and window.count(EMPTY) == 1:
        score -= 4

    return score


def score_position(board, piece):
    score = 0

    # Center column preference
    center_array = [board[r][COLS // 2] for r in range(ROWS)]
    score += center_array.count(piece) * 3

    # Horizontal
    for r in range(ROWS):
        row_array = board[r]
        for c in range(COLS - 3):
            window = row_array[c : c + 4]
            score += evaluate_window(window, piece)

    # Vertical
    for c in range(COLS):
        col_array = [board[r][c] for r in range(ROWS)]
        for r in range(ROWS - 3):
            window = col_array[r : r + 4]
            score += evaluate_window(window, piece)

    # Positive diagonal
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r + i][c + i] for i in range(4)]
            score += evaluate_window(window, piece)

    # Negative diagonal
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            window = [board[r - i][c + i] for i in range(4)]
            score += evaluate_window(window, piece)

    return score


def get_valid_locations(board):
    return [c for c in range(COLS) if is_valid_move(board, c)]


def is_terminal(board):
    return (
        check_winner(board, PLAYER_PIECE)
        or check_winner(board, AI_PIECE)
        or is_draw(board)
    )


def minimax(board, depth, alpha, beta, maximizing_player):
    valid_locations = get_valid_locations(board)
    terminal = is_terminal(board)

    if depth == 0 or terminal:
        if terminal:
            if check_winner(board, AI_PIECE):
                return None, 1_000_000
            elif check_winner(board, PLAYER_PIECE):
                return None, -1_000_000
            else:
                return None, 0
        else:
            return None, score_position(board, AI_PIECE)

    if maximizing_player:
        value = -inf
        best_col = valid_locations[0]
        for col in valid_locations:
            temp_board = deepcopy(board)
            row = get_next_open_row(temp_board, col)
            drop_piece(temp_board, row, col, AI_PIECE)
            _, new_score = minimax(temp_board, depth - 1, alpha, beta, False)
            if new_score > value:
                value = new_score
                best_col = col
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return best_col, value
    else:
        value = inf
        best_col = valid_locations[0]
        for col in valid_locations:
            temp_board = deepcopy(board)
            row = get_next_open_row(temp_board, col)
            drop_piece(temp_board, row, col, PLAYER_PIECE)
            _, new_score = minimax(temp_board, depth - 1, alpha, beta, True)
            if new_score < value:
                value = new_score
                best_col = col
            beta = min(beta, value)
            if alpha >= beta:
                break
        return best_col, value


def get_ai_move(board, depth: int = 4):
    """Return column chosen by AI using minimax."""
    valid_locations = get_valid_locations(board)
    if not valid_locations:
        return None
    col, _ = minimax(board, depth, -inf, inf, True)
    # Sometimes col can be None if terminal → fall back
    if col is None:
        return valid_locations[0]
    return col


def evaluate_board_for_ai(board, depth: int = 3):
    """
    Evaluate the board from the AI's perspective using minimax.
    Higher score = better for AI.
    Used by the learning agent to detect mistakes/blunders.
    """
    _, score = minimax(board, depth, -inf, inf, True)
    return score
