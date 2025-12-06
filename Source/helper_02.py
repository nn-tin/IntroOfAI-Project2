# Source/helper_02.py
from pysat.formula import CNF
from pysat.card import CardEnc

def generate_cnf(board):
    cnf = CNF()
    n_rows = len(board)
    n_cols = len(board[0])
    
    islands = []
    # Tìm các đảo và lưu thông tin
    for r in range(n_rows):
        for c in range(n_cols):
            if board[r][c] > 0:
                islands.append({'r': r, 'c': c, 'val': board[r][c], 'id': len(islands)})

    # 1. Xác định các cạnh khả thi (neighbors)
    # Luật: Cầu đi thẳng, không xuyên qua đảo khác [cite: 56, 63]
    possible_edges = []
    for i in range(len(islands)):
        u = islands[i]
        for j in range(i + 1, len(islands)):
            v = islands[j]
            
            # Kiểm tra cùng hàng (row)
            if u['r'] == v['r']:
                blocked = False
                c_min, c_max = min(u['c'], v['c']), max(u['c'], v['c'])
                # Check các ô ở giữa xem có bị chặn không
                for k in range(c_min + 1, c_max):
                    if board[u['r']][k] > 0: blocked = True; break
                if not blocked:
                    possible_edges.append({'u': i, 'v': j, 'type': 'row', 'r': u['r'], 'c_min': c_min, 'c_max': c_max})
            
            # Kiểm tra cùng cột (col)
            elif u['c'] == v['c']:
                blocked = False
                r_min, r_max = min(u['r'], v['r']), max(u['r'], v['r'])
                for k in range(r_min + 1, r_max):
                    if board[k][u['c']] > 0: blocked = True; break
                if not blocked:
                    possible_edges.append({'u': i, 'v': j, 'type': 'col', 'c': u['c'], 'r_min': r_min, 'r_max': r_max})

    # 2. Tạo biến logic [cite: 84, 251]
    # Mỗi cạnh có 2 biến: v1 (có ít nhất 1 cầu), v2 (có 2 cầu)
    var_map = {} 
    counter = 1
    edge_vars = [] 

    for idx, edge in enumerate(possible_edges):
        v1 = counter; counter += 1
        v2 = counter; counter += 1
        
        var_map[(idx, 1)] = v1
        var_map[(idx, 2)] = v2
        edge_vars.append({'v1': v1, 'v2': v2})

        # Ràng buộc cơ bản: Nếu có cầu 2 thì phải có cầu 1 (Logic: v2 -> v1 <=> -v2 OR v1)
        # [cite: 254] (Luật tối đa 2 cầu)
        cnf.append([-v2, v1])

    # 3. LUẬT SỐ HỌC: Tổng cầu nối vào đảo = Giá trị đảo [cite: 66, 258-260]
    for island_idx, island in enumerate(islands):
        literals = []
        # Gom tất cả các biến cầu nối vào đảo này
        for edge_idx, edge in enumerate(possible_edges):
            if edge['u'] == island_idx or edge['v'] == island_idx:
                v1 = edge_vars[edge_idx]['v1']
                v2 = edge_vars[edge_idx]['v2']
                literals.append(v1)
                literals.append(v2)
        
        # --- FIX LỖI CRASH (QUAN TRỌNG) ---
        # Nếu tổng số dây khả thi < số yêu cầu của đảo => Vô nghiệm (UNSAT)
        # Ví dụ: Đảo số 4 mà chỉ có 1 hàng xóm (max 2 dây) -> Không thể giải.
        if len(literals) < island['val']:
            print(f"DEBUG: Đảo tại ({island['r']},{island['c']}) val={island['val']} không đủ hàng xóm nối!")
            cnf.append([]) # Thêm mệnh đề rỗng để ép UNSAT ngay lập tức
            continue 
        # ----------------------------------

        # Dùng CardEnc để sinh ràng buộc: sum(literals) == island['val']
        cnf_sum = CardEnc.equals(lits=literals, bound=island['val'], encoding=1, top_id=counter)
        
        # Cập nhật counter biến
        if cnf_sum.nv > counter:
            counter = cnf_sum.nv
        cnf.extend(cnf_sum.clauses)

    # 4. LUẬT KHÔNG CẮT NHAU [cite: 63, 257]
    # Cầu ngang và cầu dọc giao nhau không được cùng tồn tại
    for i in range(len(possible_edges)):
        for j in range(i + 1, len(possible_edges)):
            e1 = possible_edges[i]
            e2 = possible_edges[j]
            
            # Chỉ xét 1 ngang - 1 dọc
            if e1['type'] == e2['type']: continue
            
            row_edge, col_edge = (e1, e2) if e1['type'] == 'row' else (e2, e1)
            row_idx = (i) if e1['type'] == 'row' else (j)
            col_idx = (j) if e1['type'] == 'row' else (i)

            # Kiểm tra tọa độ giao cắt
            if (col_edge['r_min'] < row_edge['r'] < col_edge['r_max']) and \
               (row_edge['c_min'] < col_edge['c'] < row_edge['c_max']):
                
                # Nếu cắt nhau: Không được có cầu ở cả 2 cạnh
                # Ràng buộc: NOT(row có cầu) OR NOT(col có cầu)
                # Biến v1 đại diện cho việc "có cầu"
                v1_row = edge_vars[row_idx]['v1']
                v1_col = edge_vars[col_idx]['v1']
                cnf.append([-v1_row, -v1_col])

    # Mapping lại biến để trả về cho hàm main decode
    final_var_map = {}
    for idx, edge in enumerate(possible_edges):
        u, v = edge['u'], edge['v']
        final_var_map[(u, v, 1)] = edge_vars[idx]['v1']
        final_var_map[(u, v, 2)] = edge_vars[idx]['v2']

    return cnf, {"var_map": final_var_map, "islands": islands}