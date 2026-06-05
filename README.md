# 🧠 AlgoArena

> An interactive algorithm visualization and AI gaming platform — explore 17 search algorithms, challenge three distinct AI engines in Connect4, and learn from a local LLM tutor.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Module 1 — Algorithm Visualizer](#module-1--algorithm-visualizer)
- [Module 2 — Connect4 AI Game](#module-2--connect4-ai-game)
- [Module 3 — AI Tutor Chatbot](#module-3--ai-tutor-chatbot)
- [DQN Training](#dqn-training)
- [Database Schema](#database-schema)
- [API Reference](#api-reference)
- [Screenshots](#screenshots)
- [Future Improvements](#future-improvements)

---

## Overview

AlgoArena is a full-stack educational platform built with Flask that makes classic and modern AI algorithms tangible and explorable. It consists of three integrated modules:

| Module | Description |
|---|---|
| **Algorithm Visualizer** | Step-by-step grid pathfinding with 17 algorithms and 7 heuristics |
| **Connect4 AI Game** | Play against Minimax, MCTS, or a self-trained Deep Q-Network |
| **AI Tutor Chatbot** | Ask questions about algorithms and get explanations from a local LLM |

---

## Features

### Algorithm Visualizer
- **17 algorithms** — from BFS and DFS to IDA\*, Simulated Annealing, and Beam Search
- **7 heuristics** — Manhattan, Euclidean, Chebyshev, Octile, Tie-breaker, Overestimate, Wall-penalty
- Animated step-by-step exploration with path reconstruction
- **Multi-agent report system** — automatically computes efficiency ratio, revisit rate, detour ratio, branching factor estimate, and coaching insights after every run
- All runs persisted to SQLite for historical comparison

### Connect4 AI Game
- **Three AI engines** selectable per game:
  - **Minimax + Alpha-Beta Pruning** — adaptive depth (3–5) based on historical win rate
  - **MCTS** — Monte Carlo Tree Search with UCB1, 2,500 iterations within a 350ms budget
  - **DQN** — Convolutional Deep Q-Network trained via self-play reinforcement learning
- **Learning Agent** that tracks player column preferences and occasionally contests favorite moves
- Post-game analytics report: win/loss history, mistakes, blunders, efficiency, average search depth
- All stats and game history persisted to SQLite across sessions

### AI Tutor Chatbot
- Powered by **Ollama (LLaMA 3.1 8B)** running locally — no external API calls
- Domain-scoped system prompt restricts conversation to algorithms, heuristics, Connect4 AI, and AlgoArena features
- Low-temperature (0.3) responses for consistent, factual explanations

---

## Project Structure

```
AlgoArena/
│
├── app.py                          # Flask app — routes, session management
├── config.py                       # Configuration constants
├── requirements.txt
│
├── modules/
│   ├── visualizer/
│   │   ├── search_algorithms.py    # All 17 algorithms + heuristics
│   │   ├── report_generator.py     # Per-run report builder
│   │   └── agents/
│   │       └── report_agents.py    # AnalyzerAgent + CoachAgent
│   │
│   ├── game/
│   │   ├── connect4_engine.py      # Board logic (drop, check winner, draw)
│   │   ├── minimax_agent.py        # Minimax + alpha-beta pruning
│   │   ├── mcts_agent.py           # Monte Carlo Tree Search
│   │   ├── dqn_agent.py            # DQN inference wrapper
│   │   ├── dqn_model.py            # PyTorch CNN model definition
│   │   └── learning_agent.py       # Orchestrator + persistence + reports
│   │
│   └── database/
│       ├── db.py                   # SQLite connection helper
│       ├── models.py               # Table creation + query helpers
│       └── visualizer_db.py        # Visualizer run persistence
│
├── scripts/
│   └── train_dqn.py                # Self-play DQN training script
│
├── models/
│   └── dqn_connect4.pt             # Pretrained DQN weights (~2.8 MB)
│
├── templates/
│   ├── index.html                  # Main menu
│   ├── visualizer.html             # Algorithm visualizer UI
│   ├── visualizer_report.html      # Post-run analytics report
│   ├── game.html                   # Connect4 game board
│   ├── game_report.html            # Post-game analytics report
│   └── learn.html                  # AI Tutor chatbot UI
│
├── static/
│   ├── css/                        # Per-page stylesheets
│   └── js/
│       ├── visualizer/
│       │   └── visualizer_core.js  # Grid rendering + animation
│       └── game/
│           └── connect4_core.js    # Board UI + move handling
│
├── Instance/
│   └── algoarena.db                # Game stats SQLite database
└── escalade3.db                    # Visualizer runs SQLite database
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, Flask |
| AI / ML | PyTorch (DQN), NumPy |
| Local LLM | Ollama (LLaMA 3.1 8B) |
| Database | SQLite (via Python `sqlite3`) |
| Frontend | Vanilla JS, Jinja2, CSS |
| Training | Self-play reinforcement learning with experience replay |

---

## Getting Started

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) installed and running (for the tutor chatbot)
- The LLaMA 3.1 8B model pulled: `ollama pull llama3.1:8b`

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/AlgoArena.git
cd AlgoArena

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python app.py
```

The app will be available at `http://localhost:5000`.

### Environment Variables (optional)

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.1:8b` | Model to use for the tutor |

---

## Module 1 — Algorithm Visualizer

Navigate to `/visualizer` to open an interactive grid. Set start and goal nodes, draw walls, select an algorithm and heuristic, then watch the search unfold step by step.

### Supported Algorithms

| Category | Algorithms |
|---|---|
| **Uninformed** | BFS, DFS, Depth-Limited Search, IDDFS, UCS / Dijkstra, Bidirectional BFS |
| **Informed** | Greedy Best-First, A\*, Weighted A\* (W-A\*), IDA\*, Beam Search |
| **Randomized** | Stochastic DFS, Random Walk |
| **Local Search** | Hill Climbing, Random-Restart Hill Climbing, Simulated Annealing |

### Supported Heuristics

`manhattan` · `euclidean` · `chebyshev` · `octile` · `tiebreaker` · `overestimate` (inadmissible) · `wallpenalty`

### Algorithm-specific Parameters

| Algorithm | Parameter | Default |
|---|---|---|
| Depth-Limited Search | `depth_limit` | 25 |
| IDDFS | `depth_limit` | 80 |
| Weighted A\* | `weight` | 1.6 |
| Beam Search | `beam_width` | 5 |
| Simulated Annealing | `temperature`, `cooling`, `max_steps` | 1.0, 0.995, 800 |

### Post-run Report

After each run, the **AnalyzerAgent** and **CoachAgent** compute:

- `nodes_expanded` — total nodes visited
- `unique_nodes` — deduplicated expansions
- `revisit_rate_%` — proportion of revisited nodes (useful for randomized algorithms)
- `path_length` — steps in the found path
- `efficiency_visited_per_step` — how many nodes were explored per step of the final path
- `detour_ratio_vs_manhattan` — how much longer the path is vs. the straight-line lower bound
- `branching_factor_est` — estimated effective branching factor

---

## Module 2 — Connect4 AI Game

Navigate to `/game/connect4`. Before each game, select an AI mode:

```
POST /api/connect4/new
{ "ai_mode": "minimax" | "mcts" | "dqn" }
```

### AI Engines

#### Minimax + Alpha-Beta Pruning
Full minimax search with alpha-beta cutoffs. Evaluates all horizontal, vertical, and diagonal 4-windows, with a center-column preference bonus. Search depth adapts automatically:

| AI win rate | Depth |
|---|---|
| < 30% (AI is losing) | 5 (harder) |
| 30–60% | 4 (balanced) |
| > 60% (AI dominates) | 3 (easier) |

#### MCTS (Monte Carlo Tree Search)
UCB1-guided selection, random rollout simulation, and backpropagation. Runs up to 2,500 iterations within a 350ms wall-clock budget per move.

#### DQN (Deep Q-Network)
A pretrained convolutional neural network that takes the board state as two binary channels (one per player) and outputs Q-values for each of the 7 columns. Invalid columns are masked with −∞ before argmax.

**Model architecture:**
```
Input:  (2, 6, 7)  — player channel + AI channel
Conv2D(2 → 32, 3×3, padding=1) → ReLU
Conv2D(32 → 64, 3×3, padding=1) → ReLU
Flatten → Linear(2688 → 256) → ReLU
Linear(256 → 7)                — Q-value per column
```

#### Learning Agent (Orchestrator)
Regardless of which engine is active, the LearningAgent:
- Observes which columns the player favors and occasionally contests the most-used column (if usage > 35%)
- Tracks mistakes and blunders by comparing board evaluations before and after each player move
- Persists all stats to SQLite so they accumulate across games and sessions

### Post-game Report

Navigate to `/game/connect4/report` after any game to see:
- Overall win/loss/draw record and AI win rate
- Current adaptive depth level
- Column preference heatmap (which columns the player favors)
- Last game: moves, mistakes, blunders, efficiency score, average search depth

---

## Module 3 — AI Tutor Chatbot

Navigate to `/learn` to open the tutor interface.

The tutor is powered by a local Ollama instance and is scoped to these topics:

- Search algorithms and their properties (optimality, completeness, time/space complexity)
- Heuristics (admissible vs inadmissible, Manhattan, Euclidean, etc.)
- Connect4 AI engines (minimax, alpha-beta, MCTS, DQN)
- AlgoArena-specific features and UI

Questions outside this scope are politely redirected. Temperature is set to 0.3 for factual, consistent answers with a 220-token response limit.

**Health check endpoint:**
```
GET /api/tutor/health
```
Returns Ollama connection status and available models.

---

## DQN Training

The pretrained weights in `models/dqn_connect4.pt` were generated by the self-play training script. To retrain from scratch:

```bash
python scripts/train_dqn.py
```

The script uses:
- **Self-play** — two instances of the DQN play against each other
- **Experience replay** — transitions stored in a fixed-size replay buffer
- **Epsilon-greedy exploration** — decaying over training episodes
- **Shaped rewards** — win: +1.0, loss: −1.0, draw: +0.1, invalid move: −1.0

Training runs on CPU by default. The output is saved to `models/dqn_connect4.pt` and is automatically loaded by the app at runtime.

---

## Database Schema

### `algoarena.db` — Game Database

```sql
-- Overall AI performance counters
ai_stats (id, games_played, ai_wins, player_wins, draws)

-- Per-column player behavior tracking
player_column_stats (col INTEGER PRIMARY KEY, count INTEGER)

-- Detailed per-game history
ai_game_history (
    game_id, result, moves, mistakes,
    blunders, efficiency, avg_depth
)
```

### `escalade3.db` — Visualizer Database

Stores each algorithm run as a JSON payload including `visited_order`, `path`, `stats`, and the generated `agent_report`.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Main menu |
| `GET` | `/visualizer` | Visualizer UI |
| `POST` | `/api/visualizer/run` | Run a search algorithm |
| `GET` | `/visualizer/report?run_id=N` | View a saved run report |
| `GET` | `/game/connect4` | Connect4 game UI |
| `POST` | `/api/connect4/new` | Start a new game (select AI mode) |
| `POST` | `/api/connect4/player-move` | Submit player move, get AI response |
| `GET` | `/game/connect4/report` | View post-game analytics |
| `GET` | `/learn` | AI Tutor UI |
| `POST` | `/api/tutor/chat` | Send a message to the tutor |
| `GET` | `/api/tutor/health` | Check Ollama connectivity |

### `POST /api/visualizer/run` — Request body

```json
{
  "grid": [[0,0,1,...], ...],
  "start": [0, 0],
  "goal": [9, 9],
  "algorithm": "astar",
  "heuristic": "manhattan",
  "params": { "weight": 1.6 }
}
```

### `POST /api/connect4/player-move` — Request body

```json
{ "column": 3 }
```

---

## Future Improvements

- [ ] Wire up `after_player_move()` in the game loop to enable live blunder detection
- [ ] Fix unreachable code block in `/api/visualizer/run` after early return
- [ ] Add algorithm comparison mode — run two algorithms side-by-side on the same grid
- [ ] Support 8-directional movement in the visualizer
- [ ] Add user accounts so stats persist across devices
- [ ] GPU support for DQN training (`DEVICE = "cuda"`)
- [ ] Export game reports and visualizer runs as PDF

---

## Author

Built as part of an algorithms and AI coursework project.

---

## License

This project is for educational purposes.
