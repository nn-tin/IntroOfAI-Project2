from pysat.formula import CNF
from pysat.solvers import Glucose3
from pysat.card import CardEnc

def generate_cnf(board):
    cnf = CNF()
    R, C = len(board), len(board[0])

    # 1) Xác định các đảo (islands)
    islands = []
    for r in range(R):
        for c in range(C):
            if board[r][c] > 0:
                idx = len(islands)
                islands.append({"r": r, "c": c, "val": board[r][c], "id": idx})

    n = len(islands)

    # 2) Tìm tất cả các cầu có thể nối (edges)
    edges = []
    for i in range(n):
        a = islands[i]
        for j in range(i + 1, n):
            b = islands[j]
            
            # Cầu ngang
            if a["r"] == b["r"]:
                r = a["r"]
                c1, c2 = sorted([a["c"], b["c"]])
                if all(board[r][k] == 0 for k in range(c1 + 1, c2)):
                    edges.append({"u": i, "v": j, "type": "H", "r": r, "c1": c1, "c2": c2})

            # Cầu dọc
            if a["c"] == b["c"]:
                c = a["c"]
                r1, r2 = sorted([a["r"], b["r"]])
                if all(board[k][c] == 0 for k in range(r1 + 1, r2)):
                    edges.append({"u": i, "v": j, "type": "V", "c": c, "r1": r1, "r2": r2})

    # 3) Khai báo biến SAT: MỖI CẠNH CẦN 2 BIẾN (cầu 1 và cầu 2)
    var_count = 1
    edge_vars = {} 
    
    for idx, e in enumerate(edges):
        v1 = var_count      # Biến: có cầu thứ nhất
        v2 = var_count + 1  # Biến: có cầu thứ hai
        var_count += 2
        
        edge_vars[idx] = [v1, v2]

        # Ràng buộc: Có cầu 2 thì bắt buộc phải có cầu 1 (v2 => v1 hay -v2 v v1)
        cnf.append([-v2, v1])

    # 4) Ràng buộc số cầu đúng deg(i) mỗi đảo
    for i in range(n):
        deg_i = islands[i]["val"]
        lits = []
        for idx, e in enumerate(edges):
            if e["u"] == i or e["v"] == i:
                # Thêm cả biến cầu 1 và cầu 2 vào danh sách đếm
                lits.append(edge_vars[idx][0])
                lits.append(edge_vars[idx][1])

        # Kiểm tra nhanh: Nếu tổng số cầu tối đa (số cạnh * 2) nhỏ hơn yêu cầu -> Lỗi input
        if len(lits) < deg_i:
             # Lưu ý: Đây là check sơ bộ, thực tế SAT sẽ lo việc này
             pass

        # Ràng buộc: Tổng số biến active phải bằng deg_i
        enc = CardEnc.equals(lits=lits, bound=deg_i, encoding=1, top_id=var_count)
        var_count = max(var_count, enc.nv)
        cnf.extend(enc.clauses)

    # 5) Ràng buộc cầu không được cắt nhau
    for i, e1 in enumerate(edges):
        for j in range(i + 1, len(edges)):
            e2 = edges[j]
            
            cross = False
            # Kiểm tra cắt nhau giữa Ngang và Dọc
            if e1["type"] == "H" and e2["type"] == "V":
                if e2["r1"] < e1["r"] < e2["r2"] and e1["c1"] < e2["c"] < e1["c2"]:
                    cross = True
            elif e1["type"] == "V" and e2["type"] == "H":
                if e1["r1"] < e2["r"] < e1["r2"] and e2["c1"] < e1["c"] < e2["c2"]:
                    cross = True
            
            if cross:
                # Nếu cắt nhau: Không thể tồn tại cầu ở e1 VÀ cầu ở e2.
                # Chỉ cần cấm cầu đầu tiên của 2 cạnh là đủ (vì v2 => v1).
                # Nếu v1 của e1 active thì v1 của e2 phải inactive và ngược lại.
                u1 = edge_vars[i][0]
                v1 = edge_vars[j][0]
                cnf.append([-u1, -v1])

    return cnf, islands, edges, edge_vars

def solve_hashiwokakero():
    # Input board
    board = [
        [0, 2, 0, 5, 0, 0, 2],
        [0, 0, 0, 0, 0, 0, 0],
        [4, 0, 2, 0, 2, 0, 4],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 5, 0, 2, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [4, 0, 0, 0, 0, 0, 3],
    ]

    cnf, islands, edges, edge_vars = generate_cnf(board)

    solver = Glucose3()
    solver.append_formula(cnf.clauses)

    print("Đang giải...")
    sat = solver.solve()
    
    if not sat:
        print("Không có nghiệm!")
        return

    model = solver.get_model()
    model_set = set(v for v in model if v > 0)

    # Hiển thị kết quả
    R, C = len(board), len(board[0])
    # Tạo bảng hiển thị to hơn để dễ nhìn (hoặc giữ nguyên logic cũ nhưng đổi ký tự)
    output = [[" "]*C for _ in range(R)]
    
    for isl in islands:
        output[isl["r"]][isl["c"]] = str(isl["val"])

    for idx, e in enumerate(edges):
        v1, v2 = edge_vars[idx]
        count = 0
        if v1 in model_set: count += 1
        if v2 in model_set: count += 1
        
        if count > 0:
            if e["type"] == "H":
                char = "-" if count == 1 else "="
                row = e["r"]
                for cc in range(e["c1"] + 1, e["c2"]):
                    output[row][cc] = char
            else: # Vertical
                char = "|" if count == 1 else "║" # Dùng ký tự ASCII đôi hoặc "||"
                col = e["c"]
                for rr in range(e["r1"] + 1, e["r2"]):
                    output[rr][col] = char

    print("\nKẾT QUẢ:")
    for row in output:
        # Format đẹp hơn chút
        line = " ".join(f"{x:^3}" for x in row)
        print(line)

if __name__ == "__main__":
    solve_hashiwokakero()