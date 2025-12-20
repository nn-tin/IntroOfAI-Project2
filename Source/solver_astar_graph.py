"""
A* Solver for Hashiwokakero using Graph Search
(Non-SAT, pure graph-based A*)
Includes:
- Node expanded counting
- Execution time
- Peak memory usage (tracemalloc)
"""

import time
import heapq
import tracemalloc
from collections import deque

# ---------- Helper functions ----------

def check_connectivity(islands, bridges):
    if not islands:
        return True
    if not bridges and len(islands) > 1:
        return False

    n = len(islands)
    adj = {i: set() for i in range(n)}
    for b in bridges:
        adj[b["u"]].add(b["v"])
        adj[b["v"]].add(b["u"])

    visited = set()
    queue = deque([0])
    while queue:
        u = queue.popleft()
        if u in visited:
            continue
        visited.add(u)
        for v in adj[u]:
            if v not in visited:
                queue.append(v)

    return len(visited) == n


def is_solved(islands, bridges):
    degree = [0] * len(islands)
    for b in bridges:
        degree[b["u"]] += b["count"]
        degree[b["v"]] += b["count"]
    return all(degree[i] == isl["value"] for i, isl in enumerate(islands))


def get_current_degrees(islands, bridges):
    deg = [0] * len(islands)
    for b in bridges:
        deg[b["u"]] += b["count"]
        deg[b["v"]] += b["count"]
    return deg


def bridges_to_tuple(bridges):
    # Chuẩn hóa trạng thái để so sánh trong visited set
    return tuple(sorted((min(b["u"], b["v"]), max(b["u"], b["v"]), b["count"]) for b in bridges))


# ---------- A* heuristic ----------

def calculate_heuristic(islands, bridges, degrees):
    remaining = 0
    for i, isl in enumerate(islands):
        if degrees[i] > isl["value"]:
            return float("inf")
        remaining += isl["value"] - degrees[i]

    # Connectivity heuristic: số thành phần liên thông chưa hoàn chỉnh
    n = len(islands)
    adj = {i: set() for i in range(n)}
    for b in bridges:
        adj[b["u"]].add(b["v"])
        adj[b["v"]].add(b["u"])

    visited = set()
    components = 0
    for i in range(n):
        if degrees[i] < islands[i]["value"] and i not in visited:
            components += 1
            q = deque([i])
            visited.add(i)
            while q:
                u = q.popleft()
                for v in adj[u]:
                    if v not in visited:
                        visited.add(v)
                        q.append(v)

    return remaining / 2 + max(0, components - 1)


# ---------- Successor generation ----------

def get_successors(islands, edges, max_bridges, bridges, degrees):
    # Chọn đảo đầu tiên có degree chưa đủ cầu
    idx = next((i for i in range(len(islands)) if degrees[i] < islands[i]["value"]), -1)
    if idx == -1:
        return []

    successors = []
    for e in edges:
        if idx not in (e["u"], e["v"]):
            continue

        u, v = e["u"], e["v"]

        # Nếu 1 trong 2 đảo đã đủ cầu thì skip
        if degrees[u] == islands[u]["value"] or degrees[v] == islands[v]["value"]:
            continue

        existing = next((b["count"] for b in bridges if {b["u"], b["v"]} == {u, v}), 0)
        if existing >= max_bridges:
            continue

        for add in (1, 2):
            # Nếu chưa có cầu hoặc chỉ thêm 1 cầu, kiểm tra điều kiện
            if existing == 0 or add == 1:
                if (degrees[u] + add <= islands[u]["value"] and
                        degrees[v] + add <= islands[v]["value"]):
                    nb = [b for b in bridges if {b["u"], b["v"]} != {u, v}]
                    nb.append({"u": u, "v": v, "count": existing + add})
                    successors.append(nb)

    return successors


# ---------- Solver class ----------

class AStarGraphSolver:
    def __init__(self, meta, timeout=60.0):
        # Tiền xử lý: chuyển "val" thành "value" nếu có
        for isl in meta.get("islands", []):
            if "val" in isl:
                isl["value"] = isl.pop("val")

        self.islands = meta["islands"]
        self.edges = meta["edges"]
        self.max_bridges = meta.get("max_bridges", 2)
        self.timeout = timeout

    def solve(self):
        tracemalloc.start()
        t0 = time.perf_counter()

        pq = []
        visited = set()
        node_expanded = 0
        counter = 0  # để tránh lỗi so sánh dict

        start = []
        deg0 = get_current_degrees(self.islands, start)
        h0 = calculate_heuristic(self.islands, start, deg0)
        heapq.heappush(pq, (h0, 0, counter, start))
        counter += 1

        while pq:
            if time.perf_counter() - t0 > self.timeout:
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                return {
                    "solution": None,
                    "node_expanded": node_expanded,
                    "time": time.perf_counter() - t0,
                    "peak_memory": peak,
                    "success": False
                }

            _, g, _, bridges = heapq.heappop(pq)
            node_expanded += 1

            state = bridges_to_tuple(bridges)
            if state in visited:
                continue
            visited.add(state)

            degrees = get_current_degrees(self.islands, bridges)

            if is_solved(self.islands, bridges) and check_connectivity(self.islands, bridges):
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                return {
                    "solution": bridges,
                    "node_expanded": node_expanded,
                    "time": time.perf_counter() - t0,
                    "peak_memory": peak,
                    "success": True
                }

            for nb in get_successors(self.islands, self.edges, self.max_bridges, bridges, degrees):
                nd = get_current_degrees(self.islands, nb)
                h = calculate_heuristic(self.islands, nb, nd)
                if h < float("inf"):
                    g2 = sum(b["count"] for b in nb)
                    heapq.heappush(pq, (g2 + h, g2, counter, nb))
                    counter += 1

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return {
            "solution": None,
            "node_expanded": node_expanded,
            "time": time.perf_counter() - t0,
            "peak_memory": peak,
            "success": False
        }
