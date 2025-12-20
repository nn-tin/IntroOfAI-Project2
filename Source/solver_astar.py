# Source/solver_astar.py
"""
A* SAT-based Solver for Hashiwokakero
Includes:
- node_expanded
- execution time
- peak memory usage (tracemalloc)
"""

import time
import heapq
import tracemalloc


class AStarSAT:
    def __init__(self, cnf, meta, timeout=180.0):
        self.meta = meta
        self.cnf = cnf
        self.timeout = timeout

        self.islands = meta["islands"]

        # ---------- STATIC HEURISTIC: sort edges ----------
        self.edges = sorted(
            meta["edges"],
            key=lambda e: (self.islands[e["u"]]["val"] + self.islands[e["v"]]["val"]),
            reverse=True
        )

        self.n_edges = len(self.edges)
        self.var_map = meta["var_map"]

        # ---------- Pre-compute connected edges ----------
        self.island_connected_edges = {i: [] for i in range(len(self.islands))}
        for idx, e in enumerate(self.edges):
            self.island_connected_edges[e["u"]].append(idx)
            self.island_connected_edges[e["v"]].append(idx)

        # ---------- Pre-compute crossings ----------
        self.crossing_pairs = self._find_crossing_pairs()

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
                    if v["r1"] < h["r"] < v["r2"] and h["c1"] < v["c"] < h["c2"]:
                        pairs.append((i, j))
        return pairs

    # ======================================================
    # Heuristic
    # ======================================================

    def heuristic(self, idx, current_degrees):
        """
        Return estimated remaining cost
        Return INF if dead-end detected
        """
        h_score = 0

        for isl_id, isl in enumerate(self.islands):
            needed = isl["val"] - current_degrees[isl_id]

            if needed == 0:
                continue
            if needed < 0:
                return float("inf")

            # ---------- Look-ahead pruning ----------
            potential = 0
            for edge_idx in self.island_connected_edges[isl_id]:
                if edge_idx >= idx:
                    potential += 2

            if needed > potential:
                return float("inf")

            h_score += needed

        return h_score

    # ======================================================
    # Solver
    # ======================================================

    def solve(self):
        tracemalloc.start()
        t0 = time.perf_counter()

        node_expanded = 0
        visited = set()
        pq = []

        start_degs = tuple([0] * len(self.islands))
        start_assign = tuple([0] * self.n_edges)
        start_h = self.heuristic(0, start_degs)

        heapq.heappush(
            pq, (start_h, start_h, 0, start_assign, start_degs)
        )

        while pq:
            # ---------- Timeout ----------
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

            f, h, idx, assigns, degs = heapq.heappop(pq)
            node_expanded += 1

            if h == float("inf"):
                continue

            # ---------- Goal ----------
            if idx == self.n_edges:
                if h == 0:
                    model = self._format_model(assigns)
                    current, peak = tracemalloc.get_traced_memory()
                    tracemalloc.stop()
                    return {
                        "solution": model,
                        "node_expanded": node_expanded,
                        "time": time.perf_counter() - t0,
                        "peak_memory": peak,
                        "success": True
                    }
                continue

            state_key = (idx, degs)
            if state_key in visited:
                continue
            visited.add(state_key)

            edge = self.edges[idx]
            u, v = edge["u"], edge["v"]

            # ---------- Branching: 0 / 1 / 2 ----------
            for val in (0, 1, 2):
                new_du = degs[u] + val
                new_dv = degs[v] + val

                # Degree pruning
                if new_du > self.islands[u]["val"] or new_dv > self.islands[v]["val"]:
                    continue

                # Crossing pruning
                if val > 0 and self._check_crossing(idx, assigns):
                    continue

                new_degs = list(degs)
                new_degs[u] = new_du
                new_degs[v] = new_dv
                new_degs = tuple(new_degs)

                new_h = self.heuristic(idx + 1, new_degs)
                if new_h == float("inf"):
                    continue

                new_assigns = list(assigns)
                new_assigns[idx] = val

                g = idx + 1
                f = g + new_h

                heapq.heappush(
                    pq,
                    (f, new_h, idx + 1, tuple(new_assigns), new_degs)
                )

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return {
            "solution": None,
            "node_expanded": node_expanded,
            "time": time.perf_counter() - t0,
            "peak_memory": peak,
            "success": False
        }

    # ======================================================
    # Helpers
    # ======================================================

    def _check_crossing(self, curr_idx, assigns):
        for i, j in self.crossing_pairs:
            other = j if i == curr_idx else i if j == curr_idx else -1
            if other != -1 and other < curr_idx:
                if assigns[other] > 0:
                    return True
        return False

    def _format_model(self, assignments):
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
