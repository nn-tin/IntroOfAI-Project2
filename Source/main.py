# Source/main.py
"""
Experiment runner for Hashiwokakero:
- SAT solvers: PySAT, A* SAT, Backtracking SAT, Brute-force SAT
- Graph solvers: A* Graph, Backtracking Graph
- Measure time, node expanded, connectivity
- Export outputs and CSV summary
"""

import os
import sys
import time
import csv
import multiprocessing as mp

import helper_01
import helper_02
from helper_02 import build_output_grid, export_output_grid

# ---------- SAT-based solvers ----------
from solver_astar import AStarSAT
from solver_backtracking import BacktrackingSAT
from solver_bruteforce import BruteForceSAT
from solver_pysat import run_pysat, check_connectivity_from_model, model_to_bridges

# ---------- GRAPH-based solvers ----------
from solver_astar_graph import AStarGraphSolver
from solver_astar_graph import check_connectivity
from solver_backtracking_graph import BacktrackingGraphSolver


# ================= CONFIG =================
TIMEOUT_PYSAT = 60.0
TIMEOUT_ASTAR = 60.0
TIMEOUT_BACKTRACK = 180.0
TIMEOUT_BRUTEFORCE = 180.0

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUTS_DIR = os.path.join(BASE_DIR, "Inputs")
OUTPUTS_DIR = os.path.join(BASE_DIR, "Outputs")
RESULTS_DIR = os.path.join(BASE_DIR, "Results")

os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

DEFAULT_INPUTS = [f"input-{i:02}.txt" for i in range(1, 11)]
CSV_PATH = os.path.join(RESULTS_DIR, "experiment_results.csv")


# ================= MULTIPROCESSING =================
def worker(q, fn, args):
    try:
        res = fn(*args)
        q.put(("ok", res))
    except Exception as e:
        q.put(("err", repr(e)))


def run_with_timeout(target_fn, args=(), timeout=60.0):
    q = mp.Queue()
    p = mp.Process(target=worker, args=(q, target_fn, args))

    t0 = time.perf_counter()
    p.start()
    p.join(timeout)
    elapsed = time.perf_counter() - t0

    if p.is_alive():
        p.terminate()
        p.join()
        return False, None, elapsed, True

    if q.empty():
        return False, None, elapsed, False

    status, payload = q.get()
    if status == "ok":
        return True, payload, elapsed, False
    else:
        return False, payload, elapsed, False


# ================= SOLVER WRAPPERS =================
def run_astar_proc(cnf, meta):
    solver = AStarSAT(cnf, meta, timeout=TIMEOUT_ASTAR)
    return solver.solve()


def run_backtracking_proc(cnf, meta):
    solver = BacktrackingSAT(cnf, meta, timeout=TIMEOUT_BACKTRACK)
    return solver.solve()


def run_bruteforce_proc(cnf, meta):
    solver = BruteForceSAT(cnf, meta, timeout=TIMEOUT_BRUTEFORCE)
    return solver.solve()


def run_astar_graph_proc(meta):
    solver = AStarGraphSolver(meta)
    return solver.solve()   



def run_backtracking_graph_proc(meta):
    solver = BacktrackingGraphSolver(meta, timeout=None)
    return solver.solve()   


