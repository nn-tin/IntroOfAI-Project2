# ====================== helper_02.py ==========================
# Xử lý CNF, decode output SAT, dựng lưới output + export kết quả
from pysat.formula import CNF
from pysat.card import CardEnc
from helper_01 import read_input
import os

def generate_cnf(board):
    cnf = CNF()
    R, C = len(board), len(board[0])

    # 1) Xác định đảo (islands)
    islands = []
    for r in range(R):
        for c in range(C):
            if board[r][c] > 0:
                islands.append({"r": r, "c": c, "val": board[r][c], "id": len(islands)})

    # 2) Tìm tất cả các cầu có thể nối (edges)
    edges = []
    n_islands = len(islands)
    for i in range(n_islands):
        a = islands[i]
        for j in range(i + 1, n_islands):
            b = islands[j]

            # Kiểm tra cầu ngang
            if a["r"] == b["r"]:
                r = a["r"]
                c1, c2 = sorted([a["c"], b["c"]])
                # Đảm bảo không có đảo hoặc chướng ngại vật ở giữa
                if all(board[r][k] == 0 for k in range(c1 + 1, c2)):
                    edges.append({"u": i, "v": j, "type": "H", "r": r, "c1": c1, "c2": c2})

            # Kiểm tra cầu dọc
            if a["c"] == b["c"]:
                c = a["c"]
                r1, r2 = sorted([a["r"], b["r"]])
                if all(board[k][c] == 0 for k in range(r1 + 1, r2)):
                    edges.append({"u": i, "v": j, "type": "V", "c": c, "r1": r1, "r2": r2})

    # 3) Khai báo biến SAT
    # var_map lưu cặp biến [v1, v2] cho mỗi cạnh (index trong edges)
    # v1: Có ít nhất 1 cầu
    # v2: Có 2 cầu
    var_map = {}
    var_count = 1
    
    for idx, e in enumerate(edges):
        v1 = var_count
        v2 = var_count + 1
        var_count += 2
        var_map[idx] = (v1, v2)
        
        # Ràng buộc logic: Nếu có cầu 2 thì bắt buộc phải có cầu 1 (v2 -> v1)
        # Tương đương: -v2 OR v1
        cnf.append([-v2, v1])

    # 4) Ràng buộc tổng số cầu nối mỗi đảo
    for i, island in enumerate(islands):
        deg = island["val"]
        lits = []
        
        # Tìm tất cả cạnh nối với đảo i
        for idx, e in enumerate(edges):
            if e["u"] == i or e["v"] == i:
                # Thêm cả biến v1 và v2 vào danh sách đếm
                # CardEnc sẽ đếm số lượng biến True. Nếu v1=True, v2=True => cộng 2
                lits.append(var_map[idx][0]) 
                lits.append(var_map[idx][1])

        # Nếu tổng số cầu khả thi < giá trị đảo => Vô nghiệm ngay lập tức (tránh lỗi CardEnc)
        if len(lits) < deg:
            print(f"Lỗi: Đảo tại ({island['r']},{island['c']}) cần {deg} cầu nhưng chỉ có thể nối tối đa {len(lits)}.")
            # Thêm clause rỗng để báo UNSAT ngay
            cnf.append([]) 
            continue

        # Ràng buộc: Tổng số biến active phải bằng đúng giá trị đảo
        enc = CardEnc.equals(lits=lits, bound=deg, encoding=1, top_id=var_count)
        var_count = max(var_count, enc.nv)
        cnf.extend(enc.clauses)

    # 5) Ràng buộc không cho cầu cắt nhau (Crossing Logic - ĐÃ SỬA)
    for i, e1 in enumerate(edges):
        for j in range(i + 1, len(edges)):
            e2 = edges[j]
            
            cross = False
            # Chỉ xét trường hợp 1 ngang (H) cắt 1 dọc (V)
            if e1["type"] == "H" and e2["type"] == "V":
                if e2["r1"] < e1["r"] < e2["r2"] and e1["c1"] < e2["c"] < e1["c2"]:
                    cross = True
            elif e1["type"] == "V" and e2["type"] == "H":
                if e1["r1"] < e2["r"] < e1["r2"] and e2["c1"] < e1["c"] < e2["c2"]:
                    cross = True
            
            if cross:
                # Logic đúng: Không thể đồng thời tồn tại cầu ở cạnh i VÀ cạnh j
                # Chỉ cần cấm biến v1 (cầu thứ nhất) là đủ.
                u1 = var_map[i][0]
                v1 = var_map[j][0]
                cnf.append([-u1, -v1])
                
    return cnf, {"islands": islands, "edges": edges, "var_map": var_map}



# =====================================================================
# 2) Decode SAT → list (u,v,count,type)
# =====================================================================
def decode_output(model, meta):
    bridges=[]
    for idx,e in enumerate(meta["edges"]):
        cnt=0
        if meta["var_map"][(idx,1)] in model: cnt=1
        if meta["var_map"][(idx,2)] in model: cnt=2
        if cnt>0:
            bridges.append({
                "u":e["u"],"v":e["v"],"count":cnt,"dir":e["type"]
            })
    return bridges


# =====================================================================
# 3) Build output grid (final)
# =====================================================================
def build_output_grid(board, meta, bridges):
    R,C = len(board),len(board[0])
    out=[["0" for _ in range(C)] for _ in range(R)]

    # Gán đảo
    for isl in meta["islands"]:
        out[isl["r"]][isl["c"]] = str(isl["val"])

    # Gán cầu
    for b in bridges:
        a = meta["islands"][b["u"]]
        c = meta["islands"][b["v"]]

        if b["dir"]=="H":
            row=a["r"]
            x1,x2 = sorted([a["c"],c["c"]])
            sym = "-" if b["count"]==1 else "="
            for col in range(x1+1,x2):
                out[row][col]=sym

        if b["dir"]=="V":
            col=a["c"]
            y1,y2 = sorted([a["r"],c["r"]])
            sym = "|" if b["count"]==1 else "║"  # Dùng ký tự dễ nhìn hơn thay vì $
            for row in range(y1+1,y2):
                out[row][col]=sym

    return out


# =====================================================================
# 4) Export output to txt
# =====================================================================
def export_output_grid(grid, filename="output.txt"):
    os.makedirs("Outputs",exist_ok=True)
    path=f"Outputs/{filename}"

    with open(path,"w",encoding="utf-8") as f:
        for row in grid:
            f.write("[ " + " , ".join(f'"{x}"' for x in row) + " ]\n")

    print(f"✔ Output saved → {path}")
    return path


# =====================================================================
# 5) Hàm main test (bạn cần thay dòng tạo model bằng gọi solver thật)
# =====================================================================
def main():
    input_path = "Inputs/input-01.txt"  # Thay đường dẫn nếu cần

    board = read_input(input_path)

    print("Board đầu vào:")
    for row in board:
        print(row)

    cnf, meta = generate_cnf(board)
    print(f"Toàn bộ mệnh đề CNF ({len(cnf.clauses)} mệnh đề):")
    for clause in cnf.clauses:
        print(clause)

if __name__ == "__main__":
    main()
