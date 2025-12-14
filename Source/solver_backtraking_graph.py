"""
Backtracking Solver for Hashiwokakero using Graph Search
"""

import time
from collections import deque

def is_valid_bridge(islands, bridges, u, v, count, max_bridges):
    # Kiểm tra số cầu tối đa giữa hai đảo
    current = 0
    for b in bridges:
        if (b["u"], b["v"]) == (u, v) or (b["u"], b["v"]) == (v, u):
            current += b["count"]
    if current + count > max_bridges:
        return False
    return True

def check_connectivity(islands, bridges):
    # Xây dựng đồ thị kề
    n = len(islands)
    adj = {i: set() for i in range(n)}
    for b in bridges:
        adj[b["u"]].add(b["v"])
        adj[b["v"]].add(b["u"])
    # BFS kiểm tra liên thông
    visited = set()
    queue = deque([0])
    while queue:
        cur = queue.popleft()
        if cur in visited:
            continue
        visited.add(cur)
        for nb in adj[cur]:
            if nb not in visited:
                queue.append(nb)
    return len(visited) == n

def is_solved(islands, bridges):
    # Kiểm tra tổng số cầu đến mỗi đảo
    n = len(islands)
    degree = [0] * n
    for b in bridges:
        degree[b["u"]] += b["count"]
        degree[b["v"]] += b["count"]
    for i, isl in enumerate(islands):
        if degree[i] != isl["value"]:
            return False
    return True

def get_possible_edges(meta):
    # Trả về danh sách các cạnh hợp lệ
    return meta["edges"]

def get_constrained_island(islands, bridges):
    """Tìm đảo có bậc gần đạt giới hạn (heuristic)"""
    n = len(islands)
    degree = [0] * n
    for b in bridges:
        degree[b["u"]] += b["count"]
        degree[b["v"]] += b["count"]
    
    # Ưu tiên đảo có degree gần bằng value (gần hoàn thành)
    best_idx = -1
    best_score = -1
    for i in range(n):
        remaining = islands[i]["value"] - degree[i]
        if remaining > 0:
            score = islands[i]["value"] - remaining  # Càng cao càng tốt
            if score > best_score:
                best_score = score
                best_idx = i
    return best_idx

def get_edges_for_island(edges, island_idx):
    """Lấy các cạnh liên quan đến đảo"""
    return [e for e in edges if e["u"] == island_idx or e["v"] == island_idx]

def backtrack(islands, meta, bridges, edge_idx, max_bridges, t0, timeout):
    if time.perf_counter() - t0 > timeout:
        return None, True  # Timeout

    if is_solved(islands, bridges):
        if check_connectivity(islands, bridges):
            return bridges[:], False
        return None, False

    edges = get_possible_edges(meta)
    if edge_idx >= len(edges):
        return None, False

    # Cắt tỉa: Kiểm tra constraint mỗi đảo
    n = len(islands)
    degree = [0] * n
    for b in bridges:
        degree[b["u"]] += b["count"]
        degree[b["v"]] += b["count"]
    
    for i in range(n):
        if degree[i] > islands[i]["value"]:
            return None, False  # Vô lý, cắt nhánh
    
    e = edges[edge_idx]
    u, v = e["u"], e["v"]
    dir = "H" if e["type"] == "H" else "V"

    # Thử không đặt cầu
    result, timed_out = backtrack(islands, meta, bridges, edge_idx + 1, max_bridges, t0, timeout)
    if result is not None or timed_out:
        return result, timed_out

    # Thử đặt 1 cầu
    if is_valid_bridge(islands, bridges, u, v, 1, max_bridges):
        if degree[u] + 1 <= islands[u]["value"] and degree[v] + 1 <= islands[v]["value"]:
            bridges.append({"u": u, "v": v, "count": 1, "dir": dir})
            result, timed_out = backtrack(islands, meta, bridges, edge_idx + 1, max_bridges, t0, timeout)
            if result is not None or timed_out:
                return result, timed_out
            bridges.pop()

    # Thử đặt 2 cầu
    if is_valid_bridge(islands, bridges, u, v, 2, max_bridges):
        if degree[u] + 2 <= islands[u]["value"] and degree[v] + 2 <= islands[v]["value"]:
            bridges.append({"u": u, "v": v, "count": 2, "dir": dir})
            result, timed_out = backtrack(islands, meta, bridges, edge_idx + 1, max_bridges, t0, timeout)
            if result is not None or timed_out:
                return result, timed_out
            bridges.pop()

    return None, False

def run_backtracking(meta, timeout=1000.0):
    """
    Solve Hashiwokakero bằng backtracking.
    Returns:
      bridges (list[dict]) | None,
      elapsed_time (float),
      timed_out_flag (bool),
      connected_flag (bool)
    """
    t0 = time.perf_counter()
    islands = meta["islands"]
    max_bridges = meta.get("max_bridges", 2)
    bridges, timed_out = backtrack(islands, meta, [], 0, max_bridges, t0, timeout)
    elapsed = time.perf_counter() - t0
    connected = bridges is not None and check_connectivity(islands, bridges)
    return bridges, elapsed, timed_out, connected

def read_input(filename):
    """
    Đọc file input Hashiwokakero, trả về matrix 2D kiểu int,
    với 0 là ô trống, số 1-8 là đảo
    """
    board = []
    with open(filename, 'r') as f:
        for line in f:
            if line.strip() == '':
                continue
            row = [int(x.strip()) for x in line.strip().split(',')]
            board.append(row)
    return board

def parse_input_file(filepath):
    board = read_input(filepath)
    # Tìm tất cả các đảo từ board
    islands = []
    island_map = {}
    for i in range(len(board)):
        for j in range(len(board[i])):
            if board[i][j] > 0:
                island_map[(i, j)] = len(islands)
                islands.append({"x": j, "y": i, "value": board[i][j]})
    
    # Sinh edges (các cạnh có thể nối đảo)
    n = len(islands)
    edges = []
    for i in range(n):
        xi, yi = islands[i]["x"], islands[i]["y"]
        for j in range(i+1, n):
            xj, yj = islands[j]["x"], islands[j]["y"]
            # Cùng hàng (ngang)
            if yi == yj and xi < xj:
                blocked = any(board[yi][x] > 0 for x in range(xi+1, xj))
                if not blocked:
                    edges.append({"u": i, "v": j, "type": "H"})
            # Cùng cột (dọc)
            if xi == xj and yi < yj:
                blocked = any(board[y][xi] > 0 for y in range(yi+1, yj))
                if not blocked:
                    edges.append({"u": i, "v": j, "type": "V"})
    
    return {"islands": islands, "edges": edges, "max_bridges": 2}


if __name__ == "__main__":
    meta = parse_input_file("Source/Inputs/input-05.txt")
    bridges, elapsed, timed_out, connected = run_backtracking(meta, timeout=50)
    print("Bridges:", bridges)
    print("Elapsed time:", elapsed)
    print("Timed out:", timed_out)
    print("Connected:", connected)