# ================= EXPERIMENT PER FILE =================
def experiment_on_file(
    input_filename,
    solvers=(
        "pysat",
        "astar",
        "astar_graph",
        "backtracking",
        "backtracking_graph",
        "bruteforce",
    ),
):
    path = os.path.join(INPUTS_DIR, input_filename)
    if not os.path.exists(path):
        print(f"[SKIP] {input_filename} not found")
        return []

    print(f"\n=== Experiment: {input_filename} ===")
    board = helper_01.read_input(path)
    cnf, meta = helper_02.generate_cnf(board)

    rows = []

    # ---------- PySAT ----------
    if "pysat" in solvers:
        print("-> Running PySAT...")
        model, elapsed, timed_out, connected = run_pysat(
            cnf, meta, timeout=TIMEOUT_PYSAT
        )
        sat = model is not None

        if sat:
            bridges = model_to_bridges(meta, model)
            grid = build_output_grid(board, meta, bridges)
            fname = input_filename.replace(
                "input", "output"
            ).replace(".txt", "-pysat.txt")
            export_output_grid(grid, fname)

        rows.append({
            "filename": input_filename,
            "solver": "pysat",
            "sat": sat,
            "time": elapsed,
            "node_expanded": None,
            "timeout": timed_out,
            "connected": connected,
        })

   # ---------- A* SAT ----------
    if "astar" in solvers:
        print("-> Running A* SAT...")
        ok, result, elapsed, timed_out = run_with_timeout(
            run_astar_proc, args=(cnf, meta), timeout=TIMEOUT_ASTAR
        )
        sat = False
        connected = False
        node_expanded = None

        if ok and isinstance(result, dict):
            sat = result.get("success", False)
            node_expanded = result.get("node_expanded", None)
            model = result.get("solution", None)

            if sat and model is not None:
                connected = check_connectivity_from_model(model, meta)
                bridges = model_to_bridges(meta, model)
                grid = build_output_grid(board, meta, bridges)
                fname = input_filename.replace(
                    "input", "output"
                ).replace(".txt", "-astar.txt")
                export_output_grid(grid, fname)

        rows.append({
            "filename": input_filename,
            "solver": "astar",
            "sat": sat,
            "time": elapsed,
            "node_expanded": node_expanded,
            "timeout": timed_out,
            "connected": connected,
        })

    def convert_solution_to_bridges(solution, meta):
        bridges = []
        islands = meta["islands"]
        for edge in solution:
            u, v, count = edge['u'], edge['v'], edge['count']

            x1, y1 = islands[u]['c'], islands[u]['r']
            x2, y2 = islands[v]['c'], islands[v]['r']

            if x1 == x2:
                dir_ = "V"
                x = x1
                y = min(y1, y2)
            elif y1 == y2:
                dir_ = "H"
                x = min(x1, x2)
                y = y1
            else:
                # Nếu cầu không thẳng hàng, bỏ qua
                continue

            bridges.append({
                "u": u,
                "v": v,
                "x": x,
                "y": y,
                "count": count,
                "dir": dir_,
            })
        return bridges

   # ---------- A* GRAPH ----------
    if "astar_graph" in solvers:
        print("-> Running A* Graph...")
        ok, result, elapsed, timed_out = run_with_timeout(
            run_astar_graph_proc, args=(meta,), timeout=TIMEOUT_ASTAR
        )

        sat = False
        connected = False
        node_expanded = None

        if ok and isinstance(result, dict):
            node_expanded = result.get("node_expanded")
            solution = result.get("solution")
            sat = solution is not None
            connected = (
                check_connectivity(meta["islands"], solution)
                if solution else False
            )
            if sat:
               if sat:
                bridges = convert_solution_to_bridges(solution, meta)
                grid = build_output_grid(board, meta, bridges)
                fname = input_filename.replace("input", "output").replace(".txt", "-astar_graph.txt")
                export_output_grid(grid, fname)
        else:
            if isinstance(result, dict):
                node_expanded = result.get("node_expanded")

        rows.append({
            "filename": input_filename,
            "solver": "astar_graph",
            "sat": sat,
            "time": elapsed,
            "node_expanded": node_expanded,
            "timeout": timed_out,
            "connected": connected,
        })



    # ---------- Backtracking SAT ----------
    if "backtracking" in solvers:
        print("-> Running Backtracking SAT...")
        ok, result, elapsed, timed_out = run_with_timeout(
            run_backtracking_proc, args=(cnf, meta), timeout=TIMEOUT_BACKTRACK
        )

        sat = False
        connected = False
        node_expanded = None

        if ok and isinstance(result, dict):
            sat = result["success"]
            node_expanded = result["node_expanded"]
            model = result["solution"]

            if sat:
                connected = check_connectivity_from_model(model, meta)
                bridges = model_to_bridges(meta, model)
                grid = build_output_grid(board, meta, bridges)
                fname = input_filename.replace(
                    "input", "output"
                ).replace(".txt", "-backtracking.txt")
                export_output_grid(grid, fname)

        rows.append({
            "filename": input_filename,
            "solver": "backtracking",
            "sat": sat,
            "time": elapsed,
            "node_expanded": node_expanded,
            "timeout": timed_out,
            "connected": connected,
        })

    # ---------- Backtracking GRAPH ----------
    if "backtracking_graph" in solvers:
        print("-> Running Backtracking Graph...")
        ok, result, elapsed, timed_out = run_with_timeout(
            run_backtracking_graph_proc, args=(meta,), timeout=TIMEOUT_BACKTRACK
        )

        sat = False
        connected = False
        node_expanded = None

        if ok and isinstance(result, dict):
            node_expanded = result.get("node_expanded")
            solution = result.get("solution")
            sat = solution is not None
            connected = (
                check_connectivity(meta["islands"], solution)
                if solution else False
            )

            if sat:
                bridges = convert_solution_to_bridges(solution, meta)
                grid = build_output_grid(board, meta, bridges)
                fname = input_filename.replace(
                    "input", "output"
                ).replace(".txt", "-backtracking_graph.txt")
                export_output_grid(grid, fname)
        else:
            if isinstance(result, dict):
                node_expanded = result.get("node_expanded")

        rows.append({
            "filename": input_filename,
            "solver": "backtracking_graph",
            "sat": sat,
            "time": elapsed,
            "node_expanded": node_expanded,
            "timeout": timed_out,
            "connected": connected,
        })
    
    # ---------- Brute-force SAT ----------
    if "bruteforce" in solvers:
        print("-> Running Brute-force SAT...")
        ok, result, elapsed, timed_out = run_with_timeout(
            run_bruteforce_proc, args=(cnf, meta), timeout=TIMEOUT_BRUTEFORCE
        )

        sat = False
        connected = False
        node_expanded = None

        if ok and isinstance(result, dict):
            sat = result["success"]
            node_expanded = result["node_expanded"]
            model = result["solution"]

            if sat:
                connected = check_connectivity_from_model(model, meta)
                bridges = model_to_bridges(meta, model)
                grid = build_output_grid(board, meta, bridges)
                fname = input_filename.replace(
                    "input", "output"
                ).replace(".txt", "-bruteforce.txt")
                export_output_grid(grid, fname)

        rows.append({
            "filename": input_filename,
            "solver": "bruteforce",
            "sat": sat,
            "time": elapsed,
            "node_expanded": node_expanded,
            "timeout": timed_out,
            "connected": connected,
        })

    return rows


