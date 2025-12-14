# Source/solver_backtracking.py
import sys

class BacktrackingSAT:
    def __init__(self, cnf, meta, timeout=None):
        self.meta = meta
        self.islands = meta["islands"]
        
        # --- [TỐI ƯU] Sắp xếp thứ tự duyệt cạnh ---
        # Chiến thuật: Ưu tiên duyệt các cạnh nối với đảo nhỏ trước (Most Constrained)
        # Vì đảo số 1, 2 rất dễ bị vi phạm -> giúp thuật toán phát hiện sai và quay lui sớm.
        self.edges = sorted(
            meta["edges"], 
            key=lambda e: self.islands[e["u"]]["val"] + self.islands[e["v"]]["val"]
        )
        
        self.n_edges = len(self.edges)
        self.var_map = meta["var_map"]
        
        # Pre-compute neighbors và Crossing pairs (giữ nguyên)
        self.crossing_pairs = self._find_crossing_pairs()

    def _find_crossing_pairs(self):
        # Tìm các cặp cạnh cắt nhau dựa trên danh sách edges ĐÃ SẮP XẾP
        pairs = []
        for i in range(self.n_edges):
            for j in range(i + 1, self.n_edges):
                e1, e2 = self.edges[i], self.edges[j]
                if e1["type"] != e2["type"]: # 1 H, 1 V
                    h, v = (e1, e2) if e1["type"]=="H" else (e2, e1)
                    if v["r1"] < h["r"] < v["r2"] and h["c1"] < v["c"] < h["c2"]:
                        pairs.append((i, j))
        return pairs

    def solve(self):
        assignments = [0] * self.n_edges
        current_degrees = [0] * len(self.islands)
        return self._backtrack(0, assignments, current_degrees)

    def _backtrack(self, edge_idx, assignments, current_degrees):
        # Base case: Đã duyệt hết cạnh
        if edge_idx == self.n_edges:
            # Check lần cuối: Mọi đảo phải ĐỦ (=) cầu
            for i, isl in enumerate(self.islands):
                if current_degrees[i] != isl["val"]:
                    return None
            return self._format_model(assignments)

        edge = self.edges[edge_idx]
        u, v = edge["u"], edge["v"]
        
        # Lấy giới hạn
        limit_u = self.islands[u]["val"]
        limit_v = self.islands[v]["val"]
        
        # [HEURISTIC] Thử giá trị theo thứ tự nào? 
        # Thử 0 trước giúp tìm nghiệm thưa nhanh hơn, 
        # nhưng thử max trước (2) giúp lấp đầy đảo nhanh hơn.
        # Ở đây ta giữ [0, 1, 2]
        for val in [0, 1, 2]:
            # 1. Pruning Capacity: Không được vượt quá giới hạn đảo
            if current_degrees[u] + val > limit_u: continue
            if current_degrees[v] + val > limit_v: continue
            
            # 2. Pruning Crossing: Không được cắt cạnh đã gán > 0
            if val > 0 and self._check_crossing(edge_idx, assignments):
                continue
            
            # Gán thử
            assignments[edge_idx] = val
            current_degrees[u] += val
            current_degrees[v] += val
            
            # Đệ quy
            res = self._backtrack(edge_idx + 1, assignments, current_degrees)
            if res: return res
            
            # Quay lui (Backtrack)
            current_degrees[u] -= val
            current_degrees[v] -= val
            assignments[edge_idx] = 0
            
        return None

    def _check_crossing(self, curr_idx, assignments):
        for (i, j) in self.crossing_pairs:
            # Tìm cạnh kia trong cặp cắt nhau
            other = -1
            if i == curr_idx: other = j
            elif j == curr_idx: other = i
            
            # Chỉ kiểm tra nếu cạnh kia nằm trước (index nhỏ hơn) -> đã được gán giá trị
            if other != -1 and other < curr_idx:
                if assignments[other] > 0:
                    return True
        return False

    def _format_model(self, assignments):
        model = []
        # Vì ta đã sort self.edges, nên khi trả về model ta phải map đúng lại ID gốc
        # Tuy nhiên, hàm vẽ (helper_02) vẽ dựa trên list edges. 
        # Để đơn giản, ta chỉ cần trả về list biến SAT tương ứng với edges đang giữ.
        # Lưu ý: Điều này đòi hỏi hàm gọi bên ngoài (helper_02) phải biết thứ tự edges đã đổi.
        # NHƯNG: Để an toàn nhất mà không sửa helper_02, ta dùng var_map gốc.
        
        for idx, val in enumerate(assignments):
            # Cần lấy đúng ID biến từ meta['var_map'] tương ứng với cạnh gốc
            # Nhưng self.edges đã bị sort, làm sao biết cạnh này ứng với index nào trong meta gốc?
            # -> Cách đơn giản nhất:
            # Ta KHÔNG thay đổi cấu trúc dữ liệu trả về, mà chỉ cần map đúng biến.
            # Trong code này, meta["edges"] và meta["var_map"] khớp index 1-1.
            # Do đó ta cần tìm lại index gốc của cạnh edge.
            
            # FIX: Để tránh phức tạp, ta dùng "var_map" gắn liền với edge object
            # (Bạn không cần sửa code này, logic format model đơn giản chỉ cần trả về đúng logic SAT)
            
            # Cách fix nhanh: Lấy trực tiếp từ var_map theo index của cạnh trong danh sách ĐÃ SORT?
            # KHÔNG ĐƯỢC. Var_map được đánh index theo danh sách GỐC.
            pass

        # === FIX LẠI LOGIC FORMAT MODEL CHO BACKTRACKING ===
        # Để tránh lỗi hiển thị khi sort, ta sẽ không sort trực tiếp self.edges mà dùng index mảng để tham chiếu.
        return self._format_model_safe(assignments)

    def _format_model_safe(self, assignments):
        # assignments đang theo thứ tự của self.edges (đã sort)
        # Ta cần map lại về var_map gốc.
        # Nhưng var_map gốc dùng index 0,1,2... theo thứ tự input.
        # -> Giải pháp: Trong __init__, ta lưu thêm `original_index` cho mỗi edge.
        model = []
        for idx, val in enumerate(assignments):
            edge = self.edges[idx]
            # Ta cần tìm index gốc của edge này trong meta['edges']
            # Cách này hơi chậm ($O(N^2)$) nhưng an toàn và chỉ chạy 1 lần cuối cùng.
            orig_idx = self.meta["edges"].index(edge) 
            
            v1, v2 = self.var_map[orig_idx]
            if val == 0: model.extend([-v1, -v2])
            elif val == 1: model.extend([v1, -v2])
            elif val == 2: model.extend([v1, v2])
        return model