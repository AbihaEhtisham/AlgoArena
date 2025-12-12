from typing import Dict, List, Any

# We know Connect4 has 7 columns
NUM_COLS = 7


def create_tables(conn) -> None:
    cur = conn.cursor()

    # Overall AI statistics (single row with id = 1)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_stats (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            games_played INTEGER NOT NULL DEFAULT 0,
            ai_wins INTEGER NOT NULL DEFAULT 0,
            player_wins INTEGER NOT NULL DEFAULT 0,
            draws INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    cur.execute("INSERT OR IGNORE INTO ai_stats (id) VALUES (1)")

    # Player column behavior: how often user drops in each column
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS player_column_stats (
            col INTEGER PRIMARY KEY,
            count INTEGER NOT NULL DEFAULT 0
        )
        """
    )

    # Ensure there is a row for each column 0..6
    for col in range(NUM_COLS):
        cur.execute(
            "INSERT OR IGNORE INTO player_column_stats (col, count) VALUES (?, 0)",
            (col,),
        )

    # Detailed per-game AI history
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_game_history (
            game_id INTEGER PRIMARY KEY AUTOINCREMENT,
            result TEXT NOT NULL,                -- 'ai', 'player', 'draw'
            moves INTEGER NOT NULL,              -- number of AI moves
            mistakes INTEGER NOT NULL,           -- eval dropped below previous
            blunders INTEGER NOT NULL,           -- large eval drop
            efficiency REAL NOT NULL,            -- 0.0 .. 1.0
            avg_depth REAL NOT NULL              -- average minimax depth used
        )
        """
    )

    conn.commit()


# ---------- AI stats helpers ----------


def fetch_ai_stats(conn) -> Dict[str, int]:
    cur = conn.cursor()
    cur.execute(
        "SELECT games_played, ai_wins, player_wins, draws FROM ai_stats WHERE id = 1"
    )
    row = cur.fetchone()
    if row is None:
        return {
            "games_played": 0,
            "ai_wins": 0,
            "player_wins": 0,
            "draws": 0,
        }
    return {
        "games_played": row[0],
        "ai_wins": row[1],
        "player_wins": row[2],
        "draws": row[3],
    }


def update_ai_stats(conn, stats: Dict[str, Any]) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE ai_stats
        SET games_played = ?,
            ai_wins = ?,
            player_wins = ?,
            draws = ?
        WHERE id = 1
        """,
        (
            stats.get("games_played", 0),
            stats.get("ai_wins", 0),
            stats.get("player_wins", 0),
            stats.get("draws", 0),
        ),
    )
    conn.commit()


# ---------- Player column behavior helpers ----------


def fetch_player_column_counts(conn) -> List[int]:
    cur = conn.cursor()
    cur.execute(
        "SELECT col, count FROM player_column_stats ORDER BY col ASC"
    )
    rows = cur.fetchall()
    counts = [0] * NUM_COLS
    for col, count in rows:
        if 0 <= col < NUM_COLS:
            counts[col] = count
    return counts


def increment_player_column(conn, col: int) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE player_column_stats
        SET count = count + 1
        WHERE col = ?
        """,
        (col,),
    )
    conn.commit()


# ---------- Per-game history helpers ----------


def insert_game_history(conn, game_data: Dict[str, Any]) -> None:
    """
    game_data keys:
      result: 'ai' | 'player' | 'draw'
      moves: int
      mistakes: int
      blunders: int
      efficiency: float (0..1)
      avg_depth: float
    """
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO ai_game_history
        (result, moves, mistakes, blunders, efficiency, avg_depth)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            game_data["result"],
            game_data["moves"],
            game_data["mistakes"],
            game_data["blunders"],
            game_data["efficiency"],
            game_data["avg_depth"],
        ),
    )
    conn.commit()


def fetch_history_aggregates(conn) -> Dict[str, Any]:
    """
    Returns aggregate metrics over all games:
      total_games, avg_mistakes, avg_blunders, avg_efficiency, avg_depth
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
          COUNT(*),
          AVG(mistakes),
          AVG(blunders),
          AVG(efficiency),
          AVG(avg_depth)
        FROM ai_game_history
        """
    )
    row = cur.fetchone()
    if row is None or row[0] == 0:
        return {
            "total_games": 0,
            "avg_mistakes": 0.0,
            "avg_blunders": 0.0,
            "avg_efficiency": 0.0,
            "avg_depth": 0.0,
        }

    return {
        "total_games": row[0],
        "avg_mistakes": float(row[1] or 0.0),
        "avg_blunders": float(row[2] or 0.0),
        "avg_efficiency": float(row[3] or 0.0),
        "avg_depth": float(row[4] or 0.0),
    }
