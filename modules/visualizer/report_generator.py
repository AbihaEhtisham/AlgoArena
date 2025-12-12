from typing import Dict, Any


def generate_report(stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Takes algorithm run stats and returns a simple AI-style explanation.
    """
    algorithm = stats.get("algorithm", "Unknown")
    heuristic = stats.get("heuristic")
    found = stats.get("found", False)
    nodes_expanded = stats.get("nodes_expanded", 0)
    path_length = stats.get("path_length", 0)

    efficiency = (
        path_length / nodes_expanded if found and nodes_expanded else None
    )

    summary_lines = []

    if not found:
        summary_lines.append(
            f"{algorithm} could not find a path from start to goal in this grid."
        )
    else:
        summary_lines.append(
            f"{algorithm} successfully found a path with length {path_length}."
        )

    if algorithm == "BFS":
        summary_lines.append(
            "BFS explores nodes level by level, which guarantees the shortest path in terms of steps in an unweighted grid."
        )
    elif algorithm == "DFS":
        summary_lines.append(
            "DFS dives deep along one path before backtracking. It is not guaranteed to find the shortest path and can explore many unnecessary nodes."
        )
    elif algorithm == "A*":
        if heuristic == "euclidean":
            summary_lines.append(
                "A* used the Euclidean heuristic, which approximates straight-line distance to the goal."
            )
        else:
            summary_lines.append(
                "A* used the Manhattan heuristic, which works well on grids with 4-directional movement."
            )
        summary_lines.append(
            "A* balances path cost and heuristic estimation, often exploring fewer nodes than BFS while still finding optimal paths (with an admissible heuristic)."
        )

    if efficiency is not None:
        if efficiency < 0.2:
            efficiency_comment = (
                "The path was short relative to how many nodes were expanded, "
                "indicating a lot of exploration before finding the goal."
            )
        elif efficiency < 0.6:
            efficiency_comment = (
                "There was a moderate balance between exploration and path quality."
            )
        else:
            efficiency_comment = (
                "The search was quite efficient: most expanded nodes contributed directly to the final path."
            )
    else:
        efficiency_comment = (
            "Since no path was found, the search effort did not produce a usable route."
        )

    summary_lines.append(efficiency_comment)

    return {
        "algorithm": algorithm,
        "found": found,
        "nodes_expanded": nodes_expanded,
        "path_length": path_length,
        "heuristic": heuristic,
        "efficiency_ratio": round(efficiency, 3) if efficiency is not None else None,
        "summary_lines": summary_lines,
    }
