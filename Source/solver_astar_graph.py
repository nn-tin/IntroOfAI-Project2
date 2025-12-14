"""
A* Solver for Hashiwokakero using Graph Search
"""

import time
import heapq
from collections import deque

# --- Helper functions (similar to backtracking) ---

def check_connectivity(islands, bridges):
    if not islands:
        return True
    if not bridges and len(islands) > 1:
        return False
    n = len(islands)
    adj = {i: set() for i in range(n)}
    for b in bridges:
        adj[b["u"]].add(b["v"])
        adj[b["v"]].add(b["u"])
    
    visited = set()
    queue = deque([next(iter(adj))]) # Start from any island
    count = 0
    while queue:
        cur = queue.popleft()
        if cur in visited:
            continue
        visited.add(cur)
        count += 1
        for nb in adj[cur]:
            if nb not in visited:
                queue.append(nb)
    return count == n

def is_solved(islands, bridges):
    n = len(islands)
    degree = [0] * n
    for b in bridges:
        degree[b["u"]] += b["count"]
        degree[b["v"]] += b["count"]
    for i, isl in enumerate(islands):
        if degree[i] != isl["value"]:
            return False
    return True

# --- A* Specific Functions ---

def calculate_heuristic(islands, bridges, degrees):
    """
    Heuristic (h): Ước tính chi phí còn lại.
    Bao gồm:
    1. Số cầu tối thiểu cần thêm (remaining_degrees / 2).
    2. Chi phí kết nối các thành phần liên thông.
    """
    remaining_degrees = 0
    for i, isl in enumerate(islands):
        if degrees[i] < isl["value"]:
            remaining_degrees += isl["value"] - degrees[i]
        elif degrees[i] > isl["value"]:
            return float('inf') # Trạng thái không hợp lệ

    # Heuristic về kết nối:
    # Xây dựng đồ thị của các đảo chưa hoàn thành
    n = len(islands)
    adj = {i: set() for i in range(n)}
    for b in bridges:
        adj[b["u"]].add(b["v"])
        adj[b["v"]].add(b["u"])

    num_components = 0
    visited = set()
    for i in range(n):
        # Chỉ xét các đảo chưa hoàn thành hoặc các đảo đã hoàn thành nhưng là một phần của cây cầu
        if degrees[i] < islands[i]["value"] and i not in visited:
            num_components += 1
            # BFS để tìm tất cả các nút trong thành phần này
            q = deque([i])
            visited.add(i)
            while q:
                u = q.popleft()
                for v_neighbor in adj[u]:
                    if v_neighbor not in visited:
                        visited.add(v_neighbor)
                        q.append(v_neighbor)

    connectivity_h = max(0, num_components - 1)
    return (remaining_degrees / 2) + connectivity_h

def get_current_degrees(islands, bridges):
    degrees = [0] * len(islands)
    for b in bridges:
        degrees[b["u"]] += b["count"]
        degrees[b["v"]] += b["count"]
    return degrees

def bridges_to_tuple(bridges):
    """Converts a list of bridge dicts to a hashable tuple for the visited set."""
    return tuple(sorted((b['u'], b['v'], b['count']) for b in bridges))

# --- Main A* Solver ---

def get_successors(islands, edges, max_bridges, current_bridges, degrees):
    """Tạo các trạng thái kế thừa một cách thông minh."""
    
    # Tìm một đảo chưa hoàn thành để mở rộng
    expand_island_idx = -1
    for i in range(len(islands)):
        if degrees[i] < islands[i]["value"]:
            expand_island_idx = i
            break
    
    if expand_island_idx == -1:
        return [] # Không có đảo nào để mở rộng

    successors = []
    
    # Lấy các cạnh liên quan đến đảo này
    for edge in edges:
        if edge['u'] != expand_island_idx and edge['v'] != expand_island_idx:
            continue

        u, v = edge["u"], edge["v"]
        
        # Đảm bảo không thêm cầu vào đảo đã hoàn thành
        if degrees[u] == islands[u]["value"] or degrees[v] == islands[v]["value"]:
            continue

        existing_count = 0
        for b in current_bridges:
            if (b['u'] == u and b['v'] == v) or (b['u'] == v and b['v'] == u):
                existing_count = b['count']
                break
        
        if existing_count >= max_bridges:
            continue

        # Thử thêm 1 cầu
        if degrees[u] + 1 <= islands[u]["value"] and degrees[v] + 1 <= islands[v]["value"]:
            next_bridges = [b for b in current_bridges if not ((b['u'] == u and b['v'] == v) or (b['u'] == v and b['v'] == u))]
            next_bridges.append({"u": u, "v": v, "count": existing_count + 1, "dir": edge["type"]})
            successors.append(next_bridges)

        # Thử thêm 2 cầu
        if existing_count == 0 and max_bridges >= 2:
            if degrees[u] + 2 <= islands[u]["value"] and degrees[v] + 2 <= islands[v]["value"]:
                next_bridges = [b for b in current_bridges if not ((b['u'] == u and b['v'] == v) or (b['u'] == v and b['v'] == u))]
                next_bridges.append({"u": u, "v": v, "count": 2, "dir": edge["type"]})
                successors.append(next_bridges)

    return successors


