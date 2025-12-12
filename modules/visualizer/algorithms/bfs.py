from collections import deque
from typing import Dict, List, Tuple

from .utils import Grid, Coord, get_neighbors, reconstruct_path


def run_bfs(grid: Grid, start: Coord, goal: Coord):
    """
    Classic BFS on a grid.
    Returns: dict with visited_order, path, stats
    """
    queue = deque()
    queue.append(start)
    visited = set([start])
    came_from: Dict[Coord, Coord] = {start: None}
    visited_order: List[Coord] = []

    found = False

    while queue:
        current = queue.popleft()
        visited_order.append(current)

        if current == goal:
            found = True
            break

        for neighbor in get_neighbors(grid, *current):
            if neighbor not in visited:
                visited.add(neighbor)
                came_from[neighbor] = current
                queue.append(neighbor)

    path = reconstruct_path(came_from, start, goal) if found else []

    stats = {
        "algorithm": "BFS",
        "found": found,
        "nodes_expanded": len(visited_order),
        "path_length": len(path),
    }

    return {
        "visited_order": visited_order,
        "path": path,
        "stats": stats,
    }
