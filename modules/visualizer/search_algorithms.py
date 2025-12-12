from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple
import heapq
import math
import time
from collections import deque

Coord = Tuple[int, int]
Grid = List[List[int]]  # 0 empty, 1 wall, 2 start, 3 goal

def normalize_algo(name: str) -> str:
    # normalize for safety: casing, spaces, dashes
    n = (name or "").strip().lower()
    n = n.replace(" ", "").replace("-", "").replace("_", "")

    # common aliases/typos users pick up from UI labels
    aliases = {
        "dffs": "dfs",              # common typo
        "bidirectionalbfs": "bidir",
        "bidirectionalbfs": "bidir",
        "bidirectional": "bidir",
        "uniformcostsearch": "ucs",
        "uniformcost": "ucs",
        "weightedastar": "wastar",
        "wastar": "wastar",
        "idastar": "idastar",
        "id a*": "idastar",
        "id a": "idastar",
        "simulatedannealing": "anneal",
        "randomwalk": "rwalk",
        "stochasticdfs": "sdfs",
        "randomrestarthillclimb": "rrhill",
        "randomrestarthillclimbing": "rrhill",
        "hillclimb": "hill",
        "hillclimbing": "hill",
        "beamsearch": "beam",
        "depthlimitedsearch": "dls",
        "iterativedeepeningdfs": "iddfs",
        "iterativedeepeninga*": "idastar",
    }

    return aliases.get(n, n)

@dataclass
class SearchResult:
    ok: bool
    visited_order: List[Coord]
    path: List[Coord]
    stats: Dict


# -------------------------
# Helpers
# -------------------------

def in_bounds(r: int, c: int, rows: int, cols: int) -> bool:
    return 0 <= r < rows and 0 <= c < cols


def is_wall(grid: Grid, r: int, c: int) -> bool:
    return grid[r][c] == 1


def neighbors_4(grid: Grid, node: Coord) -> List[Coord]:
    rows, cols = len(grid), len(grid[0])
    r, c = node
    candidates = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
    out = []
    for nr, nc in candidates:
        if in_bounds(nr, nc, rows, cols) and not is_wall(grid, nr, nc):
            out.append((nr, nc))
    return out


def reconstruct_path(parent: Dict[Coord, Optional[Coord]], start: Coord, goal: Coord) -> List[Coord]:
    if goal not in parent:
        return []
    cur = goal
    path = []
    while cur is not None:
        path.append(cur)
        cur = parent.get(cur)
    path.reverse()
    if path and path[0] == start:
        return path
    return []


def h_manhattan(a: Coord, b: Coord) -> float:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def h_euclidean(a: Coord, b: Coord) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def get_heuristic_fn(name: str) -> Callable[[Coord, Coord], float]:
    if name == "euclidean":
        return h_euclidean
    return h_manhattan


# -------------------------
# Algorithms
# -------------------------

def bfs(grid: Grid, start: Coord, goal: Coord) -> Tuple[List[Coord], Dict[Coord, Optional[Coord]]]:
    q = deque([start])
    parent = {start: None}
    visited_order = [start]

    while q:
        cur = q.popleft()
        if cur == goal:
            break
        for nb in neighbors_4(grid, cur):
            if nb not in parent:
                parent[nb] = cur
                visited_order.append(nb)
                q.append(nb)
    return visited_order, parent


def dfs(grid: Grid, start: Coord, goal: Coord) -> Tuple[List[Coord], Dict[Coord, Optional[Coord]]]:
    stack = [start]
    parent = {start: None}
    visited_order = []

    while stack:
        cur = stack.pop()
        if cur in visited_order:
            continue
        visited_order.append(cur)
        if cur == goal:
            break
        # push neighbors in reverse so it looks consistent visually
        for nb in reversed(neighbors_4(grid, cur)):
            if nb not in parent:
                parent[nb] = cur
            stack.append(nb)

    return visited_order, parent


