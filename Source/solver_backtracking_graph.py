import time
from collections import deque

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

def is_valid_bridge(bridges, u, v, count, max_bridges):
    current = 0
    for b in bridges:
        if {b["u"], b["v"]} == {u, v}:
            current += b["count"]
    return current + count <= max_bridges

def backtrack(islands, edges, max_bridges, bridges, edge_idx, start_time, timeout, node_expanded):
    # Timeout check
    if timeout is not None and (time.perf_counter() - start_time) > timeout:
        return None, True

    node_expanded[0] += 1  # tăng đếm node mở rộng

    if is_solved(islands, bridges):
        if check_connectivity(islands, bridges):
            return bridges[:], False
        else:
            return None, False

    if edge_idx >= len(edges):
        return None, False

    deg = get_current_degrees(islands, bridges)
    for i, isl in enumerate(islands):
        if deg[i] > isl["value"]:
            return None, False  # prune

    e = edges[edge_idx]
    u, v = e["u"], e["v"]

    # Case 1: no bridge
    result, timed_out = backtrack(islands, edges, max_bridges, bridges, edge_idx + 1, start_time, timeout, node_expanded)
    if result is not None or timed_out:
        return result, timed_out

    # Case 2: add 1 or 2 bridges
    for c in (1, 2):
        if is_valid_bridge(bridges, u, v, c, max_bridges):
            if deg[u] + c <= islands[u]["value"] and deg[v] + c <= islands[v]["value"]:
                bridges.append({"u": u, "v": v, "count": c})
                result, timed_out = backtrack(islands, edges, max_bridges, bridges, edge_idx + 1, start_time, timeout, node_expanded)
                if result is not None or timed_out:
                    return result, timed_out
                bridges.pop()

    return None, False

class BacktrackingGraphSolver:
    def __init__(self, meta, timeout=180.0):
        # Normalize "val" -> "value" if needed
        for isl in meta.get("islands", []):
            if "val" in isl:
                isl["value"] = isl.pop("val")

        self.islands = meta["islands"]
        self.edges = meta["edges"]
        self.max_bridges = meta.get("max_bridges", 2)
        self.timeout = timeout

        self.node_expanded = 0
        self.start_time = None

    def solve(self):
        self.node_expanded = 0
        self.start_time = time.perf_counter()
        node_expanded = [0]  # dùng list để truyền tham chiếu đếm node

        result, timed_out = backtrack(
            self.islands,
            self.edges,
            self.max_bridges,
            [],
            0,
            self.start_time,
            self.timeout,
            node_expanded
        )
        elapsed = time.perf_counter() - self.start_time
        self.node_expanded = node_expanded[0]  # cập nhật node_expanded thực tế

        return {
            "solution": result,
            "success": result is not None and not timed_out,
            "timeout": timed_out,
            "node_expanded": self.node_expanded,
            "time": elapsed
        }
