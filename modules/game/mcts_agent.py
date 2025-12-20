# modules/game/mcts_agent.py
import math
import random
import time
from copy import deepcopy

# Reuse your engine helpers if you want, but keep this file standalone-friendly.
# We'll implement minimal helpers here to avoid coupling.

ROWS = 6
COLS = 7

PLAYER = 1   # human
AI = 2       # AI

def valid_moves(board):
    moves = []
    for c in range(COLS):
        if board[0][c] == 0:
            moves.append(c)
    return moves

def next_open_row(board, col):
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == 0:
            return r
    return None

def drop(board, row, col, piece):
    board[row][col] = piece

def is_draw(board):
    return all(board[0][c] != 0 for c in range(COLS))

def check_winner(board, piece):
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            if all(board[r][c+i] == piece for i in range(4)):
                return True
    # Vertical
    for r in range(ROWS - 3):
        for c in range(COLS):
            if all(board[r+i][c] == piece for i in range(4)):
                return True
    # Diagonal /
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            if all(board[r-i][c+i] == piece for i in range(4)):
                return True
    # Diagonal \
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if all(board[r+i][c+i] == piece for i in range(4)):
                return True
    return False

def terminal_result(board):
    """Return (is_terminal, winner_piece_or_0_for_draw)."""
    if check_winner(board, AI):
        return True, AI
    if check_winner(board, PLAYER):
        return True, PLAYER
    if is_draw(board):
        return True, 0
    return False, None


class Node:
    __slots__ = ("parent", "move", "player_to_move", "children", "untried", "wins", "visits")

    def __init__(self, parent, move, player_to_move, untried_moves):
        self.parent = parent
        self.move = move  # move that led to this node
        self.player_to_move = player_to_move
        self.children = []
        self.untried = list(untried_moves)
        self.wins = 0.0
        self.visits = 0

    def uct_score(self, c=1.4):
        if self.visits == 0:
            return float("inf")
        return (self.wins / self.visits) + c * math.sqrt(math.log(self.parent.visits + 1) / self.visits)

    def best_child(self, c=1.4):
        return max(self.children, key=lambda ch: ch.uct_score(c))

    def most_visited_child(self):
        return max(self.children, key=lambda ch: ch.visits)


class MCTSAgent:
    """
    Monte Carlo Tree Search agent (UCT).
    - Runs simulations for a time budget OR fixed iterations.
    - Returns the column for the AI move.
    """

    def __init__(self, time_limit_ms=350, max_iters=2000, exploration=1.4, seed=7):
        self.time_limit_ms = time_limit_ms
        self.max_iters = max_iters
        self.exploration = exploration
        random.seed(seed)

    def choose_move(self, board, ai_piece=AI, player_piece=PLAYER):
        start_t = time.time()
        time_limit = self.time_limit_ms / 1000.0

        root_moves = valid_moves(board)
        if not root_moves:
            return None

        root = Node(parent=None, move=None, player_to_move=ai_piece, untried_moves=root_moves)
        root.parent = root  # tiny hack to avoid None log issues; root uses itself as parent

        iters = 0
        while iters < self.max_iters and (time.time() - start_t) < time_limit:
            iters += 1
            node = root
            sim_board = deepcopy(board)
            player_to_move = ai_piece

            # 1) SELECTION
            while not node.untried and node.children:
                node = node.best_child(self.exploration)
                # apply node.move
                r = next_open_row(sim_board, node.move)
                drop(sim_board, r, node.move, player_to_move)
                player_to_move = player_piece if player_to_move == ai_piece else ai_piece

            # 2) EXPANSION
            if node.untried:
                m = random.choice(node.untried)
                node.untried.remove(m)

                r = next_open_row(sim_board, m)
                drop(sim_board, r, m, player_to_move)

                next_player = player_piece if player_to_move == ai_piece else ai_piece
                child = Node(parent=node, move=m, player_to_move=next_player, untried_moves=valid_moves(sim_board))
                node.children.append(child)
                node = child
                player_to_move = next_player

            # 3) SIMULATION (rollout)
            terminal, winner = terminal_result(sim_board)
            while not terminal:
                moves = valid_moves(sim_board)
                if not moves:
                    break

                # Simple rollout policy: prefer center sometimes (improves quality)
                center = 3
                if center in moves and random.random() < 0.45:
                    move = center
                else:
                    move = random.choice(moves)

                r = next_open_row(sim_board, move)
                drop(sim_board, r, move, player_to_move)
                player_to_move = player_piece if player_to_move == ai_piece else ai_piece
                terminal, winner = terminal_result(sim_board)

            # 4) BACKPROP
            # score from AI perspective
            if winner == ai_piece:
                reward = 1.0
            elif winner == 0:
                reward = 0.5
            else:
                reward = 0.0

            # backprop up to root
            while True:
                node.visits += 1
                node.wins += reward
                if node is root:
                    break
                node = node.parent

        # choose by most visits (standard)
        best = root.most_visited_child()
        return best.move