# ================= BATCH RUNNER =================
def run_batch(input_list=None, out_csv=CSV_PATH):
    if input_list is None:
        input_list = DEFAULT_INPUTS

    results = []
    for fname in input_list:
        rows = experiment_on_file(fname)
        results.extend(rows)

    header = [
        "filename",
        "solver",
        "sat",
        "time",
        "node_expanded",
        "timeout",
        "connected",
    ]

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    print(f"\nAll experiments done. Results saved to: {out_csv}")


# ================= MAIN =================
if __name__ == "__main__":
    mp.freeze_support()

    if len(sys.argv) == 1:
        # Chạy tất cả file input, lưu file tổng hợp mặc định
        run_batch()
    elif len(sys.argv) == 2:
        arg = sys.argv[1].lower()
        if arg == "all":
            run_batch()
        elif arg.endswith(".txt"):
            # Lưu kết quả vào file CSV riêng cho từng input
            csv_name = f"experiment_results_{arg.replace('.txt','')}.csv"
            csv_path = os.path.join(RESULTS_DIR, csv_name)
            run_batch([arg], out_csv=csv_path)
        else:
            print("Usage: python main.py [input-file.txt | all]")
    else:
        files = [f for f in sys.argv[1:] if f.endswith(".txt")]
        if files:
            if len(files) == 1:
                csv_name = f"experiment_results_{files[0].replace('.txt','')}.csv"
                csv_path = os.path.join(RESULTS_DIR, csv_name)
                run_batch(files, out_csv=csv_path)
            else:
                # Nhiều file -> lưu file tổng hợp
                run_batch(files)
        else:
            print("Usage: python main.py [input-file.txt | all]")
