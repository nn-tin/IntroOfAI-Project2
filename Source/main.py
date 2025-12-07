# main.py
# Chương trình chính, gọi helper đọc dữ liệu, tạo CNF, giải bằng pysat

from pysat.solvers import Glucose3
from helper_01 import read_input, print_board
from helper_02 import generate_cnf, var_bridge
import time

def decode_solution(model, edges):
    """
    Giải mã kết quả model trả về từ pysat
    Trả về ma trận kết quả hiển thị cầu nối (ký hiệu |, $, -, =)
    """
    # Tạo board kết quả tương tự đầu vào
    # Mỗi cầu nối ứng với 1 hoặc 2 cây cầu ngang/dọc
    # Dùng ký hiệu đề bài
    pass

def solve_with_pysat(board):
    cnf, edges = generate_cnf(board)
    solver = Glucose3()
    for clause in cnf.clauses:
        solver.add_clause(clause)

    start = time.time()
    sat = solver.solve()
    end = time.time()
    print(f"Solver finished: SAT={sat} in {end - start:.4f}s")

    if sat:
        model = solver.get_model()
        result = decode_solution(model, edges)
        return result
    else:
        return None


if __name__ == "__main__":
    board = read_input('Inputs/input-01.txt')
    print("Input board:")
    print_board(board)

    result = solve_with_pysat(board)

    if result is None:
        print("No solution found.")
    else:
        print("Solution:")
        for row in result:
            print(' '.join(row))
