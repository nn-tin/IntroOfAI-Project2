# Source/solver_astar.py
import heapq
import sys
import os

class AStarSAT:
    def __init__(self, cnf):
        # Convert clauses sang list để dễ xử lý
        self.clauses = [list(c) for c in cnf.clauses] 
        self.num_vars = cnf.nv
        
    def heuristic(self, assignment):
        # Heuristic: Số lượng mệnh đề CHƯA được thỏa mãn (Unsatisfied Clauses)
        unsat_count = 0
        for clause in self.clauses:
            is_satisfied = False
            for lit in clause:
                # lit là số dương (biến) hoặc âm (NOT biến)
                var = abs(lit)
                val = assignment.get(var)
                
                if val is None: 
                    continue # Biến chưa gán -> coi như chưa thỏa mãn mệnh đề này
                
                # Nếu lit > 0 và val = True -> True
                # Nếu lit < 0 và val = False -> True
                if (lit > 0 and val) or (lit < 0 and not val):
                    is_satisfied = True
                    break
            
            if not is_satisfied:
                unsat_count += 1
        return unsat_count

    def solve(self):
        # Priority Queue lưu tuple: (f_score, h_score, id_assign, assignment_dict)
        # f = g + h. 
        # g = số biến đã gán (chi phí đường đi)
        # h = số mệnh đề chưa thỏa mãn (ước lượng còn lại)
        
        start_assignment = {}
        start_h = self.heuristic(start_assignment)
        
        # Open set
        open_set = []
        # id(assignment) để đảm bảo tính unique khi push vào heap
        heapq.heappush(open_set, (start_h, start_h, id(start_assignment), start_assignment))
        
        visited_states = set() # Tránh lặp lại trạng thái (tập hợp các biến đã gán)

        while open_set:
            f, h, _, current_assign = heapq.heappop(open_set)
            
            # Key để lưu vết visited (tuple sorted của các biến đã gán)
            state_key = tuple(sorted(current_assign.items()))
            if state_key in visited_states:
                continue
            visited_states.add(state_key)

            # Nếu h = 0: Tất cả mệnh đề đã được thỏa mãn?
            # Cẩn thận: h=0 có thể do chưa gán biến nào thuộc mệnh đề đó (nếu logic heuristic lỏng)
            # Nhưng với logic trên: val is None -> continue -> is_satisfied = False -> unsat += 1
            # Nên nếu h=0 tức là TẤT CẢ mệnh đề đều đã có ít nhất 1 literal True.
            if h == 0:
                return self.format_model(current_assign)
            
            # Chọn biến tiếp theo để gán
            # Chiến thuật: Chọn biến xuất hiện trong các mệnh đề chưa thỏa mãn đầu tiên
            next_var = -1
            # Cách đơn giản: Chọn biến có index nhỏ nhất chưa được gán
            for v in range(1, self.num_vars + 1):
                if v not in current_assign:
                    next_var = v
                    break
            
            if next_var == -1: 
                continue 
                
            # Tạo 2 nhánh con: Gán True và Gán False
            for val in [True, False]:
                new_assign = current_assign.copy()
                new_assign[next_var] = val
                
                # Tính heuristic mới
                new_h = self.heuristic(new_assign)
                
                # Kiểm tra Conflict: Nếu có mệnh đề nào SAI HOÀN TOÀN (tất cả literal đều False) -> Cắt tỉa nhánh này
                if not self.has_conflict(new_assign):
                    g = len(new_assign)
                    f = g + new_h 
                    heapq.heappush(open_set, (f, new_h, id(new_assign), new_assign))
                    
        return None # Không tìm thấy

    def has_conflict(self, assignment):
        # Kiểm tra nhanh: Có clause nào mà tất cả literal đều đã được gán giá trị và đều False không?
        for clause in self.clauses:
            clause_false = True # Giả sử clause này sai
            is_fully_assigned = True
            
            for lit in clause:
                var = abs(lit)
                if var not in assignment:
                    is_fully_assigned = False
                    clause_false = False # Còn biến chưa gán -> Chưa chắc sai -> Vẫn còn hy vọng
                    break
                
                val = assignment[var]
                if (lit > 0 and val) or (lit < 0 and not val):
                    clause_false = False # Có 1 cái True -> Clause này đúng
                    break
            
            if clause_false: # Tất cả literal trong clause đều False
                return True
        return False

    def format_model(self, assignment):
        # Chuyển đổi format về giống PySAT (list các số nguyên có dấu)
        model = []
        for v in range(1, self.num_vars + 1):
            if assignment.get(v, False):
                model.append(v)
            else:
                model.append(-v)
        return model

# --- PHẦN KIỂM THỬ (UNIT TEST) ---
if __name__ == "__main__":
    print("\n=== TEST 1: Chạy thử với input-01.txt ===")
    import helper_01
    import helper_02
    
    # Đường dẫn file input
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(current_dir, 'Inputs', 'input-01.txt')
    
    if os.path.exists(input_path):
        board = helper_01.read_input(input_path)
        print("Đã đọc board từ input-01.txt")
        cnf, data = helper_02.generate_cnf(board)
        print(f"Sinh CNF: {cnf.nv} biến, {len(cnf.clauses)} mệnh đề.")
        
        print("Đang chạy A* solver (có thể mất vài giây)...")
        astar = AStarSAT(cnf)
        model = astar.solve()
        
        if model:
            print("-> TÌM THẤY LỜI GIẢI!")
            print("Model mẫu (10 biến đầu):", model[:10])
        else:
            print("-> KHÔNG TÌM THẤY LỜI GIẢI (UNSAT)")
    else:
        print("Không tìm thấy file input-01.txt để test.")