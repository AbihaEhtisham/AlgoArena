from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple
import heapq
import math
import random
import time
from collections import deque

Coord = Tuple[int, int]
Grid = List[List[int]]  # 0 empty, 1 wall, 2 start, 3 goal


def normalize_algo(name: str) -> str:
    n = (name or "").strip().lower()
    n = n.replace(" ", "").replace("-", "").replace("_", "")

    aliases = {
        "dffs": "dfs",
        "bidirectionalbfs": "bidir",
        "bidirectional": "bidir",
        "uniformcostsearch": "ucs",
        "uniformcost": "ucs",
        "weightedastar": "wastar",
        "beamsearch": "beam",
        "depthlimitedsearch": "dls",
        "iterativedeepeningdfs": "iddfs",
        "stochasticdfs": "sdfs",
        "randomwalk": "rwalk",
        "hillclimb": "hill",
        "hillclimbing": "hill",
        "randomrestarthillclimb": "rrhill",
        "randomrestarthillclimbing": "rrhill",
        "simulatedannealing": "anneal",
        "idastar": "idastar",
        "id a*": "idastar",
        "ida*": "idastar",
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
# Classic searches
# -------------------------

def bfs(grid: Grid, start: Coord, goal: Coord):
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


def dfs(grid: Grid, start: Coord, goal: Coord):
    stack = [start]
    parent = {start: None}
    visited_order = []
    seen = set()

    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        visited_order.append(cur)
        if cur == goal:
            break
        for nb in reversed(neighbors_4(grid, cur)):
            if nb not in parent:
                parent[nb] = cur
            stack.append(nb)
    return visited_order, parent


def ucs_or_dijkstra(grid: Grid, start: Coord, goal: Coord):
    pq = [(0, start)]
    parent = {start: None}
    dist = {start: 0}
    visited_order = []
    visited_set = set()

    while pq:
        g, cur = heapq.heappop(pq)
        if cur in visited_set:
            continue
        visited_set.add(cur)
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


# -------------------------
# DLS / IDDFS
# -------------------------

def dls(grid: Grid, start: Coord, goal: Coord, limit: int):
    stack = [(start, 0)]
    parent = {start: None}
    visited_order = []
    best_depth = {start: 0}

    while stack:
        cur, depth = stack.pop()
        visited_order.append(cur)
        if cur == goal:
            break
        if depth >= limit:
            continue

        for nb in reversed(neighbors_4(grid, cur)):
            nd = depth + 1
            if nb not in best_depth or nd < best_depth[nb]:
                best_depth[nb] = nd
                parent[nb] = cur
                stack.append((nb, nd))

    return visited_order, parent


def iddfs(grid: Grid, start: Coord, goal: Coord, max_depth: int = 80):
    total_visited = []
    final_parent = {start: None}

    for limit in range(max_depth + 1):
        visited_order, parent = dls(grid, start, goal, limit)
        total_visited.extend(visited_order)
        if goal in parent:
            final_parent = parent
            break

    return total_visited, final_parent


# -------------------------
# Bidirectional BFS
# -------------------------

def bidirectional_bfs(grid: Grid, start: Coord, goal: Coord):
    if start == goal:
        return [start], {start: None}

    q1 = deque([start])
    q2 = deque([goal])
    parent1 = {start: None}
    parent2 = {goal: None}
    visited_order = []
    meet = None

    while q1 and q2:
        for _ in range(len(q1)):
            cur = q1.popleft()
            visited_order.append(cur)
            for nb in neighbors_4(grid, cur):
                if nb not in parent1:
                    parent1[nb] = cur
                    q1.append(nb)
                    if nb in parent2:
                        meet = nb
                        break
            if meet:
                break
        if meet:
            break

        for _ in range(len(q2)):
            cur = q2.popleft()
            visited_order.append(cur)
            for nb in neighbors_4(grid, cur):
                if nb not in parent2:
                    parent2[nb] = cur
                    q2.append(nb)
                    if nb in parent1:
                        meet = nb
                        break
            if meet:
                break
        if meet:
            break

    if not meet:
        return visited_order, parent1

    path1 = reconstruct_path(parent1, start, meet)
    back = reconstruct_path(parent2, goal, meet)
    back.reverse()
    full_path = path1 + back[1:]

    parent = {start: None}
    for i in range(1, len(full_path)):
        parent[full_path[i]] = full_path[i - 1]

    return visited_order, parent


# -------------------------
# Informed: Greedy / A* / Weighted A*
# -------------------------

def greedy_best_first(grid: Grid, start: Coord, goal: Coord, h_fn):
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


def astar(grid: Grid, start: Coord, goal: Coord, h_fn):
    pq = [(h_fn(start, goal), 0, start)]  # (f,g,node)
    parent = {start: None}
    g_score = {start: 0}
    visited_order = []
    visited_set = set()

    while pq:
        _, g, cur = heapq.heappop(pq)
        if cur in visited_set:
            continue
        visited_set.add(cur)
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


def weighted_astar(grid: Grid, start: Coord, goal: Coord, h_fn, w: float):
    w = max(1.0, float(w))
    pq = [(w * h_fn(start, goal), 0, start)]
    parent = {start: None}
    g_score = {start: 0}
    visited_order = []
    visited_set = set()

    while pq:
        _, g, cur = heapq.heappop(pq)
        if cur in visited_set:
            continue
        visited_set.add(cur)
        visited_order.append(cur)

        if cur == goal:
            break

        for nb in neighbors_4(grid, cur):
            ng = g + 1
            if nb not in g_score or ng < g_score[nb]:
                g_score[nb] = ng
                parent[nb] = cur
                f = ng + w * h_fn(nb, goal)
                heapq.heappush(pq, (f, ng, nb))

    return visited_order, parent


# -------------------------
# IDA* (Iterative Deepening A*)
# -------------------------

def ida_star(grid: Grid, start: Coord, goal: Coord, h_fn, max_iters: int = 20000):
    visited_order: List[Coord] = []
    parent: Dict[Coord, Optional[Coord]] = {start: None}

    bound = h_fn(start, goal)

    def search(node: Coord, g: int, bound_val: float, seen: set) -> Tuple[float, bool]:
        f = g + h_fn(node, goal)
        if f > bound_val:
            return f, False
        visited_order.append(node)
        if node == goal:
            return f, True

        min_over = float("inf")
        for nb in neighbors_4(grid, node):
            if nb in seen:
                continue
            parent[nb] = node
            seen.add(nb)
            t, found = search(nb, g + 1, bound_val, seen)
            if found:
                return t, True
            min_over = min(min_over, t)
            seen.remove(nb)
        return min_over, False

    seen = set([start])
    for _ in range(max_iters):
        t, found = search(start, 0, bound, seen)
        if found:
            return visited_order, parent
        if t == float("inf"):
            break
        bound = t

    return visited_order, parent


# -------------------------
# Randomized: Stochastic DFS / Random Walk
# -------------------------

def stochastic_dfs(grid: Grid, start: Coord, goal: Coord, seed: Optional[int] = None):
    rng = random.Random(seed)
    stack = [start]
    parent = {start: None}
    visited_order = []
    seen = set()

    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        visited_order.append(cur)
        if cur == goal:
            break

        nbs = neighbors_4(grid, cur)
        rng.shuffle(nbs)
        for nb in nbs:
            if nb not in parent:
                parent[nb] = cur
            stack.append(nb)

    return visited_order, parent


def random_walk(grid: Grid, start: Coord, goal: Coord, max_steps: int = 800, seed: Optional[int] = None):
    rng = random.Random(seed)
    cur = start
    visited_order = [cur]
    parent = {start: None}

    for _ in range(max_steps):
        if cur == goal:
            break
        nbs = neighbors_4(grid, cur)
        if not nbs:
            break
        nxt = rng.choice(nbs)
        if nxt not in parent:
            parent[nxt] = cur
        cur = nxt
        visited_order.append(cur)

    return visited_order, parent


# -------------------------
# Local Search: Hill Climb / Random Restart / Simulated Annealing
# -------------------------

def steepest_hill_climb(grid: Grid, start: Coord, goal: Coord, h_fn, max_steps: int = 800):
    cur = start
    parent = {start: None}
    visited_order = [cur]

    for _ in range(max_steps):
        if cur == goal:
            break
        nbs = neighbors_4(grid, cur)
        if not nbs:
            break

        # pick neighbor with lowest heuristic
        best = min(nbs, key=lambda x: h_fn(x, goal))

        # if no improvement, stop (local min / plateau)
        if h_fn(best, goal) >= h_fn(cur, goal):
            break

        if best not in parent:
            parent[best] = cur
        cur = best
        visited_order.append(cur)

    return visited_order, parent


def random_restart_hill_climb(
    grid: Grid, start: Coord, goal: Coord, h_fn,
    restarts: int = 15, max_steps: int = 400, seed: Optional[int] = None
):
    rng = random.Random(seed)
    rows, cols = len(grid), len(grid[0])
    candidates = [(r, c) for r in range(rows) for c in range(cols) if not is_wall(grid, r, c)]

    best_parent = {start: None}
    best_visit = [start]
    best_end = start

    for _ in range(max(1, restarts)):
        s = start if rng.random() < 0.5 else rng.choice(candidates)
        visit, parent = steepest_hill_climb(grid, s, goal, h_fn, max_steps=max_steps)
        end = visit[-1] if visit else s

        if h_fn(end, goal) < h_fn(best_end, goal):
            best_end = end
            best_visit = visit if visit else [s]
            best_parent = parent

        if best_end == goal:
            break

    return best_visit, best_parent


def simulated_annealing(
    grid: Grid, start: Coord, goal: Coord, h_fn,
    max_steps: int = 800, temperature: float = 1.0, cooling: float = 0.995,
    seed: Optional[int] = None
):
    rng = random.Random(seed)
    cur = start
    parent = {start: None}
    visited_order = [cur]

    T = max(1e-6, float(temperature))
    cooling = float(cooling)

    def accept(delta: float, temp: float) -> bool:
        if delta < 0:
            return True
        return rng.random() < math.exp(-delta / max(1e-9, temp))

    for _ in range(max_steps):
        if cur == goal:
            break
        nbs = neighbors_4(grid, cur)
        if not nbs:
            break

        nxt = rng.choice(nbs)
        delta = h_fn(nxt, goal) - h_fn(cur, goal)  # >0 worse, <0 better

        if accept(delta, T):
            if nxt not in parent:
                parent[nxt] = cur
            cur = nxt
            visited_order.append(cur)

        T *= cooling
        if T < 1e-6:
            T = 1e-6

    return visited_order, parent


# -------------------------
# Beam Search (informed)
# -------------------------

def beam_search(grid: Grid, start: Coord, goal: Coord, h_fn, beam_width: int = 5, max_steps: int = 3000):
    K = max(1, int(beam_width))
    frontier = [start]
    parent = {start: None}
    visited_order = [start]
    seen = set([start])

    steps = 0
    while frontier and steps < max_steps:
        steps += 1
        if goal in frontier:
            break

        candidates = []
        for cur in frontier:
            for nb in neighbors_4(grid, cur):
                if nb not in seen:
                    seen.add(nb)
                    parent[nb] = cur
                    candidates.append(nb)
                    visited_order.append(nb)

        if not candidates:
            break

        candidates.sort(key=lambda x: h_fn(x, goal))
        frontier = candidates[:K]

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

    # Dispatch
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

    elif algo == "wastar":
        w = float(params.get("weight", 1.6))
        visited_order, parent = weighted_astar(grid, start, goal, h_fn, w)

    elif algo == "idastar":
        visited_order, parent = ida_star(grid, start, goal, h_fn)

    elif algo == "beam":
        bw = int(params.get("beam_width", 5))
        visited_order, parent = beam_search(grid, start, goal, h_fn, beam_width=bw)

    elif algo == "sdfs":
        visited_order, parent = stochastic_dfs(grid, start, goal)

    elif algo == "rwalk":
        steps = int(params.get("max_steps", 800))
        visited_order, parent = random_walk(grid, start, goal, max_steps=steps)

    elif algo == "hill":
        steps = int(params.get("max_steps", 800))
        visited_order, parent = steepest_hill_climb(grid, start, goal, h_fn, max_steps=steps)

    elif algo == "rrhill":
        steps = int(params.get("max_steps", 400))
        restarts = int(params.get("restarts", 15))
        visited_order, parent = random_restart_hill_climb(grid, start, goal, h_fn, restarts=restarts, max_steps=steps)

    elif algo == "anneal":
        steps = int(params.get("max_steps", 800))
        temp = float(params.get("temperature", 1.0))
        cooling = float(params.get("cooling", 0.995))
        visited_order, parent = simulated_annealing(grid, start, goal, h_fn, max_steps=steps, temperature=temp, cooling=cooling)

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
        "heuristic": heuristic if algo in ("astar", "greedy", "wastar", "idastar", "beam", "hill", "rrhill", "anneal") else None,
        "nodes_expanded": len(visited_order),
        "path_length": len(path) - 1 if found else 0,
        "found": found,
        "runtime_ms": round(ms, 2),
        "params": params,
    }

    return SearchResult(ok=True, visited_order=visited_order, path=path, stats=stats)