def ucs_or_dijkstra(grid: Grid, start: Coord, goal: Coord) -> Tuple[List[Coord], Dict[Coord, Optional[Coord]]]:
    """
    Uniform cost search on a grid where each move cost = 1.
    (Equivalent to Dijkstra.)
    """
    pq = [(0, start)]
    parent = {start: None}
    dist = {start: 0}
    visited_order = []

    while pq:
        g, cur = heapq.heappop(pq)
        if cur in visited_order:
            continue
        visited_order.append(cur)
        if cur == goal:
            break

        for nb in neighbors_4(grid, cur):
            ng = g + 1
            if nb not in dist or ng < dist[nb]:
                dist[nb] = ng
                parent[nb] = cur
                heapq.heappush(pq, (ng, nb))

    return visited_order, parent


def greedy_best_first(grid: Grid, start: Coord, goal: Coord, h_fn) -> Tuple[List[Coord], Dict[Coord, Optional[Coord]]]:
    pq = [(h_fn(start, goal), start)]
    parent = {start: None}
    seen = set([start])
    visited_order = []

    while pq:
        _, cur = heapq.heappop(pq)
        visited_order.append(cur)
        if cur == goal:
            break

        for nb in neighbors_4(grid, cur):
            if nb not in seen:
                seen.add(nb)
                parent[nb] = cur
                heapq.heappush(pq, (h_fn(nb, goal), nb))

    return visited_order, parent


def astar(grid: Grid, start: Coord, goal: Coord, h_fn) -> Tuple[List[Coord], Dict[Coord, Optional[Coord]]]:
    pq = [(h_fn(start, goal), 0, start)]  # (f, g, node)
    parent = {start: None}
    g_score = {start: 0}
    visited_order = []

    while pq:
        _, g, cur = heapq.heappop(pq)
        if cur in visited_order:
            continue
        visited_order.append(cur)

        if cur == goal:
            break

        for nb in neighbors_4(grid, cur):
            ng = g + 1
            if nb not in g_score or ng < g_score[nb]:
                g_score[nb] = ng
                parent[nb] = cur
                f = ng + h_fn(nb, goal)
                heapq.heappush(pq, (f, ng, nb))

    return visited_order, parent


def dls(grid: Grid, start: Coord, goal: Coord, limit: int) -> Tuple[List[Coord], Dict[Coord, Optional[Coord]]]:
    """
    Depth-limited search used by IDDFS.
    Returns visited order and parent map for reconstruction when goal found.
    """
    stack = [(start, 0)]
    parent = {start: None}
    visited_order = []
    visited_depth = {start: 0}

    while stack:
        cur, depth = stack.pop()
        visited_order.append(cur)
        if cur == goal:
            break
        if depth >= limit:
            continue

        for nb in reversed(neighbors_4(grid, cur)):
            nd = depth + 1
            if nb not in visited_depth or nd < visited_depth[nb]:
                visited_depth[nb] = nd
                parent[nb] = cur
                stack.append((nb, nd))

    return visited_order, parent


def iddfs(grid: Grid, start: Coord, goal: Coord, max_depth: int = 60) -> Tuple[List[Coord], Dict[Coord, Optional[Coord]]]:
    total_visited = []
    final_parent = {start: None}

    for limit in range(max_depth + 1):
        visited_order, parent = dls(grid, start, goal, limit)
        total_visited.extend(visited_order)

        if goal in parent:
            final_parent = parent
            break

    return total_visited, final_parent


