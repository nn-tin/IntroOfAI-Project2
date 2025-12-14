# Source/solver_astar.py
import heapq

class AStarSAT:
    def __init__(self, cnf, meta):
        self.meta = meta
        self.islands = meta["islands"]
        
        # --- TỐI ƯU 1: SẮP XẾP CẠNH (Heuristic Static) ---
        # Ưu tiên duyệt các cạnh nối với đảo có giá trị lớn hoặc đảo "cô đơn" (ít hàng xóm)
        # Giống như chiến thuật điền Sudoku: điền ô khó trước.
        self.edges = sorted(
            meta["edges"], 
            key=lambda e: (self.islands[e["u"]]["val"] + self.islands[e["v"]]["val"]),
            reverse=True # Ưu tiên đảo lớn trước
        )
        
        self.n_edges = len(self.edges)
        self.var_map = meta["var_map"]
        
        # Pre-compute neighbors cho việc tính toán nhanh
        self.island_connected_edges = {i: [] for i in range(len(self.islands))}
        for idx, e in enumerate(self.edges): # Lưu ý: dùng index của list đã sort
            self.island_connected_edges[e["u"]].append(idx)
            self.island_connected_edges[e["v"]].append(idx)

        # Pre-compute crossing (dựa trên edges đã sort)
        self.crossing_pairs = self._find_crossing_pairs()

    def _find_crossing_pairs(self):
        pairs = []
        for i in range(self.n_edges):
            for j in range(i + 1, self.n_edges):
                e1, e2 = self.edges[i], self.edges[j]
                if e1["type"] != e2["type"]:
                    h, v = (e1, e2) if e1["type"]=="H" else (e2, e1)
                    if v["r1"] < h["r"] < v["r2"] and h["c1"] < v["c"] < h["c2"]:
                        pairs.append((i, j))
        return pairs

    def heuristic(self, idx, current_degrees):
        """
        Hàm heuristic nâng cao:
        1. Trả về chi phí ước lượng (số cầu còn thiếu).
        2. Trả về INFINITY nếu phát hiện nhánh cụt (Pruning).
        """
        h_score = 0
        
        for isl_id, isl in enumerate(self.islands):
            needed = isl["val"] - current_degrees[isl_id]
            
            if needed == 0: continue
            if needed < 0: return 999999 # Đã bị thừa cầu -> Cắt nhánh
            
            # --- TỐI ƯU 2: LOOK-AHEAD PRUNING ---
            # Tính "tiềm năng" còn lại của đảo này từ các cạnh CHƯA DUYỆT (index > idx)
            potential = 0
            connected_indices = self.island_connected_edges[isl_id]
            
            for edge_idx in connected_indices:
                if edge_idx >= idx: # Cạnh này chưa được quyết định
                    potential += 2 # Mỗi cạnh tối đa đóng góp 2 cầu
            
            # Nếu số cầu hiện tại + tất cả tiềm năng tương lai vẫn KHÔNG ĐỦ
            # -> Nhánh này vô vọng (Dead end) -> Cắt nhánh ngay!
            if needed > potential:
                return 999999
            
            h_score += needed
            
        return h_score

    def solve(self):
        # Priority Queue
        start_degrees = tuple([0] * len(self.islands))
        start_h = self.heuristic(0, start_degrees) # idx=0
        start_assign = tuple([0] * self.n_edges)
        
        pq = []
        # Push: (f, h, idx, assignments, degrees)
        # idx: index của cạnh sắp xét
        heapq.heappush(pq, (start_h, start_h, 0, start_assign, start_degrees))
        
        visited = set()

        while pq:
            f, h, idx, assigns, degs = heapq.heappop(pq)
            
            # Nếu h quá lớn nghĩa là nhánh cụt (do Look-ahead phát hiện)
            if h >= 999999: continue

            # Base case: Đã duyệt hết cạnh
            if idx == self.n_edges:
                if h == 0: return self._format_model(assigns)
                else: continue

            # Visited check (Memoization)
            state_key = (idx, degs)
            if state_key in visited: continue
            visited.add(state_key)

            # Thử gán giá trị 0, 1, 2 cho cạnh thứ idx
            edge = self.edges[idx]
            u, v = edge["u"], edge["v"]
            
            # Heuristic ordering: Thử giá trị nào trước?
            # Với A*, thứ tự push vào heap không quá quan trọng vì nó tự sort theo f,
            # nhưng ta vẫn loop 0,1,2
            for val in [0, 1, 2]:
                # 1. Pruning cơ bản: Quá tải
                new_deg_u = degs[u] + val
                new_deg_v = degs[v] + val
                if new_deg_u > self.islands[u]["val"] or new_deg_v > self.islands[v]["val"]:
                    continue
                
                # 2. Pruning Crossing
                if val > 0 and self._check_crossing(idx, val, assigns):
                    continue

                # Tạo trạng thái mới
                new_degs_list = list(degs)
                new_degs_list[u] = new_deg_u
                new_degs_list[v] = new_deg_v
                new_degs = tuple(new_degs_list)
                
                # Tính Heuristic cho bước TIẾP THEO (idx + 1)
                new_h = self.heuristic(idx + 1, new_degs)
                
                if new_h >= 999999: continue # Cắt nhánh sớm

                new_g = idx + 1
                new_f = new_g + new_h
                
                new_assigns = list(assigns)
                new_assigns[idx] = val
                
                heapq.heappush(pq, (new_f, new_h, idx + 1, tuple(new_assigns), new_degs))
                
        return None

    def _check_crossing(self, curr_idx, val, assigns):
        for (i, j) in self.crossing_pairs:
             other = -1
             if i == curr_idx: other = j
             elif j == curr_idx: other = i
             
             if other != -1 and other < curr_idx:
                 if assigns[other] > 0:
                     return True
        return False

    def _format_model(self, assignments):
        # Vì ta đã sort self.edges, cần map lại đúng biến CNF gốc
        model = []
        for idx, val in enumerate(assignments):
            edge = self.edges[idx]
            # Tìm index gốc của edge trong meta
            orig_idx = self.meta["edges"].index(edge)
            
            v1, v2 = self.var_map[orig_idx]
            if val == 0: model.extend([-v1, -v2])
            elif val == 1: model.extend([v1, -v2])
            elif val == 2: model.extend([v1, v2])
        return model