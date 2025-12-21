# Source/solver_backtracking.py
"""
SAT Solver using Backtracking for Hashiwokakero
Includes:
- node_expanded
- execution time
- peak memory usage (tracemalloc)
"""

import time
import tracemalloc


class BacktrackingSAT:
    def __init__(self, cnf, meta, timeout=None):
        self.cnf = cnf
        self.meta = meta
        self.islands = meta["islands"]
        self.timeout = timeout
        self.edges = meta["edges"]
        self.n_edges = len(self.edges)
        self.var_map = meta["var_map"]
        self.n_vars = cnf.nv

        # ---------- Metrics ----------
        self.node_expanded = 0
        self.start_time = None

    # ======================================================
    # Unit Propagation
    # ======================================================

    def _unit_propagate(self, assignment):
        """
        Thực hiện unit propagation trên CNF
        Return: (success, new_assignment) hoặc (False, None) nếu conflict
        """
        assignment = dict(assignment)
        changed = True

        while changed:
            changed = False

            for clause in self.cnf.clauses:
                unassigned = []
                satisfied = False

                for lit in clause:
                    var = abs(lit)
                    if var in assignment:
                        if (lit > 0 and assignment[var]) or (lit < 0 and not assignment[var]):
                            satisfied = True
                            break
                    else:
                        unassigned.append(lit)

                if satisfied:
                    continue

                # Conflict: tất cả literals đều false
                if len(unassigned) == 0:
                    return False, None

                # Unit clause: chỉ còn 1 literal chưa assign
                if len(unassigned) == 1:
                    lit = unassigned[0]
                    var = abs(lit)
                    assignment[var] = (lit > 0)
                    changed = True

        return True, assignment

    # ======================================================
    # Check Satisfiability
    # ======================================================

    def _is_satisfied(self, assignment):
        """
        Kiểm tra xem assignment có thỏa mãn tất cả clauses không
        """
        for clause in self.cnf.clauses:
            satisfied = False
            for lit in clause:
                var = abs(lit)
                if var in assignment:
                    if (lit > 0 and assignment[var]) or (lit < 0 and not assignment[var]):
                        satisfied = True
                        break

            if not satisfied:
                return False

        return True

    # ======================================================
    # Variable Selection Heuristic
    # ======================================================

    def _select_variable(self, assignment):
        """
        Chọn biến chưa assign để branch
        Heuristic: Chọn biến xuất hiện nhiều nhất trong các clause chưa thỏa mãn
        """
        var_count = {}

        for clause in self.cnf.clauses:
            satisfied = False
            for lit in clause:
                var = abs(lit)
                if var in assignment:
                    if (lit > 0 and assignment[var]) or (lit < 0 and not assignment[var]):
                        satisfied = True
                        break

            if not satisfied:
                for lit in clause:
                    var = abs(lit)
                    if var not in assignment:
                        var_count[var] = var_count.get(var, 0) + 1

        if not var_count:
            # Nếu không có biến trong clause chưa thỏa mãn, chọn biến đầu tiên chưa assign
            for var in range(1, self.n_vars + 1):
                if var not in assignment:
                    return var
            return None

        # Chọn biến có tần suất cao nhất
        return max(var_count, key=var_count.get)

    # ======================================================
    # Solver
    # ======================================================

    def solve(self):
        tracemalloc.start()
        self.start_time = time.perf_counter()

        assignment = {}
        model = self._backtrack(assignment)

        elapsed = time.perf_counter() - self.start_time
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        return {
            "solution": model,
            "node_expanded": self.node_expanded,
            "time": elapsed,
            "peak_memory": peak,
            "success": model is not None
        }

    def _backtrack(self, assignment):
        # ---------- Timeout ----------
        if self.timeout is not None:
            if time.perf_counter() - self.start_time > self.timeout:
                return None

        self.node_expanded += 1

        # ---------- Unit Propagation ----------
        success, propagated = self._unit_propagate(assignment)
        if not success:
            return None  # Conflict detected

        assignment = propagated

        # ---------- Goal Test ----------
        if len(assignment) == self.n_vars:
            if self._is_satisfied(assignment):
                return self._format_model(assignment)
            return None

        # ---------- Select Variable ----------
        var = self._select_variable(assignment)
        if var is None:
            return None

        # ---------- Try True ----------
        new_assignment = assignment.copy()
        new_assignment[var] = True
        res = self._backtrack(new_assignment)
        if res is not None:
            return res

        # ---------- Try False ----------
        new_assignment = assignment.copy()
        new_assignment[var] = False
        res = self._backtrack(new_assignment)
        if res is not None:
            return res

        return None

    # ======================================================
    # Helpers
    # ======================================================

    def _format_model(self, assignment):
        """
        Convert assignment dict to model list
        """
        model = []
        for var in range(1, self.n_vars + 1):
            if var in assignment:
                model.append(var if assignment[var] else -var)
            else:
                model.append(-var)  # Default false
        return model