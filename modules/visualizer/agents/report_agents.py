from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple
import math
from collections import Counter

Coord = Tuple[int, int]

@dataclass
class AgentOutput:
    name: str
    summary: str
    insights: List[str]
    metrics: Dict


def _path_length(path: List[Coord]) -> int:
    return max(0, len(path) - 1)


def _unique_count(seq: List[Coord]) -> int:
    return len(set(seq))


def _estimate_branching(visited: List[Coord]) -> float:
    # rough: unique expansions vs depth proxy
    if not visited:
        return 0.0
    unique = _unique_count(visited)
    # log proxy (not perfect, but useful)
    return round(math.pow(max(unique, 1), 1/4), 2)


def _revisit_rate(visited: List[Coord]) -> float:
    if not visited:
        return 0.0
    total = len(visited)
    unique = _unique_count(visited)
    return round((total - unique) / total * 100.0, 2)


def _efficiency_ratio(visited: List[Coord], path: List[Coord]) -> float:
    # visited per step on final path
    pl = _path_length(path)
    if pl <= 0:
        return float("inf") if visited else 0.0
    return round(len(visited) / pl, 3)


def _detour_ratio(path: List[Coord], heuristic_lb: float) -> float:
    pl = _path_length(path)
    if pl <= 0 or heuristic_lb <= 0:
        return 0.0
    return round(pl / heuristic_lb, 3)


def analyzer_agent(run: Dict) -> AgentOutput:
    algo = run["algorithm"]
    heuristic = run.get("heuristic")
    visited = run.get("visited_order", [])
    path = run.get("path", [])
    start = tuple(run.get("start", (0,0)))
    goal = tuple(run.get("goal", (0,0)))

    # heuristic lower bound using Manhattan
    h_lb = abs(start[0]-goal[0]) + abs(start[1]-goal[1])

    metrics = {
        "nodes_expanded": len(visited),
        "unique_nodes": _unique_count(visited),
        "revisit_rate_%": _revisit_rate(visited),
        "path_length": _path_length(path),
        "efficiency_visited_per_step": _efficiency_ratio(visited, path),
        "detour_ratio_vs_manhattan": _detour_ratio(path, h_lb),
        "branching_factor_est": _estimate_branching(visited),
    }

    insights = []
    if metrics["path_length"] == 0:
        insights.append("No path was found. Try reducing walls or changing algorithm/heuristic.")
    else:
        if metrics["efficiency_visited_per_step"] > 20:
            insights.append("Exploration was heavy relative to the final path → algorithm searched broadly before committing.")
        if metrics["detour_ratio_vs_manhattan"] > 1.8:
            insights.append("The found path is much longer than the straight-line lower bound → maze geometry forces detours.")
        if metrics["revisit_rate_%"] > 5:
            insights.append("Noticeable revisits/duplicates occurred → likely due to local search/randomness or repeated frontier candidates.")

    summary = f"Computed core metrics for {algo.upper()} ({heuristic or 'no heuristic'})."
    return AgentOutput("AnalyzerAgent", summary, insights, metrics)


def coach_agent(run: Dict, analysis: AgentOutput) -> AgentOutput:
    algo = run["algorithm"]
    heuristic = run.get("heuristic")
    m = analysis.metrics

    insights = []
    if algo in ("bfs", "ucs", "dijkstra"):
        insights.append("This algorithm expands outward layer-by-layer (or cost-by-cost), so it tends to explore many nodes before reaching goal.")
    if algo in ("dfs", "dls", "iddfs"):
        insights.append("Depth-first style tends to dive deep and can miss shorter routes early; limits (DLS/IDDFS) control this behavior.")
    if algo in ("greedy",):
        insights.append("Greedy best-first uses only h(n), so it looks smart but can get trapped into detours.")
    if algo in ("astar", "wastar", "idastar"):
        insights.append("A* balances g(n) + h(n). Better heuristics reduce exploration while keeping direction toward goal.")
    if algo in ("beam",):
        insights.append("Beam search keeps only the best K frontier nodes, trading optimality for speed (visual: multiple parallel paths).")
    if algo in ("anneal", "hill", "rrhill", "rwalk", "sdfs"):
        insights.append("This is a local/randomized strategy; results can vary per run. Use repeat runs to see performance trends.")

    # turn numbers into explanation
    insights.append(f"Efficiency: visited {m['efficiency_visited_per_step']} nodes per path step.")
    if m["path_length"] > 0:
        insights.append(f"Detour ratio vs Manhattan lower bound: {m['detour_ratio_vs_manhattan']} (1.0 is perfectly direct).")

    summary = f"Explained behavior + tradeoffs of {algo.upper()} and how the selected heuristic influences it."
    return AgentOutput("StrategyCoachAgent", summary, insights, {})


