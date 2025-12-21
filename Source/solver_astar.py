import time
import heapq

class AStarSAT:
    def __init__(self, clauses, n_vars, timeout=180.0):
        self.clauses = clauses
        self.n_vars = n_vars
        self.timeout = timeout

    def heuristic(self, assignment):
        """
        Heuristic: số clause chưa chắc chắn thoả mãn.
        Một clause được coi là 'chưa chắc chắn thoả' nếu chưa có literal True,
        và vẫn còn literal chưa gán biến.
        """
        count = 0
        assigned_vars = set(var for var, val in assignment.items())

        for clause in self.clauses:
            clause_satisfied = False
            undecided_literals = False
            for lit in clause:
                var = abs(lit)
                val = assignment.get(var)
                if val is not None:
                    if (lit > 0 and val is True) or (lit < 0 and val is False):
                        clause_satisfied = True
                        break
                else:
                    undecided_literals = True
            if not clause_satisfied:
                if undecided_literals:
                    # Clause chưa chắc chắn thoả
                    count += 1
                else:
                    # Clause bị conflict (tất cả literal False)
                    return float('inf')
        return count

    def is_conflict(self, assignment):
        """Kiểm tra có clause nào bị mâu thuẫn (không thể thoả) hay không."""
        for clause in self.clauses:
            clause_satisfied = False
            for lit in clause:
                var = abs(lit)
                val = assignment.get(var)
                if val is None:
                    clause_satisfied = True  # chưa biết => không conflict ngay
                    break
                if (lit > 0 and val is True) or (lit < 0 and val is False):
                    clause_satisfied = True
                    break
            if not clause_satisfied:
                return True  # conflict
        return False

    def solve(self):
        start_time = time.perf_counter()

        # Trạng thái đầu: gán biến rỗng
        start_assignment = {}

        # Hàm đánh giá f = g + h
        # g: số biến đã gán
        # h: heuristic
        start_h = self.heuristic(start_assignment)
        start_g = 0
        start_f = start_g + start_h

        pq = []
        heapq.heappush(pq, (start_f, start_g, start_assignment))

        visited = set()
        node_expanded = 0

        while pq:
            if time.perf_counter() - start_time > self.timeout:
                return {
                    "solution": None,
                    "node_expanded": node_expanded,
                    "time": time.perf_counter() - start_time,
                    "success": False,
                    "reason": "timeout"
                }

            f, g, assignment = heapq.heappop(pq)
            node_expanded += 1

            # Tạo khóa trạng thái để tránh lặp (tuple sorted)
            state_key = tuple(sorted(assignment.items()))
            if state_key in visited:
                continue
            visited.add(state_key)

            # Kiểm tra conflict
            if self.is_conflict(assignment):
                continue

            # Kiểm tra thoả CNF
            if len(assignment) == self.n_vars:
                # Gán hết biến rồi, kiểm tra CNF thoả?
                h = self.heuristic(assignment)
                if h == 0:
                    return {
                        "solution": assignment,
                        "node_expanded": node_expanded,
                        "time": time.perf_counter() - start_time,
                        "success": True
                    }
                else:
                    continue

            # Chọn biến chưa gán nhỏ nhất
            for var in range(1, self.n_vars + 1):
                if var not in assignment:
                    next_var = var
                    break

            # Mở rộng trạng thái với 2 nhánh: True / False
            for val in [True, False]:
                new_assignment = assignment.copy()
                new_assignment[next_var] = val

                if self.is_conflict(new_assignment):
                    continue

                h_new = self.heuristic(new_assignment)
                if h_new == float('inf'):
                    continue

                g_new = g + 1
                f_new = g_new + h_new

                heapq.heappush(pq, (f_new, g_new, new_assignment))

        return {
            "solution": None,
            "node_expanded": node_expanded,
            "time": time.perf_counter() - start_time,
            "success": False,
            "reason": "no_solution"
        }
