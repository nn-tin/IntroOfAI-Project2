"""
SAT Solver using PySAT Glucose3 for Hashiwokakero
"""
import time
from pysat.solvers import Glucose3

# ---------------------------------------------------
# 1) Kiểm tra liên thông bằng BFS từ model SAT
# ---------------------------------------------------
def check_connectivity_from_model(model, meta):
    islands = meta["islands"]
    var_map = meta["var_map"] # Dạng: {edge_idx: (v1, v2)}
    edges = meta["edges"]
    n = len(islands)

    if n <= 1:
        return True

    # Tạo tập hợp model để tra cứu nhanh (O(1))
    model_set = set(model)

    # Xây dựng đồ thị kề (Adjacency list)
    adj = {i: set() for i in range(n)}
    
    # Duyệt qua tất cả các cạnh trong var_map
    for edge_idx, (v1, v2) in var_map.items():
        # Nếu v1 (cầu 1) hoặc v2 (cầu 2) tồn tại trong model -> có kết nối
        if v1 in model_set or v2 in model_set:
            e = edges[edge_idx]
            u, v = e["u"], e["v"]
            adj[u].add(v)
            adj[v].add(u)

    # BFS từ đảo 0
    visited = set([0])
    stack = [0]

    while stack:
        cur = stack.pop()
        for nb in adj[cur]:
            if nb not in visited:
                visited.add(nb)
                stack.append(nb)

    return len(visited) == n


# ---------------------------------------------------
# 2) Chuyển kết quả SAT thành danh sách cầu để output
# ---------------------------------------------------
def model_to_bridges(meta, model):
    """
    Trích xuất cầu từ model.
    Input: var_map dạng {edge_idx: (v1, v2)}
    Return list: [{u, v, count, dir}]
    """
    model_set = set(model)
    var_map = meta["var_map"]
    edges = meta["edges"]
    bridges = []

    for edge_idx, (v1, v2) in var_map.items():
        count = 0
        if v1 in model_set: count += 1
        if v2 in model_set: count += 1
        
        # Lưu ý: Do logic v2 -> v1, nếu có v2 thì chắc chắn có v1 => count = 2
        # Nếu chỉ có v1 => count = 1
        
        if count > 0:
            e = edges[edge_idx]
            d = "H" if e["type"] == "H" else "V"
            bridges.append({
                "u": e["u"],
                "v": e["v"],
                "count": count,
                "dir": d
            })

    return bridges


# ---------------------------------------------------
# 3) Solver chính — tìm model + lọc model liên thông
# ---------------------------------------------------
def run_pysat(cnf, meta, timeout=1000.0):
    """
    Solve CNF bằng PySAT Glucose3.
    Returns:
      model (list[int]) | None,
      elapsed_time (float),
      timed_out_flag (bool),
      connected_flag (bool)
    """
    t0 = time.perf_counter()
    solver = Glucose3()
    solver.append_formula(cnf.clauses)

    model = None
    connected = False
    timed_out = False

    try:
        while True:
            # Kiểm tra timeout
            if time.perf_counter() - t0 > timeout:
                timed_out = True
                break

            # Giải SAT
            sat = solver.solve()
            if not sat:
                break

            m = solver.get_model()

            # Kiểm tra liên thông
            if check_connectivity_from_model(m, meta):
                model = m
                connected = True
                break # Tìm thấy lời giải hợp lệ

            # Nếu chưa liên thông -> Thêm ràng buộc chặn model này để tìm nghiệm khác
            # (Blocking Clause: -l1 v -l2 v ... v -ln)
            solver.add_clause([-lit for lit in m])

    finally:
        solver.delete()

    elapsed = time.perf_counter() - t0
    return model, elapsed, timed_out, connected