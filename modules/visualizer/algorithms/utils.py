from math import hypot
from typing import List, Tuple, Dict, Optional

Grid = List[List[int]]
Coord = Tuple[int, int]

# Cell types from front-end:
# 0 = empty, 1 = wall, 2 = start, 3 = goal


def in_bounds(grid: Grid, r: int, c: int) -> bool:
    return 0 <= r < len(grid) and 0 <= c < len(grid[0])


def is_walkable(grid: Grid, r: int, c: int) -> bool:
    return grid[r][c] != 1  # 1 = wall


def get_neighbors(grid: Grid, r: int, c: int) -> List[Coord]:
    candidates = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
    result = []
    for nr, nc in candidates:
        if in_bounds(grid, nr, nc) and is_walkable(grid, nr, nc):
            result.append((nr, nc))
    return result


def reconstruct_path(
    came_from: Dict[Coord, Optional[Coord]],
    start: Coord,
    goal: Coord,
) -> List[Coord]:
    if goal not in came_from:
        return []
    path = []
    current = goal
    while current is not None:
        path.append(current)
        if current == start:
            break
        current = came_from.get(current)
    path.reverse()
    return path


def manhattan(a: Coord, b: Coord) -> float:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def euclidean(a: Coord, b: Coord) -> float:
    return hypot(a[0] - b[0], a[1] - b[1])
