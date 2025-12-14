# Source/solver_bruteforce.py
import sys

class BruteForceSAT:
    # Cập nhật: Thêm tham số timeout=None để khớp với main.py
    def __init__(self, cnf, meta, timeout=None):
        self.meta = meta
        self.edges = meta["edges"]
        self.islands = meta["islands"]
        self.n_edges = len(self.edges)
        self.var_map = meta["var_map"]
        self.timeout = timeout
        
        # Pre-compute crossing pairs
        self.crossing_pairs = self._find_crossing_pairs()

    def _find_crossing_pairs(self):
        pairs = []
        for i in range(self.n_edges):
            for j in range(i + 1, self.n_edges):
                e1 = self.edges[i]
                e2 = self.edges[j]
                if e1["type"] != e2["type"]:
                    h, v = (e1, e2) if e1["type"]=="H" else (e2, e1)
                    if v["r1"] < h["r"] < v["r2"] and h["c1"] < v["c"] < h["c2"]:
                        pairs.append((i, j))
        return pairs

    def solve(self):
        # Bắt đầu vét cạn từ cạnh 0
        assignments = [0] * self.n_edges
        return self._dfs(0, assignments)

    def _dfs(self, idx, assignments):
        # Base case: Đã điền xong tất cả các cạnh
        if idx == self.n_edges:
            if self._is_valid_solution(assignments):
                return self._format_model(assignments)
            return None

        # Thử lần lượt 0, 1, 2 cầu
        for val in [0, 1, 2]:
            assignments[idx] = val
            
            # 1. Pruning Crossing: Nếu cắt nhau -> Bỏ qua
            if val > 0 and self._has_conflict_crossing(idx, assignments):
                continue
            
            # 2. Pruning Overflow: Nếu quá tải đảo -> Bỏ qua
            # (Giúp input-01 chạy nhanh hơn, không bị treo)
            if self._is_island_overflow(idx, assignments):
                continue
            
            # Đệ quy
            res = self._dfs(idx + 1, assignments)
            if res: return res
        
        # Backtrack
        assignments[idx] = 0
        return None

    def _has_conflict_crossing(self, curr_idx, assignments):
        for (i, j) in self.crossing_pairs:
            other = -1
            if i == curr_idx: other = j
            elif j == curr_idx: other = i
            
            if other != -1 and other < curr_idx:
                if assignments[other] > 0:
                    return True
        return False

    def _is_island_overflow(self, curr_idx, assignments):
        edge = self.edges[curr_idx]
        u, v = edge["u"], edge["v"]
        
        deg_u = 0
        deg_v = 0
        
        # Chỉ tính tổng các cạnh đã gán (từ 0 đến curr_idx)
        for k in range(curr_idx + 1):
            val = assignments[k]
            if val > 0:
                ek = self.edges[k]
                if ek["u"] == u or ek["v"] == u: deg_u += val
                if ek["u"] == v or ek["v"] == v: deg_v += val
        
        if deg_u > self.islands[u]["val"]: return True
        if deg_v > self.islands[v]["val"]: return True
        return False

    def _is_valid_solution(self, assignments):
        current_degrees = [0] * len(self.islands)
        for idx, val in enumerate(assignments):
            if val > 0:
                e = self.edges[idx]
                current_degrees[e["u"]] += val
                current_degrees[e["v"]] += val
        
        for i, isl in enumerate(self.islands):
            if current_degrees[i] != isl["val"]:
                return False
        return True

    def _format_model(self, assignments):
        model = []
        for idx, val in enumerate(assignments):
            v1, v2 = self.var_map[idx]
            if val == 0: model.extend([-v1, -v2])
            elif val == 1: model.extend([v1, -v2])
            elif val == 2: model.extend([v1, v2])
        return model