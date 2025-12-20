# Source/solver_backtracking.py
"""
SAT Solver using Backtracking for Hashiwokakero
Includes:
- node_expanded
- execution time
- peak memory usage (tracemalloc)
"""

import time
import tracemalloc


class BacktrackingSAT:
    def __init__(self, cnf, meta, timeout=None):
        self.meta = meta
        self.islands = meta["islands"]
        self.timeout = timeout

        # ---------- Sort edges (heuristic) ----------
        self.edges = sorted(
            meta["edges"],
            key=lambda e: self.islands[e["u"]]["val"] + self.islands[e["v"]]["val"]
        )

        self.n_edges = len(self.edges)
        self.var_map = meta["var_map"]

        # ---------- Pre-compute crossings ----------
        self.crossing_pairs = self._find_crossing_pairs()

        # ---------- Metrics ----------
        self.node_expanded = 0
        self.start_time = None

    # ======================================================
    # Pre-processing
    # ======================================================

    def _find_crossing_pairs(self):
        pairs = []
        for i in range(self.n_edges):
            for j in range(i + 1, self.n_edges):
                e1, e2 = self.edges[i], self.edges[j]
                if e1["type"] != e2["type"]:
                    h, v = (e1, e2) if e1["type"] == "H" else (e2, e1)
                    if v["r1"] < h["r"] < v["r2"] and h["c1"] < h["c2"]:
                        if h["c1"] < v["c"] < h["c2"]:
                            pairs.append((i, j))
        return pairs

    # ======================================================
    # Solver
    # ======================================================

    def solve(self):
        tracemalloc.start()
        self.start_time = time.perf_counter()

        assignments = [0] * self.n_edges
        current_degrees = [0] * len(self.islands)

        model = self._backtrack(0, assignments, current_degrees)

        elapsed = time.perf_counter() - self.start_time
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        return {
            "solution": model,
            "node_expanded": self.node_expanded,
            "time": elapsed,
            "peak_memory": peak,
            "success": model is not None
        }

    def _backtrack(self, edge_idx, assignments, current_degrees):
        # ---------- Timeout ----------
        if self.timeout is not None:
            if time.perf_counter() - self.start_time > self.timeout:
                return None

        self.node_expanded += 1

        # ---------- Base case ----------
        if edge_idx == self.n_edges:
            for i, isl in enumerate(self.islands):
                if current_degrees[i] != isl["val"]:
                    return None
            return self._format_model_safe(assignments)

        edge = self.edges[edge_idx]
        u, v = edge["u"], edge["v"]

        limit_u = self.islands[u]["val"]
        limit_v = self.islands[v]["val"]

        # ---------- Try assignments ----------
        for val in (0, 1, 2):
            if current_degrees[u] + val > limit_u:
                continue
            if current_degrees[v] + val > limit_v:
                continue

            if val > 0 and self._check_crossing(edge_idx, assignments):
                continue

            assignments[edge_idx] = val
            current_degrees[u] += val
            current_degrees[v] += val

            res = self._backtrack(edge_idx + 1, assignments, current_degrees)
            if res is not None:
                return res

            # ---------- Backtrack ----------
            assignments[edge_idx] = 0
            current_degrees[u] -= val
            current_degrees[v] -= val

        return None

    # ======================================================
    # Helpers
    # ======================================================

    def _check_crossing(self, curr_idx, assignments):
        for i, j in self.crossing_pairs:
            other = j if i == curr_idx else i if j == curr_idx else -1
            if other != -1 and other < curr_idx:
                if assignments[other] > 0:
                    return True
        return False

    def _format_model_safe(self, assignments):
        model = []
        for idx, val in enumerate(assignments):
            edge = self.edges[idx]
            orig_idx = self.meta["edges"].index(edge)

            v1, v2 = self.var_map[orig_idx]
            if val == 0:
                model.extend([-v1, -v2])
            elif val == 1:
                model.extend([v1, -v2])
            elif val == 2:
                model.extend([v1, v2])
        return model
