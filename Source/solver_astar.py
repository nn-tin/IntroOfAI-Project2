# Source/solver_astar.py
"""
A* SAT-based Solver for Hashiwokakero

Features:
- Unit propagation
- A* search (g + h)
- Node expansion counter
- Execution time
- Peak memory usage (tracemalloc)
"""

import time
import heapq
import tracemalloc


class AStarSAT:
    def __init__(self, cnf, meta, timeout=180.0):
        self.cnf = cnf
        self.meta = meta
        self.timeout = timeout

        self.n_vars = cnf.nv
        self.clauses = cnf.clauses

    # ======================================================
    # Unit Propagation
    # ======================================================

    def unit_propagate(self, assignment):
        """
        Perform unit propagation.
        Return (True, new_assignment) or (False, None) if conflict.
        """
        assignment = dict(assignment)
        changed = True

        while changed:
            changed = False

            for clause in self.clauses:
                satisfied = False
                unassigned = []

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

                # Conflict: all literals false
                if not unassigned:
                    return False, None

                # Unit clause
                if len(unassigned) == 1:
                    lit = unassigned[0]
                    assignment[abs(lit)] = (lit > 0)
                    changed = True

        return True, assignment

    # ======================================================
    # Heuristic
    # ======================================================

    def heuristic(self, assignment):
        """
        h(n): number of unassigned SAT variables
        """
        return self.n_vars - len(assignment)

    # ======================================================
    # SAT Check
    # ======================================================

    def is_satisfied(self, assignment):
        """
        Check whether assignment satisfies all clauses.
        """
        for clause in self.clauses:
            clause_ok = False
            for lit in clause:
                var = abs(lit)
                if var in assignment:
                    if (lit > 0 and assignment[var]) or (lit < 0 and not assignment[var]):
                        clause_ok = True
                        break
            if not clause_ok:
                return False
        return True

    # ======================================================
    # Variable Selection
    # ======================================================

    def select_unassigned_var(self, assignment):
        """
        Pick the smallest unassigned variable.
        """
        for var in range(1, self.n_vars + 1):
            if var not in assignment:
                return var
        return None

    # ======================================================
    # Solver
    # ======================================================

    def solve(self):
        tracemalloc.start()
        start_time = time.perf_counter()

        node_expanded = 0
        visited = set()
        pq = []

        start_assignment = {}
        h0 = self.heuristic(start_assignment)

        # (f, h, g, frozen_assignment)
        heapq.heappush(pq, (h0, h0, 0, frozenset()))

        while pq:
            # Timeout check
            if time.perf_counter() - start_time > self.timeout:
                break

            f, h, g, frozen = heapq.heappop(pq)
            assignment = dict(frozen)
            node_expanded += 1

            # Unit propagation
            ok, assignment = self.unit_propagate(assignment)
            if not ok:
                continue

            state_key = frozenset(assignment.items())
            if state_key in visited:
                continue
            visited.add(state_key)

            # Goal test
            if len(assignment) == self.n_vars:
                if self.is_satisfied(assignment):
                    current, peak = tracemalloc.get_traced_memory()
                    tracemalloc.stop()
                    return {
                        "solution": self.format_model(assignment),
                        "node_expanded": node_expanded,
                        "time": time.perf_counter() - start_time,
                        "peak_memory": peak,
                        "success": True
                    }
                continue

            # Branching
            var = self.select_unassigned_var(assignment)
            if var is None:
                continue

            for value in (True, False):
                new_assignment = dict(assignment)
                new_assignment[var] = value

                new_g = g + 1
                new_h = self.heuristic(new_assignment)
                new_f = new_g + new_h

                heapq.heappush(
                    pq,
                    (new_f, new_h, new_g, frozenset(new_assignment.items()))
                )

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return {
            "solution": None,
            "node_expanded": node_expanded,
            "time": time.perf_counter() - start_time,
            "peak_memory": peak,
            "success": False
        }

    # ======================================================
    # Helpers
    # ======================================================

    def format_model(self, assignment):
        """
        Convert assignment dict to DIMACS-style model list.
        """
        model = []
        for var in range(1, self.n_vars + 1):
            model.append(var if assignment.get(var, False) else -var)
        return model


# ======================================================
# Simple Test
# ======================================================

def main():
    class SimpleCNF:
        def __init__(self):
            self.nv = 5
            self.clauses = [
                [1, 2],
                [-1, 3],
                [-2, -3, 4],
                [5],
                [-5, 1]
            ]

    meta = {}  # Not used in this simplified test

    solver = AStarSAT(SimpleCNF(), meta, timeout=10.0)
    result = solver.solve()

    print("=== A* SAT Solver ===")
    print("Success:", result["success"])
    print("Solution:", result["solution"])
    print("Nodes Expanded:", result["node_expanded"])
    print(f"Time: {result['time']:.4f}s")
    print(f"Peak Memory: {result['peak_memory'] / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    main()
