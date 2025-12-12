import heapq
from typing import Dict, List, Tuple, Callable

from .utils import (
    Grid,
    Coord,
    get_neighbors,
    reconstruct_path,
    manhattan,
    euclidean,
)


def get_heuristic_fn(name: str) -> Callable[[Coord, Coord], float]:
    name = (name or "").lower()
    if name == "euclidean":
        return euclidean
    # default:
    return manhattan


def run_astar(grid: Grid, start: Coord, goal: Coord, heuristic_name: str = "manhattan"):
    """
    A* search on a grid.
    """
    h = get_heuristic_fn(heuristic_name)

    open_set = []
    heapq.heappush(open_set, (0, start))

    g_score: Dict[Coord, float] = {start: 0.0}
    came_from: Dict[Coord, Coord] = {start: None}
    visited_order: List[Coord] = []
    visited_set = set()

    found = False

    while open_set:
        _, current = heapq.heappop(open_set)

        if current in visited_set:
            continue
        visited_set.add(current)
        visited_order.append(current)

        if current == goal:
            found = True
            break

        for neighbor in get_neighbors(grid, *current):
            tentative_g = g_score[current] + 1  # uniform cost

            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score = tentative_g + h(neighbor, goal)
                heapq.heappush(open_set, (f_score, neighbor))

    path = reconstruct_path(came_from, start, goal) if found else []

    stats = {
        "algorithm": "A*",
        "heuristic": heuristic_name,
        "found": found,
        "nodes_expanded": len(visited_order),
        "path_length": len(path),
    }

    return {
        "visited_order": visited_order,
        "path": path,
        "stats": stats,
    }
