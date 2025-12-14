# Source/main.py
"""
Experiment runner for Hashiwokakero SAT:
- Generate CNF (helper_02)
- Solve by: PySAT(Glucose3), A*, Backtracking, Brute-force
- Measure time, check connectivity, export outputs and CSV summary
Usage:
    python main.py                # runs default inputs (input-01.txt ... input-05.txt)
    python main.py input-03.txt   # runs only that input
    python main.py all            # run default batch
"""

import os
import sys
import time
import csv
import multiprocessing as mp

import helper_01
import helper_02
from helper_02 import build_output_grid, export_output_grid  # output helpers

from solver_astar import AStarSAT
from solver_backtracking import BacktrackingSAT
from solver_bruteforce import BruteForceSAT
from solver_pysat import run_pysat, check_connectivity_from_model, model_to_bridges

# ----------------- Config -----------------
TIMEOUT_PYSAT = 60.0
TIMEOUT_ASTAR = 30.0
TIMEOUT_BACKTRACK = 10.0
TIMEOUT_BRUTEFORCE = 10.0

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUTS_DIR = os.path.join(BASE_DIR, "Inputs")
OUTPUTS_DIR = os.path.join(BASE_DIR, "Outputs")
RESULTS_DIR = os.path.join(BASE_DIR, "Results")
os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

DEFAULT_INPUTS = [f"input-{i:02}.txt" for i in range(1, 6)]
CSV_PATH = os.path.join(RESULTS_DIR, "experiment_results.csv")

# ----------------- Utilities & multiprocessing worker -----------------
def worker(q, fn, args):
    """
    Global worker function — MUST be global (not nested) for Windows multiprocessing.
    Puts ("ok", result) or ("err", errmsg) into queue.
    """
    try:
        res = fn(*args)
        q.put(("ok", res))
    except Exception as e:
        q.put(("err", repr(e)))

def run_with_timeout(target_fn, args=(), timeout=60.0):
    """
    Run target_fn(*args) in separate process with timeout.
    Returns: (success_flag, payload, elapsed_seconds, timed_out_flag)
    payload is result (if success) or error string (if not success).
    """
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
    
# ----------------- Solver wrappers -----------------
def run_astar_proc(cnf, meta):
    ast = AStarSAT(cnf, meta)
    return ast.solve()

def run_backtracking_proc(cnf, meta):
    bt = BacktrackingSAT(cnf, meta, timeout=None)
    return bt.solve()

def run_bruteforce_proc(cnf, meta):
    bf = BruteForceSAT(cnf, meta, timeout=None)
    return bf.solve()

# ----------------- Experiment per file -----------------
def experiment_on_file(input_filename, solvers=("pysat","astar","backtracking","bruteforce")):
    path = os.path.join(INPUTS_DIR, input_filename)
    if not os.path.exists(path):
        print(f"[SKIP] {input_filename} not found")
        return []

    print(f"\n=== Experiment: {input_filename} ===")
    board = helper_01.read_input(path)
    cnf, meta = helper_02.generate_cnf(board)
    rows = []

    # 1) PySAT
    if "pysat" in solvers:
        print("-> Running PySAT...")
        model, elapsed, timed_out, connected = run_pysat(cnf, meta, timeout=TIMEOUT_PYSAT)
        sat = model is not None
        print(f"   PySAT: sat={sat}, time={elapsed:.4f}s, timeout={timed_out}, connected={connected}")
        if sat:
            bridges = model_to_bridges(meta, model)
            grid = build_output_grid(board, meta, bridges)
            fname = input_filename.replace("input", "output").replace(".txt", "-pysat.txt")
            export_output_grid(grid, fname)
        rows.append({"filename":input_filename, "solver":"pysat", "sat":sat, "time":elapsed, "timeout":timed_out, "connected":connected})

    # 2) A*
    if "astar" in solvers:
        print("-> Running A*...")
        ok, model, elapsed, timed_out = run_with_timeout(run_astar_proc, args=(cnf, meta), timeout=TIMEOUT_ASTAR)
        sat = (ok and model is not None)
        connected = False
        if sat:
            connected = check_connectivity_from_model(model, meta)
            bridges = model_to_bridges(meta, model)
            grid = build_output_grid(board, meta, bridges)
            fname = input_filename.replace("input","output").replace(".txt","-astar.txt")
            export_output_grid(grid, fname)
        print(f"   A*: sat={sat}, time={elapsed:.4f}s, timeout={timed_out}, connected={connected}")
        rows.append({"filename":input_filename, "solver":"astar", "sat":sat, "time":elapsed, "timeout":timed_out, "connected":connected})

    # 3) Backtracking
    if "backtracking" in solvers:
        print("-> Running Backtracking...")
        ok, model, elapsed, timed_out = run_with_timeout(run_backtracking_proc, args=(cnf, meta), timeout=TIMEOUT_BACKTRACK)
        sat = (ok and model is not None)
        connected = False
        if sat:
            connected = check_connectivity_from_model(model, meta)
            bridges = model_to_bridges(meta, model)
            grid = build_output_grid(board, meta, bridges)
            fname = input_filename.replace("input","output").replace(".txt","-backtracking.txt")
            export_output_grid(grid, fname)
        print(f"   Backtracking: sat={sat}, time={elapsed:.4f}s, timeout={timed_out}, connected={connected}")
        rows.append({"filename":input_filename, "solver":"backtracking", "sat":sat, "time":elapsed, "timeout":timed_out, "connected":connected})

    # 4) Brute-force
    if "bruteforce" in solvers:
        print("-> Running Brute-force...")
        ok, model, elapsed, timed_out = run_with_timeout(run_bruteforce_proc, args=(cnf, meta), timeout=TIMEOUT_BRUTEFORCE)
        sat = (ok and model is not None)
        connected = False
        if sat:
            connected = check_connectivity_from_model(model, meta)
            bridges = model_to_bridges(meta, model)
            grid = build_output_grid(board, meta, bridges)
            fname = input_filename.replace("input","output").replace(".txt","-bruteforce.txt")
            export_output_grid(grid, fname)
        print(f"   Brute-force: sat={sat}, time={elapsed:.4f}s, timeout={timed_out}, connected={connected}")
        rows.append({"filename":input_filename, "solver":"bruteforce", "sat":sat, "time":elapsed, "timeout":timed_out, "connected":connected})

    return rows

# ----------------- Batch runner -----------------
def run_batch(input_list=None, out_csv=CSV_PATH):
    if input_list is None:
        input_list = DEFAULT_INPUTS

    results = []
    for fname in input_list:
        rows = experiment_on_file(fname)
        results.extend(rows)

    header = ["filename","solver","sat","time","timeout","connected"]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for r in results:
            writer.writerow(r)
    print(f"\nAll experiments done. Results saved to: {out_csv}")

# ----------------- Main -----------------
if __name__ == "__main__":
    # Needed for Windows multiprocessing safe spawn
    mp.freeze_support()

    if len(sys.argv) == 1:
        run_batch()
    elif len(sys.argv) == 2:
        arg = sys.argv[1].lower()
        if arg == "all":
            run_batch()
        elif arg.endswith(".txt"):
            run_batch([arg])
        else:
            print("Usage: python main.py [input-file.txt | all]")
    else:
        # If multiple files provided
        files = [f for f in sys.argv[1:] if f.endswith(".txt")]
        if files:
            run_batch(files)
        else:
            print("Usage: python main.py [input-file.txt | all]")
