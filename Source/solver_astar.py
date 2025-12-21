import time
import heapq
import tracemalloc


class AStarSAT:
    def __init__(self, cnf, meta, timeout=180.0):
        self.meta = meta
        self.cnf = cnf
        self.timeout = timeout

        self.islands = meta["islands"]

        # --- TỐI ƯU 1: SẮP XẾP CẠNH (Heuristic Static) ---
        # Ưu tiên duyệt các cạnh nối với đảo có giá trị lớn (hoặc cô đơn)
        self.edges = sorted(
            meta["edges"],
            key=lambda e: (self.islands[e["u"]]["val"] + self.islands[e["v"]]["val"]),
            reverse=True
        )

        self.n_edges = len(self.edges)
        self.var_map = meta["var_map"]

        # Pre-compute connected edges cho mỗi đảo
        self.island_connected_edges = {i: [] for i in range(len(self.islands))}
        for idx, e in enumerate(self.edges):
            self.island_connected_edges[e["u"]].append(idx)
            self.island_connected_edges[e["v"]].append(idx)

        # Pre-compute crossing edges pairs
        self.crossing_pairs = self._find_crossing_pairs()

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

    def heuristic(self, idx, current_degrees):
        """
        Heuristic function:
        - Return estimated remaining cost (số cầu còn thiếu).
        - Return float('inf') if phát hiện nhánh cụt (pruning).
        """
        h_score = 0
        for isl_id, isl in enumerate(self.islands):
            needed = isl["val"] - current_degrees[isl_id]
            if needed == 0:
                continue
            if needed < 0:
                return float("inf")  # Quá tải cầu -> dead end

            # Look-ahead pruning: tính tổng tiềm năng số cầu có thể thêm từ cạnh chưa xét
            potential = 0
            connected_indices = self.island_connected_edges[isl_id]
            for edge_idx in connected_indices:
                if edge_idx >= idx:
                    potential += 2  # Mỗi cạnh max 2 cầu
            
            if needed > potential:
                return float("inf")  # Không đủ tiềm năng -> dead end

            h_score += needed

        return h_score

    def solve(self):
        start_degrees = tuple([0] * len(self.islands))
        start_h = self.heuristic(0, start_degrees)
        start_assign = tuple([0] * self.n_edges)

        pq = []
        # Push: (f, h, idx, assignments, degrees)
        heapq.heappush(pq, (start_h, start_h, 0, start_assign, start_degrees))

        tracemalloc.start()
        t0 = time.perf_counter()

        node_expanded = 0
        visited = set()

        while pq:
            # Timeout check
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

            if h == float("inf") or h >= 999999:
                continue  # Dead end pruning

            node_expanded += 1

            # Goal check: đã duyệt hết cạnh
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
                else:
                    continue

            # Memoization check
            state_key = (idx, degs)
            if state_key in visited:
                continue
            visited.add(state_key)

            edge = self.edges[idx]
            u, v = edge["u"], edge["v"]

            # Try assign values 0,1,2 for this edge
            for val in (0, 1, 2):
                new_du = degs[u] + val
                new_dv = degs[v] + val

                # Degree pruning: không vượt quá số cầu của đảo
                if new_du > self.islands[u]["val"] or new_dv > self.islands[v]["val"]:
                    continue

                # Crossing pruning: nếu val > 0 thì check crossing
                if val > 0 and self._check_crossing(idx, assigns):
                    continue

                new_degs_list = list(degs)
                new_degs_list[u] = new_du
                new_degs_list[v] = new_dv
                new_degs = tuple(new_degs_list)

                new_h = self.heuristic(idx + 1, new_degs)
                if new_h == float("inf") or new_h >= 999999:
                    continue

                new_g = idx + 1
                new_f = new_g + new_h

                new_assigns = list(assigns)
                new_assigns[idx] = val

                heapq.heappush(pq, (new_f, new_h, idx + 1, tuple(new_assigns), new_degs))

        # Nếu không tìm được lời giải
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return {
            "solution": None,
            "node_expanded": node_expanded,
            "time": time.perf_counter() - t0,
            "peak_memory": peak,
            "success": False
        }

    def _check_crossing(self, curr_idx, assigns):
        """
        Kiểm tra xem cạnh curr_idx có tạo crossing với các cạnh đã gán giá trị > 0 trước đó không
        """
        for i, j in self.crossing_pairs:
            other = j if i == curr_idx else i if j == curr_idx else -1
            if other != -1 and other < curr_idx:
                if assigns[other] > 0:
                    return True
        return False

    def _format_model(self, assignments):
        """
        Chuyển assignments theo self.edges (đã sort) về model theo var_map gốc
        """
        model = []
        for idx, val in enumerate(assignments):
            edge = self.edges[idx]
            # Tìm index gốc của edge trong meta["edges"]
            orig_idx = self.meta["edges"].index(edge)
            v1, v2 = self.var_map[orig_idx]
            if val == 0:
                model.extend([-v1, -v2])
            elif val == 1:
                model.extend([v1, -v2])
            elif val == 2:
                model.extend([v1, v2])
        return model
