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

from modules.visualizer.search_algorithms import run_search

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
    report = session.get("visualizer_report")
    if report is None:
        # No run yet
        report = {
            "algorithm": "N/A",
            "found": False,
            "nodes_expanded": 0,
            "path_length": 0,
            "heuristic": None,
            "efficiency_ratio": None,
            "summary_lines": [
                "No visualization has been run yet. Go back and run an algorithm first."
            ],
        }
    return render_template("visualizer_report.html", report=report)



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
    """Show a simple report of how the AI has been doing."""
    report = learning_agent.get_report()
    return render_template("game_report.html", report=report)

@app.route("/learn")
def learn_with_ai():
    return "<h1>AI Tutor Placeholder – Coming Soon</h1>"


if __name__ == "__main__":
    app.run(debug=True)
