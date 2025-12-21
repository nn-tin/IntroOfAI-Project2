import time
import heapq
import tracemalloc

class AStarSAT:
    def __init__(self, cnf_clauses, num_vars, timeout=180.0):
        """
        cnf_clauses: List[List[int]], mỗi clause là list các literal (ví dụ: [1, -2, 3])
        num_vars: số biến tối đa, biến đánh số từ 1..num_vars
        """
        self.clauses = cnf_clauses
        self.num_vars = num_vars
        self.timeout = timeout

    def is_satisfied(self, assignment):
        for clause in self.clauses:
            satisfied = False
            for lit in clause:
                var = abs(lit)
                val = assignment.get(var, None)
                if val is None:
                    # biến chưa gán
                    satisfied = True  # có khả năng thỏa, tiếp tục
                    break
                if (lit > 0 and val == True) or (lit < 0 and val == False):
                    satisfied = True
                    break
            if not satisfied:
                return False
        return True

    def is_conflict(self, assignment):
        # Kiểm tra có clause nào chắc chắn không thể thỏa (tất cả literal False)
        for clause in self.clauses:
            conflict = True
            for lit in clause:
                var = abs(lit)
                val = assignment.get(var, None)
                if val is None:
                    conflict = False
                    break
                if (lit > 0 and val == True) or (lit < 0 and val == False):
                    conflict = False
                    break
            if conflict:
                return True
        return False

    def heuristic(self, assignment):
        # Đếm số clause chưa chắc chắn thỏa
        count = 0
        for clause in self.clauses:
            satisfied = False
            for lit in clause:
                var = abs(lit)
                val = assignment.get(var, None)
                if val is None:
                    satisfied = True
                    break
                if (lit > 0 and val == True) or (lit < 0 and val == False):
                    satisfied = True
                    break
            if not satisfied:
                count += 1
        return count

    def solve(self):
        tracemalloc.start()
        t0 = time.perf_counter()

        node_expanded = 0
        visited = set()
        frontier = []

        start_assign = dict()
        start_h = self.heuristic(start_assign)
        g = 0
        heapq.heappush(frontier, (g + start_h, g, start_assign))

        while frontier:
            if time.perf_counter() - t0 > self.timeout:
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                return {
                    "solution": None,
                    "node_expanded": node_expanded,
                    "time": time.perf_counter() - t0,
                    "peak_memory": peak,
                    "success": False
                }

            f, g, assignment = heapq.heappop(frontier)
            node_expanded += 1

            # Tạo key trạng thái để tránh lặp
            key = tuple(sorted(assignment.items()))
            if key in visited:
                continue
            visited.add(key)

            if self.is_conflict(assignment):
                continue

            if self.is_satisfied(assignment):
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                return {
                    "solution": assignment,
                    "node_expanded": node_expanded,
                    "time": time.perf_counter() - t0,
                    "peak_memory": peak,
                    "success": True
                }

            # Chọn biến chưa gán nhỏ nhất
            for var in range(1, self.num_vars + 1):
                if var not in assignment:
                    # Branch True
                    new_assign_true = assignment.copy()
                    new_assign_true[var] = True
                    if not self.is_conflict(new_assign_true):
                        h_new = self.heuristic(new_assign_true)
                        heapq.heappush(frontier, (g + 1 + h_new, g + 1, new_assign_true))
                    # Branch False
                    new_assign_false = assignment.copy()
                    new_assign_false[var] = False
                    if not self.is_conflict(new_assign_false):
                        h_new = self.heuristic(new_assign_false)
                        heapq.heappush(frontier, (g + 1 + h_new, g + 1, new_assign_false))
                    break  # chỉ xét một biến chưa gán một lượt

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return {
            "solution": None,
            "node_expanded": node_expanded,
            "time": time.perf_counter() - t0,
            "peak_memory": peak,
            "success": False
        }


if __name__ == "__main__":
    # Ví dụ CNF: (x1 or not x2) and (not x1 or x3) and (x2 or not x3)
    clauses = [
        [1, -2],
        [-1, 3],
        [2, -3]
    ]
    num_vars = 3

    solver = AStarSAT(clauses, num_vars)
    result = solver.solve()
    if result["success"]:
        print("Found solution:")
        for var in range(1, num_vars + 1):
            print(f"x{var} = {result['solution'].get(var, 'undefined')}")
    else:
        print("No solution found.")
