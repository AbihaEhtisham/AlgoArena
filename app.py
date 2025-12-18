from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    url_for,
)
from datetime import timedelta
from modules.database.db import get_connection  # optional if you want direct DB use
from modules.database.visualizer_db import init_visualizer_db
from modules.database.visualizer_db import load_run  # adjust import if path differs
from modules.visualizer.search_algorithms import run_search
from modules.game.connect4_engine import (
    create_empty_board,
    is_valid_move,
    get_next_open_row,
    drop_piece,
    check_winner,
    is_draw,
    ROWS,
    COLS,
    PLAYER_PIECE,
    AI_PIECE,
)
from modules.game.learning_agent import LearningAgent
from modules.visualizer.search_algorithms import run_search
from modules.visualizer.report_generator import generate_report


app = Flask(__name__)

# For sessions (needed to store board per user)
app.secret_key = "change-this-secret-key"
app.permanent_session_lifetime = timedelta(hours=2)

# Global learning agent instance (simple in-memory learning across games)
learning_agent = LearningAgent()
init_visualizer_db()

def init_board():
    """Initialize a new empty board in the session."""
    board = create_empty_board()
    session["board"] = board
    session["game_over"] = False
    return board


def get_board():
    """Get current board from session, or create one if not present."""
    board = session.get("board")
    if board is None:
        board = init_board()
    return board


@app.route("/")
def index():
    """Main menu: Visualizer or Game."""
    return render_template("index.html")


@app.route("/visualizer")
def visualizer():
    """Visualizer page."""
    return render_template("visualizer.html")

from modules.visualizer.search_algorithms import run_search
from modules.database.visualizer_db import save_run
from modules.visualizer.agents.report_agents import generate_multiagent_report

@app.route("/api/visualizer/run", methods=["POST"])
def api_visualizer_run():
    data = request.get_json() or {}

    grid = data.get("grid")
    start = data.get("start")
    goal = data.get("goal")
    algorithm = data.get("algorithm", "bfs")
    heuristic = data.get("heuristic", "manhattan")
    params = data.get("params", {}) or {}

    if grid is None or start is None or goal is None:
        return jsonify({"ok": False, "error": "Missing grid/start/goal"}), 400

    try:
        start = (int(start[0]), int(start[1]))
        goal = (int(goal[0]), int(goal[1]))
    except Exception:
        return jsonify({"ok": False, "error": "Invalid start/goal format"}), 400

    # ✅ result is ALWAYS defined here
    result = run_search(grid, start, goal, algorithm, heuristic, params)
    run_payload = {
        "algorithm": result.stats.get("algorithm"),
        "heuristic": heuristic,
        "params": params,
        "grid_rows": len(grid),
        "grid_cols": len(grid[0]) if grid else 0,
        "wall_count": sum(1 for r in grid for v in r if v == 1),
        "start": list(start),
        "goal": list(goal),
        "visited_order": result.visited_order,
        "path": result.path,
        "stats": result.stats,
    }

# optionally: compare to last run later (we'll add it soon)
    agent_report = generate_multiagent_report(run_payload, previous_run=None)
    run_payload["agent_report"] = agent_report

    run_id = save_run(run_payload)

    return jsonify({
        "ok": True,
        "visited_order": result.visited_order,
        "path": result.path,
        "stats": result.stats,
        "run_id": run_id,
        "agent_report": agent_report
    })


    if not result.ok:
        return jsonify({"ok": False, "error": result.stats.get("error", "Error")}), 400

    return jsonify({
        "ok": True,
        "visited_order": result.visited_order,
        "path": result.path,
        "stats": result.stats
    })


@app.route("/visualizer/report")
def visualizer_report():
    run_id = request.args.get("run_id", type=int)

    if not run_id:
        return render_template("visualizer_report.html", report=None)

    run = load_run(run_id)
    if not run:
        return render_template("visualizer_report.html", report=None)

    return render_template("visualizer_report.html", report=run.get("agent_report"))

@app.route("/game/connect4")
def connect4():
    """Connect4 game page."""
    get_board()  # ensure a board exists in session
    return render_template("game.html", rows=ROWS, cols=COLS)


@app.route("/api/connect4/new", methods=["POST"])
def api_new_game():
    """Start a new game (reset board)."""
    board = init_board()
    learning_agent.start_new_game()
    return jsonify({"board": board, "status": "new"})



@app.route("/api/connect4/player-move", methods=["POST"])
def api_player_move():
    """Handle player move and AI move; return updated board + game status."""
    data = request.get_json(silent=True) or {}
    col = data.get("column")

    board = get_board()

    if session.get("game_over"):
        return jsonify({"error": "Game is already over."}), 400

    if col is None or not isinstance(col, int) or not is_valid_move(board, col):
        return jsonify({"error": "Invalid move."}), 400
    learning_agent.observe_player_move(col)
    # ----- Player move -----
    player_row = get_next_open_row(board, col)
    drop_piece(board, player_row, col, PLAYER_PIECE)

    # Let the evaluation agent see the new position
    learning_agent.after_player_move(board)

    status = "ongoing"
    winner = None
    ai_col = None


    if check_winner(board, PLAYER_PIECE):
        status = "finished"
        winner = "player"
        session["game_over"] = True
        learning_agent.update_after_game("player")
    elif is_draw(board):
        status = "finished"
        winner = "draw"
        session["game_over"] = True
        learning_agent.update_after_game("draw")
    else:
        # ----- AI move -----
        ai_col = learning_agent.choose_move(board)
        if ai_col is not None and is_valid_move(board, ai_col):
            ai_row = get_next_open_row(board, ai_col)
            drop_piece(board, ai_row, ai_col, AI_PIECE)
            learning_agent.after_ai_move(board)


            if check_winner(board, AI_PIECE):
                status = "finished"
                winner = "ai"
                session["game_over"] = True
                learning_agent.update_after_game("ai")
            elif is_draw(board):
                status = "finished"
                winner = "draw"
                session["game_over"] = True
                learning_agent.update_after_game("draw")
        else:
            # No valid move for AI (should be rare) → draw
            status = "finished"
            winner = "draw"
            session["game_over"] = True
            learning_agent.update_after_game("draw")

    # Save board back into session
    session["board"] = board

    response = {
        "board": board,
        "status": status,
        "winner": winner,
        "ai_column": ai_col,
    }
    if status == "finished":
        response["redirect_to_report"] = url_for("connect4_report")

    return jsonify(response)

def evaluate_board_for_ai(board, depth: int = 3):
    """
    Evaluate the board from the AI's perspective using minimax.
    Higher score = better for AI.
    Used by the learning agent to detect mistakes/blunders.
    """
    _, score = minimax(board, depth, -inf, inf, True)
    return score

@app.route("/game/connect4/report")
def connect4_report():
    
    report = learning_agent.get_report()

    counts_raw = report.get("player_column_counts") or []
    counts = []
    for x in counts_raw:
        try:
            counts.append(int(x))
        except Exception:
            counts.append(0)

    max_count = max(counts) if counts else 0

    bars = []
    for i, c in enumerate(counts):
        pct = (c / max_count * 100.0) if max_count > 0 else 0.0
        bars.append({
            "col": i,
            "count": c,
            "pct": pct,
            "width_css": f"{pct:.1f}%"   # ✅ plain string for CSS
        })

    report["player_column_bars"] = bars
    return render_template("game_report.html", report=report)



if __name__ == "__main__":
    app.run(debug=True)