def run_astar(meta, timeout=1000.0):
    """
    Solve Hashiwokakero using A* search.
    Returns:
      bridges (list[dict]) | None,
      elapsed_time (float),
      timed_out_flag (bool),
      connected_flag (bool)
    """
    t0 = time.perf_counter()
    
    islands = meta["islands"]
    edges = meta["edges"]
    max_bridges = meta.get("max_bridges", 2)

    # Priority queue: (f_cost, g_cost, tie_breaker, bridges_list)
    tie_breaker = 0
    start_bridges = []
    start_degrees = get_current_degrees(islands, start_bridges)
    h_start = calculate_heuristic(islands, start_bridges, start_degrees)
    pq = [(h_start, 0, tie_breaker, start_bridges)]
    tie_breaker += 1
    
    # Visited set to store hashable representations of states
    visited = set()

    while pq:
        if time.perf_counter() - t0 > timeout:
            return None, time.perf_counter() - t0, True, False

        f_cost, g_cost, _, current_bridges = heapq.heappop(pq)

        state_tuple = bridges_to_tuple(current_bridges)
        if state_tuple in visited:
            continue
        visited.add(state_tuple)

        degrees = get_current_degrees(islands, current_bridges)

        # Goal check
        if is_solved(islands, current_bridges):
            if check_connectivity(islands, current_bridges):
                elapsed = time.perf_counter() - t0
                return current_bridges, elapsed, False, True

        # Generate successors
        for next_bridges_state in get_successors(islands, edges, max_bridges, current_bridges, degrees):
            
            next_degrees = get_current_degrees(islands, next_bridges_state)
            h_new = calculate_heuristic(islands, next_bridges_state, next_degrees)
            if h_new == float('inf'):
                continue
            
            # g_cost là tổng số cầu đã đặt
            g_new = sum(b['count'] for b in next_bridges_state)
            f_new = g_new + h_new
            
            heapq.heappush(pq, (f_new, g_new, tie_breaker, next_bridges_state))
            tie_breaker += 1

    # No solution found
    elapsed = time.perf_counter() - t0
    return None, elapsed, False, False

# --- Input Parsing (copied from backtracking) ---

def read_input(filename):
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
    islands = []
    for i in range(len(board)):
        for j in range(len(board[i])):
            if board[i][j] > 0:
                islands.append({"x": j, "y": i, "value": board[i][j], "id": len(islands)})
    
    n = len(islands)
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            xi, yi = islands[i]["x"], islands[i]["y"]
            xj, yj = islands[j]["x"], islands[j]["y"]
            
            if yi == yj: # Horizontal
                if not any(board[yi][x] > 0 for x in range(xi + 1, xj)):
                    edges.append({"u": i, "v": j, "type": "H"})
            elif xi == xj: # Vertical
                if not any(board[y][xi] > 0 for y in range(yi + 1, yj)):
                    edges.append({"u": i, "v": j, "type": "V"})
    
    return {"islands": islands, "edges": edges, "max_bridges": 2}


if __name__ == "__main__":
    # Make sure the path is correct relative to where you run the script
    # If you run from the root folder: "Source/Inputs/input-05.txt"
    # If you run from the Source folder: "Inputs/input-05.txt"
    try:
        meta = parse_input_file("Source/Inputs/input-02.txt")
        bridges, elapsed, timed_out, connected = run_astar(meta, timeout=60)
        
        print("--- A* Solver ---")
        if bridges:
            print(f"Solution found in {elapsed:.4f} seconds.")
            # Sort for consistent output
            sorted_bridges = sorted(bridges, key=lambda b: (b['u'], b['v']))
            print("Bridges:", sorted_bridges)
        elif timed_out:
            print(f"Solver timed out after {elapsed:.4f} seconds.")
        else:
            print(f"No solution found. Searched for {elapsed:.4f} seconds.")
        
        print("Timed out:", timed_out)
        print("Connected:", connected)

    except FileNotFoundError:
        print("Error: Input file not found. Please check the path.")
