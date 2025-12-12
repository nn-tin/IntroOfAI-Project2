# Source/solver_bruteforce.py
import heapq
import sys
import os

class BruteForceSAT:
    def __init__(self, cnf):
        self.clauses = cnf.clauses
        self.n = cnf.nv

    def solve(self):
        total = 1 << self.n  # 2^n
        for mask in range(total):
            if self.check(mask):
                # chuyển bitmask -> model True/False dạng SAT
                return [(i+1) if (mask >> i) & 1 else -(i+1) for i in range(self.n)]
        return None

    def check(self, mask):
        for clause in self.clauses:
            ok = False
            for lit in clause:
                var = abs(lit) - 1
                val = (mask >> var) & 1
                if (lit > 0 and val == 1) or (lit < 0 and val == 0):
                    ok = True
                    break
            if not ok:
                return False
        return True
