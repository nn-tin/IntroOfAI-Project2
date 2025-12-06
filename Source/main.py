# Source/main.py
import sys
import os
import time # Import để đo thời gian chạy
from pysat.solvers import Glucose3
import helper_01
import helper_02
from solver_astar import AStarSAT # Import thuật toán A* của bạn

# --- CÁC HÀM HỖ TRỢ ---
def check_connectivity(model, data):
    """Kiểm tra tính liên thông của đồ thị cầu nối"""
    var_map = data['var_map']
    islands = data['islands']
    num_islands = len(islands)
    if num_islands <= 1: return True

    adj = {i: [] for i in range(num_islands)}
    id_to_info = {v: k for k, v in var_map.items()}
    active_vars = set(model)
    
    for (u, v, k), var_id in var_map.items():
        if var_id in active_vars and var_id > 0:
            if v not in adj[u]: adj[u].append(v)
            if u not in adj[v]: adj[v].append(u)

    start_node = 0
    queue = [start_node]
    visited = {start_node}
    while queue:
        curr = queue.pop(0)
        for neighbor in adj[curr]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    
    return len(visited) == num_islands

def print_solution(model, data):
    print("\n--- CHI TIẾT CẦU NỐI ---")
    var_map = data['var_map']
    islands = data['islands']
    id_to_info = {v: k for k, v in var_map.items()}
    
    count = 0
    for var_id in model:
        if var_id > 0 and var_id in id_to_info:
            u_idx, v_idx, k = id_to_info[var_id]
            is_max = True
            if k == 1:
                next_var = var_map.get((u_idx, v_idx, 2))
                if next_var and next_var in model: is_max = False
            
            if is_max:
                u, v = islands[u_idx], islands[v_idx]
                print(f"Đảo ({u['r']},{u['c']}) --({k} cầu)-- Đảo ({v['r']},{v['c']})")
                count += 1
    if count == 0: print("(Không có cầu nào)")

# --- HÀM GIẢI BẰNG PYSAT ---
def solve_with_pysat(board):
    print("\n>>> [PYSAT] 1. Sinh CNF...")
    cnf, data = helper_02.generate_cnf(board)
    print(f"    - Số biến: {cnf.nv}, Số mệnh đề: {len(cnf.clauses)}")
    
    print(">>> [PYSAT] 2. Đang giải...")
    start_time = time.time()
    
    solver = Glucose3()
    solver.append_formula(cnf.clauses)
    
    attempt = 0
    while solver.solve():
        attempt += 1
        model = solver.get_model()
        if check_connectivity(model, data):
            end_time = time.time()
            print(f"    -> TÌM THẤY SAU {end_time - start_time:.4f}s ({attempt} lần thử)")
            print_solution(model, data)
            return
        else:
            current_bridges = [l for l in model if l > 0]
            solver.add_clause([-l for l in current_bridges])
            
    print(">>> [PYSAT] UNSAT (Không tìm thấy lời giải liên thông)")

# --- HÀM GIẢI BẰNG A* (Của bạn) ---
def solve_with_astar(board):
    print("\n>>> [A*] 1. Sinh CNF...")
    cnf, data = helper_02.generate_cnf(board)
    print(f"    - Số biến: {cnf.nv}, Số mệnh đề: {len(cnf.clauses)}")
    
    print(">>> [A*] 2. Đang giải (Logic thuần túy)...")
    start_time = time.time()
    
    # Khởi tạo A* Solver
    solver = AStarSAT(cnf)
    model = solver.solve()
    
    end_time = time.time()
    
    if model:
        print(f"    -> TÌM THẤY LỜI GIẢI SAU {end_time - start_time:.4f}s")
        # Lưu ý: A* ở đây chỉ giải CNF tĩnh, chưa bao gồm vòng lặp check liên thông
        # (Vì A* chạy lặp sẽ rất chậm, mục tiêu chính là demo thuật toán giải CNF)
        print_solution(model, data)
        
        # Check thử xem có liên thông không (để báo cáo)
        if check_connectivity(model, data):
            print("    (Kết quả này đảm bảo tính liên thông ✅)")
        else:
            print("    (Kết quả này thỏa mãn số lượng cầu, nhưng chưa liên thông toàn bộ ⚠️)")
    else:
        print(">>> [A*] UNSAT")

# --- MAIN ---
def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    inputs_dir = os.path.join(current_dir, 'Inputs')
    if not os.path.exists(inputs_dir): os.makedirs(inputs_dir)

    # Xử lý tham số dòng lệnh
    # python main.py <file_input> <method>
    filename = 'input-01.txt'
    method = 'pysat' # mặc định

    if len(sys.argv) > 1: filename = sys.argv[1]
    if len(sys.argv) > 2: method = sys.argv[2].lower()

    input_path = os.path.join(inputs_dir, filename)
    if not os.path.exists(input_path):
        print(f"Lỗi: Không tìm thấy file {input_path}")
        return

    print(f"=== ĐANG CHẠY FILE: {filename} | METHOD: {method.upper()} ===")
    board = helper_01.read_input(input_path)
    
    if method == 'astar':
        solve_with_astar(board)
    else:
        solve_with_pysat(board)

if __name__ == "__main__":
    main()