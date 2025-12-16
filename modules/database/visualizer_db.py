import sqlite3
import json
from datetime import datetime

DB_PATH = "escalade3.db"

def init_visualizer_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS visualizer_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT,
        algorithm TEXT,
        heuristic TEXT,
        params TEXT,
        grid_rows INTEGER,
        grid_cols INTEGER,
        wall_count INTEGER,
        start TEXT,
        goal TEXT,
        visited_order TEXT,
        path TEXT,
        stats TEXT,
        agent_report TEXT
    )
    """)
    conn.commit()
    conn.close()


def save_run(payload: dict) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO visualizer_runs (
        created_at, algorithm, heuristic, params,
        grid_rows, grid_cols, wall_count,
        start, goal, visited_order, path, stats, agent_report
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.utcnow().isoformat(),
        payload.get("algorithm"),
        payload.get("heuristic"),
        json.dumps(payload.get("params", {})),
        payload.get("grid_rows"),
        payload.get("grid_cols"),
        payload.get("wall_count"),
        json.dumps(payload.get("start")),
        json.dumps(payload.get("goal")),
        json.dumps(payload.get("visited_order", [])),
        json.dumps(payload.get("path", [])),
        json.dumps(payload.get("stats", {})),
        json.dumps(payload.get("agent_report", {})),
    ))
    conn.commit()
    run_id = cur.lastrowid
    conn.close()
    return run_id


def load_run(run_id: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM visualizer_runs WHERE id=?", (run_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return {}

    # map columns by index order
    keys = [
        "id","created_at","algorithm","heuristic","params",
        "grid_rows","grid_cols","wall_count",
        "start","goal","visited_order","path","stats","agent_report"
    ]
    out = dict(zip(keys, row))
    for k in ("params","start","goal","visited_order","path","stats","agent_report"):
        out[k] = json.loads(out[k]) if out[k] else {}
    return out
