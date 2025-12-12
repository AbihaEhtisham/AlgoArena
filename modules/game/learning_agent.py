from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from .minimax_agent import get_ai_move, evaluate_board_for_ai
from .connect4_engine import COLS

from ..database.db import get_connection
from ..database.models import (
    fetch_ai_stats,
    update_ai_stats,
    fetch_player_column_counts,
    increment_player_column,
    insert_game_history,
    fetch_history_aggregates,
)


@dataclass
class LearningStats:
    games_played: int = 0
    ai_wins: int = 0
    player_wins: int = 0
    draws: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "games_played": self.games_played,
            "ai_wins": self.ai_wins,
            "player_wins": self.player_wins,
            "draws": self.draws,
        }

    @property
    def ai_win_rate(self) -> float:
        if self.games_played == 0:
            return 0.0
        return self.ai_wins / self.games_played * 100.0


class LearningAgent:
    """
    Multi-agent style learning controller for Connect4.

    Internally you can describe it as coordinating three "agents":

      1) PerformanceAgent   – tracks wins/losses and adjusts difficulty (depth)
      2) BehaviorAgent      – observes which columns the player prefers
      3) EvaluationAgent    – evaluates positions to detect mistakes/blunders

    All of this is persisted in SQLite and exposed through detailed reports.
    """

    def __init__(self):
        self.stats = LearningStats()
        self.last_result: Optional[str] = None
        # How often player plays each column 0..COLS-1
        self.player_column_counts: List[int] = [0] * COLS

        # Per-game metrics
        self.current_game_ai_moves: int = 0
        self.current_game_mistakes: int = 0
        self.current_game_blunders: int = 0
        self.current_game_total_depth: int = 0
        self.last_ai_eval: Optional[float] = None

        # Snapshot of last game metrics for the report
        self.last_game_metrics: Optional[Dict[str, Any]] = None

        self._load_from_db()

    # ---------- Persistence layer ----------

    def _load_from_db(self) -> None:
        """Load stats + column behavior from SQLite."""
        with get_connection() as conn:
            stats_dict = fetch_ai_stats(conn)
            self.stats.games_played = stats_dict["games_played"]
            self.stats.ai_wins = stats_dict["ai_wins"]
            self.stats.player_wins = stats_dict["player_wins"]
            self.stats.draws = stats_dict["draws"]

            self.player_column_counts = fetch_player_column_counts(conn)

    def _save_stats_to_db(self) -> None:
        with get_connection() as conn:
            update_ai_stats(conn, self.stats.to_dict())

    def _update_column_in_db(self, col: int) -> None:
        with get_connection() as conn:
            increment_player_column(conn, col)

    def _insert_game_history(self, result: str, moves: int,
                             mistakes: int, blunders: int,
                             efficiency: float, avg_depth: float) -> None:
        game_data = {
            "result": result,
            "moves": moves,
            "mistakes": mistakes,
            "blunders": blunders,
            "efficiency": efficiency,
            "avg_depth": avg_depth,
        }
        with get_connection() as conn:
            insert_game_history(conn, game_data)

        # also keep in memory for the "last game" section of the report
        self.last_game_metrics = game_data

    # ---------- Game lifecycle hooks ----------

    def start_new_game(self) -> None:
        """
        Call this at the beginning of each new game
        (e.g., when the user clicks 'New Game').
        """
        self.current_game_ai_moves = 0
        self.current_game_mistakes = 0
        self.current_game_blunders = 0
        self.current_game_total_depth = 0
        self.last_ai_eval = None
        # last_result is set when game ends

    def observe_player_move(self, col: int) -> None:
        """
        Called every time the human chooses a column.
        BehaviorAgent: learns which columns the player prefers.
        """
        if 0 <= col < COLS:
            self.player_column_counts[col] += 1
            self._update_column_in_db(col)

    def current_depth(self) -> int:
        """
        PerformanceAgent:
        Adapt minimax depth based on AI performance:

        - First few games: moderate difficulty
        - If AI is losing a lot: increase depth to play stronger
        - If AI is dominating: reduce depth to be more fair
        """
        games = self.stats.games_played
        win_rate = self.stats.ai_win_rate

        if games < 5:
            # Warm-up phase
            return 3

        if win_rate < 30:
            return 5  # hard
        if win_rate < 60:
            return 4  # normal
        return 3      # easy/medium

    def choose_move(self, board):
        """
        Main AI move chooser.

        - Decides depth using PerformanceAgent
        - Uses minimax for the actual move
        - BehaviorAgent biases towards contesting favorite player columns
        """
        depth = self.current_depth()
        self.current_game_ai_moves += 1
        self.current_game_total_depth += depth

        from .minimax_agent import get_valid_locations
        import random

        base_col = get_ai_move(board, depth=depth)
        valid_cols = get_valid_locations(board)
        if not valid_cols:
            return base_col

        # If we don't have any behavior data yet, just return base_col
        if sum(self.player_column_counts) == 0:
            return base_col

        # Player's historically favorite column
        favorite_col = max(
            range(COLS),
            key=lambda c: self.player_column_counts[c],
        )
        favorite_count = self.player_column_counts[favorite_col]
        total_moves = sum(self.player_column_counts)
        usage_ratio = favorite_count / float(total_moves or 1)

        chosen = base_col

        # If player strongly prefers a column, sometimes contest it
        if usage_ratio > 0.35 and favorite_col in valid_cols:
            if random.random() < 0.5:
                chosen = favorite_col

        return chosen

    # ---------- EvaluationAgent: measuring mistakes/blunders ----------

    def after_ai_move(self, board) -> None:
        """
        Called after the AI's move is actually placed on the board.
        Evaluates the new position from AI's perspective.
        """
        # Use a smaller eval depth to keep it cheap
        self.last_ai_eval = evaluate_board_for_ai(board, depth=2)

    def after_player_move(self, board) -> None:
        """
        Called after the player's move is actually placed on the board.
        Compares new evaluation with previous AI evaluation to see
        how much the position worsened for the AI.
        """
        new_eval = evaluate_board_for_ai(board, depth=2)

        if self.last_ai_eval is None:
            # First evaluation of the game
            self.last_ai_eval = new_eval
            return

        delta = new_eval - self.last_ai_eval  # how much better/worse for AI
        # If delta < 0, the position is worse for AI than before:
        if delta < 0:
            # Moderate drop → "mistake"
            self.current_game_mistakes += 1
            # Very large drop → "blunder"
            if delta <= -200000:  # threshold relative to +/-1_000_000 terminal
                self.current_game_blunders += 1

        self.last_ai_eval = new_eval

    # ---------- Finalizing a game ----------

    def update_after_game(self, result: str) -> None:
        """
        result in {"ai", "player", "draw"}.
        Update long-term stats, compute per-game efficiency, and persist.
        """
        self.stats.games_played += 1
        self.last_result = result

        if result == "ai":
            self.stats.ai_wins += 1
        elif result == "player":
            self.stats.player_wins += 1
        elif result == "draw":
            self.stats.draws += 1

        # Save high-level stats
        self._save_stats_to_db()

        # Per-game detailed metrics
        moves = self.current_game_ai_moves or 1
        mistakes = self.current_game_mistakes
        blunders = self.current_game_blunders
        avg_depth = (
            float(self.current_game_total_depth) / float(moves)
            if moves > 0
            else float(self.current_depth())
        )

        # Simple efficiency metric: penalize mistakes and blunders
        penalty = mistakes + 2 * blunders
        efficiency = max(0.0, 1.0 - penalty / float(moves))

        # Persist per-game history
        self._insert_game_history(
            result=result,
            moves=moves,
            mistakes=mistakes,
            blunders=blunders,
            efficiency=efficiency,
            avg_depth=avg_depth,
        )

    # ---------- Report for UI ----------

    def get_report(self) -> Dict[str, Any]:
        report: Dict[str, Any] = self.stats.to_dict()
        report["ai_win_rate"] = round(self.stats.ai_win_rate, 2)
        report["last_result"] = self.last_result

        # Depth & behavior
        report["current_depth"] = self.current_depth()
        report["player_column_counts"] = self.player_column_counts

        # Last game metrics
        if self.last_game_metrics is not None:
            lg = self.last_game_metrics
        else:
            lg = {
                "result": "N/A",
                "moves": 0,
                "mistakes": 0,
                "blunders": 0,
                "efficiency": 0.0,
                "avg_depth": 0.0,
            }
        report["last_game"] = lg

        # History aggregates from DB
        with get_connection() as conn:
            history = fetch_history_aggregates(conn)
        report["history"] = history

        return report
