"""
SAT Solver using bruteforce for Hashiwokakero

Metrics:
- node_expanded
- execution time
- peak memory usage
"""

import time
import tracemalloc


class BruteForceSAT:
    def __init__(self, cnf, meta, timeout=None):
        self.meta = meta
        self.edges = meta["edges"]
        self.islands = meta["islands"]
        self.n_edges = len(self.edges)
        self.var_map = meta["var_map"]
        self.timeout = timeout

        # ---------- Metrics ----------
        self.node_expanded = 0
        self.start_time = None

        # Pre-compute crossing pairs
        self.crossing_pairs = self._find_crossing_pairs()

    # ======================================================
    # Geometry pruning
    # ======================================================

    def _find_crossing_pairs(self):
        pairs = []
        for i in range(self.n_edges):
            for j in range(i + 1, self.n_edges):
                e1 = self.edges[i]
                e2 = self.edges[j]
                if e1["type"] != e2["type"]:
                    h, v = (e1, e2) if e1["type"] == "H" else (e2, e1)
                    if v["r1"] < h["r"] < v["r2"] and h["c1"] < v["c"] < h["c2"]:
                        pairs.append((i, j))
        return pairs

    # ======================================================
    # Public solve
    # ======================================================

    def solve(self):
        tracemalloc.start()
        self.start_time = time.perf_counter()

        assignments = [0] * self.n_edges
        model = self._dfs(0, assignments)

        elapsed = time.perf_counter() - self.start_time
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        return {
            "solution": model,
            "success": model is not None,
            "timeout": False if model else self._is_timeout(),
            "node_expanded": self.node_expanded,
            "time": elapsed,
            "peak_memory": peak
        }

    # ======================================================
    # DFS brute force
    # ======================================================

    def _dfs(self, idx, assignments):
        # ---------- Timeout ----------
        if self.timeout is not None:
            if time.perf_counter() - self.start_time > self.timeout:
                return None

        self.node_expanded += 1

        # ---------- Base case ----------
        if idx == self.n_edges:
            if self._is_valid_solution(assignments):
                return self._format_model(assignments)
            return None

        # ---------- Try 0,1,2 bridges ----------
        for val in (0, 1, 2):
            assignments[idx] = val

            # Pruning 1: crossing
            if val > 0 and self._has_conflict_crossing(idx, assignments):
                continue

            # Pruning 2: island overflow
            if self._is_island_overflow(idx, assignments):
                continue

            res = self._dfs(idx + 1, assignments)
            if res is not None:
                return res

        assignments[idx] = 0
        return None

    # ======================================================
    # Pruning helpers
    # ======================================================

    def _has_conflict_crossing(self, curr_idx, assignments):
        for (i, j) in self.crossing_pairs:
            other = -1
            if i == curr_idx:
                other = j
            elif j == curr_idx:
                other = i

            if other != -1 and other < curr_idx:
                if assignments[other] > 0:
                    return True
        return False

    def _is_island_overflow(self, curr_idx, assignments):
        edge = self.edges[curr_idx]
        u, v = edge["u"], edge["v"]

        deg_u = 0
        deg_v = 0

        for k in range(curr_idx + 1):
            val = assignments[k]
            if val > 0:
                ek = self.edges[k]
                if ek["u"] == u or ek["v"] == u:
                    deg_u += val
                if ek["u"] == v or ek["v"] == v:
                    deg_v += val

        if deg_u > self.islands[u]["val"]:
            return True
        if deg_v > self.islands[v]["val"]:
            return True
        return False

    # ======================================================
    # Solution validation
    # ======================================================

    def _is_valid_solution(self, assignments):
        deg = [0] * len(self.islands)
        for idx, val in enumerate(assignments):
            if val > 0:
                e = self.edges[idx]
                deg[e["u"]] += val
                deg[e["v"]] += val

        for i, isl in enumerate(self.islands):
            if deg[i] != isl["val"]:
                return False
        return True

    def _format_model(self, assignments):
        model = []
        for idx, val in enumerate(assignments):
            v1, v2 = self.var_map[idx]
            if val == 0:
                model.extend([-v1, -v2])
            elif val == 1:
                model.extend([v1, -v2])
            elif val == 2:
                model.extend([v1, v2])
        return model

    def _is_timeout(self):
        if self.timeout is None:
            return False
        return time.perf_counter() - self.start_time > self.timeout
