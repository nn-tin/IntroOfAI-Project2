# Source/solver_backtracking.py
class BacktrackingSAT:
    def __init__(self, cnf):
        self.clauses = cnf.clauses
        self.n = cnf.nv

    def solve(self):
        return self.dfs({})

    def dfs(self, assign):
        # Nếu gán hết biến
        if len(assign) == self.n:
            if self.satisfied(assign):
                return assign
            return None
        
        var = len(assign) + 1  # gán biến theo thứ tự
        
        for val in [True, False]:
            assign[var] = val
            if not self.conflict(assign):      # nếu không mâu thuẫn → đi tiếp
                result = self.dfs(assign)
                if result: 
                    return result
            del assign[var]  # quay lui
        return None

    def conflict(self, assign):
        # giống has_conflict trong A*
        for clause in self.clauses:
            all_false = True
            for lit in clause:
                v = abs(lit)
                if v not in assign:
                    all_false = False
                    break
                if (lit>0 and assign[v]) or (lit<0 and not assign[v]):
                    all_false = False
                    break
            if all_false: 
                return True
        return False

    def satisfied(self, assign):
        for clause in self.clauses:
            if not any((lit>0 and assign[abs(lit)]) or (lit<0 and not assign[abs(lit)]) for lit in clause):
                return False
        return True