def comparator_agent(current: Dict, previous: Dict | None, analysis: AgentOutput) -> AgentOutput:
    if not previous:
        return AgentOutput(
            "ComparatorAgent",
            "No previous run available for comparison.",
            ["Run another algorithm on the same maze to generate comparative insights."],
            {}
        )

    cur_m = analysis.metrics
    prev_analysis = analyzer_agent(previous).metrics

    insights = []
    def delta(a, b): 
        try: return round(a - b, 3)
        except: return None

    insights.append(f"Nodes expanded change: {delta(cur_m['nodes_expanded'], prev_analysis['nodes_expanded'])}")
    insights.append(f"Path length change: {delta(cur_m['path_length'], prev_analysis['path_length'])}")
    insights.append(f"Efficiency change (visited/step): {delta(cur_m['efficiency_visited_per_step'], prev_analysis['efficiency_visited_per_step'])}")

    summary = "Compared this run with the most recent previous run to highlight improvements/tradeoffs."
    metrics = {"previous_run_id": previous.get("id")}
    return AgentOutput("ComparatorAgent", summary, insights, metrics)


def narrator_agent(run: Dict, outputs: List[AgentOutput]) -> Dict:
    algo = (run.get("algorithm") or "unknown").upper()
    heur = run.get("heuristic") or "None"

    # Build agent sections (clean, no ugly [AgentName])
    agent_sections = []
    merged_metrics = {}

    for o in outputs:
        merged_metrics.update(o.metrics or {})
        agent_sections.append({
            "agent_name": o.name,
            "agent_title": {
                "AnalyzerAgent": "Run Analyzer",
                "StrategyCoachAgent": "Strategy Coach",
                "ComparatorAgent": "Performance Comparator"
            }.get(o.name, o.name),
            "summary": o.summary,
            "insights": o.insights or []
        })

    # Add extra "learning outcomes" block (for end semester feel)
    learning_outcomes = []
    if merged_metrics.get("path_length", 0) > 0:
        eff = merged_metrics.get("efficiency_visited_per_step", None)
        detour = merged_metrics.get("detour_ratio_vs_manhattan", None)

        if eff is not None:
            if eff <= 3.5:
                learning_outcomes.append("The search was efficient: it explored only a few nodes for each step of the final path.")
            elif eff <= 8:
                learning_outcomes.append("Moderate exploration: the algorithm explored a noticeable portion of the grid before locking onto the solution.")
            else:
                learning_outcomes.append("Heavy exploration: the algorithm searched broadly, which is expected for uninformed methods or poor heuristics.")

        if detour is not None:
            if detour <= 1.2:
                learning_outcomes.append("The maze allowed a nearly direct route (path close to theoretical straight-line lower bound).")
            elif detour <= 2.0:
                learning_outcomes.append("The maze forced detours: walls/structure pushed the path away from the direct route.")
            else:
                learning_outcomes.append("The maze structure strongly constrained movement, forcing major detours.")

    else:
        learning_outcomes.append("No solution path was found. This suggests either the maze is blocked or the depth/steps constraints were too tight.")

    # Build final formatted report object for UI
    return {
        "title": f"AI Visualizer Report — {algo}",
        "algorithm": run.get("algorithm"),
        "heuristic": heur,
        "high_level": (
            f"The AI agent analyzed your run of {algo}. "
            f"It computed efficiency, detours, revisits, and inferred what this teaches about the algorithm."
        ),
        "metrics": merged_metrics,
        "agent_sections": agent_sections,
        "learning_outcomes": learning_outcomes,
        "study_notes": [
            "Run BFS and A* on the same maze to see how heuristics reduce exploration.",
            "Try Weighted A* with different weights to see speed vs optimality tradeoff.",
            "Compare Random Walk / Hill-Climbing across multiple runs (variance is part of the lesson)."
        ]
    }



def generate_multiagent_report(run: Dict, previous_run: Dict | None = None) -> Dict:
    analysis = analyzer_agent(run)
    coach = coach_agent(run, analysis)
    comp = comparator_agent(run, previous_run, analysis)
    report = narrator_agent(run, [analysis, coach, comp])
    return report