def bidirectional_bfs(grid: Grid, start: Coord, goal: Coord) -> Tuple[List[Coord], Dict[Coord, Optional[Coord]]]:
    """
    Bidirectional BFS (uninformed). Reconstructs path via meeting point.
    """
    if start == goal:
        return [start], {start: None}

    q1 = deque([start])
    q2 = deque([goal])

    parent1 = {start: None}
    parent2 = {goal: None}

    visited_order = []

    meeting: Optional[Coord] = None

    while q1 and q2:
        # Expand from start side
        for _ in range(len(q1)):
            cur = q1.popleft()
            visited_order.append(cur)
            for nb in neighbors_4(grid, cur):
                if nb not in parent1:
                    parent1[nb] = cur
                    q1.append(nb)
                    if nb in parent2:
                        meeting = nb
                        break
            if meeting:
                break
        if meeting:
            break

        # Expand from goal side
        for _ in range(len(q2)):
            cur = q2.popleft()
            visited_order.append(cur)
            for nb in neighbors_4(grid, cur):
                if nb not in parent2:
                    parent2[nb] = cur
                    q2.append(nb)
                    if nb in parent1:
                        meeting = nb
                        break
            if meeting:
                break

        if meeting:
            break

    if not meeting:
        # no connection
        return visited_order, parent1

    # Build combined parent map for standard reconstruct
    # Path: start -> meeting using parent1; meeting -> goal using parent2
    # parent2 stores edges from goal backward; we need forward from meeting to goal
    path1 = reconstruct_path(parent1, start, meeting)
    # reconstruct from goal to meeting then reverse
    back = reconstruct_path(parent2, goal, meeting)
    back.reverse()  # meeting -> goal

    full_path = path1 + back[1:]  # avoid duplicating meeting node

    # create a parent map that represents the final path (optional)
    parent = {start: None}
    for i in range(1, len(full_path)):
        parent[full_path[i]] = full_path[i - 1]

    return visited_order, parent


# -------------------------
# Public runner
# -------------------------

def run_search(
    grid: Grid,
    start: Coord,
    goal: Coord,
    algorithm: str,
    heuristic: str,
    params: Optional[Dict] = None
) -> SearchResult:
    params = params or {}
    t0 = time.perf_counter()

    h_fn = get_heuristic_fn(heuristic)
    algo = normalize_algo(algorithm)

    visited_order: List[Coord] = []
    parent: Dict[Coord, Optional[Coord]] = {start: None}

    # ---- Dispatch ----
    if algo == "bfs":
        visited_order, parent = bfs(grid, start, goal)

    elif algo == "dfs":
        visited_order, parent = dfs(grid, start, goal)

    elif algo == "dls":
        limit = int(params.get("depth_limit", 25))
        visited_order, parent = dls(grid, start, goal, limit)

    elif algo == "iddfs":
        max_depth = int(params.get("depth_limit", 80))
        visited_order, parent = iddfs(grid, start, goal, max_depth=max_depth)

    elif algo in ("ucs", "dijkstra"):
        visited_order, parent = ucs_or_dijkstra(grid, start, goal)

    elif algo == "bidir":
        visited_order, parent = bidirectional_bfs(grid, start, goal)

    elif algo == "greedy":
        visited_order, parent = greedy_best_first(grid, start, goal, h_fn)

    elif algo == "astar":
        visited_order, parent = astar(grid, start, goal, h_fn)

    # If you haven't added these functions yet, DON'T include them here.
    # Add them only once you implement them:
    # elif algo == "wastar": ...
    # elif algo == "idastar": ...
    # elif algo == "beam": ...
    # elif algo == "sdfs": ...
    # elif algo == "rwalk": ...
    # elif algo == "hill": ...
    # elif algo == "rrhill": ...
    # elif algo == "anneal": ...

    else:
        return SearchResult(
            ok=False,
            visited_order=[],
            path=[],
            stats={"error": f"Unknown algorithm '{algorithm}' (normalized: '{algo}')"},
        )

    path = reconstruct_path(parent, start, goal)
    found = len(path) > 0

    t1 = time.perf_counter()
    ms = (t1 - t0) * 1000.0

    stats = {
        "algorithm": algo,
        "heuristic": heuristic if algo in ("astar", "greedy") else None,
        "nodes_expanded": len(visited_order),
        "path_length": len(path) - 1 if found else 0,
        "found": found,
        "runtime_ms": round(ms, 2),
        "params": params,
    }

    return SearchResult(ok=True, visited_order=visited_order, path=path, stats=stats)
