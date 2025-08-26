import os
import sys
import time

# Add root directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dpll import SAT_dpll
from DIMACS_reader import read_DIMACS
from task1.DIMACS_encoding import DIMACS_decoder

from decision_heuristics.choose_literal.choose_best_score import choose_literal
from decision_heuristics.choose_literal.choose_random import choose_random
from decision_heuristics.precompute_score.jaroslow_wang_h import JW_heuristic
from decision_heuristics.precompute_score.lit_counts_h import lit_counts_h

from propagate.unit_propagate_adjacency_list import unit_propagate_basic
from propagate.unit_propagate_watched_literals import unit_propagate_w_watched_lits
from decision_heuristics.precompute_score.VSIDS import VSIDs

def collect_files_ais(prefix : str) -> list[str]:
    return [f"{prefix}inputs\\ais\\ais{i}.cnf" for i in range(6, 13, 2)]


def collect_files(prefix: str, rng: int, start=0) -> list[str]:
    return [f"{prefix}{i + 1}.cnf" for i in range(start, rng)]


def run_small_experiment(
    input_file: str,
    output,
    DIMACS: bool = False,
    watched_lits: bool = False,
    score_h: str = None
) -> tuple[bool, float, int, int, int, int]:
    """Run SAT solver experiment on one input file."""
    if DIMACS:
        clauses, variables, n_vars, n_cl = read_DIMACS(input_file)
    else:
        decoder = DIMACS_decoder(input_file)
        decoder.get_var_mapping()
        clauses = decoder.get_DIMACS()
        variables = decoder.var2dimacs_map.values()
        n_vars, n_cl = len(variables), len(clauses)

    # Choose decision heuristic
    score = None
    vsids = None
    if score_h is None:
        heuristic_fn = choose_random
    else:
        heuristic_fn = choose_literal
        if score_h == "jw":
            score = JW_heuristic
        elif score_h == "lc":
            score = lit_counts_h

        elif score_h == "vsids":
            vsids = VSIDs(n_vars)
            heuristic_fn = vsids.pick_literal
            
    # Instantiate solver
    solver = SAT_dpll(
        clauses,
        max(variables),
        choose_lit=heuristic_fn,
        score_h=score,
        VSIDS=vsids
    )

    # Choose unit propagation method
    propagate_fn = unit_propagate_w_watched_lits if watched_lits else unit_propagate_basic

    # Solve
    sat, _, cpu_time, n_decisions, n_up = solver.solve(propagate_fn)

    # Output results
    print(f"SAT result: {sat}", file=output)
    print(f"number of clauses: {n_cl}", file=output)
    print(f"number of variables: {n_vars}", file=output)
    print(f"Experiment with {input_file} lasted {cpu_time:.6f}", file=output)
    print(f"number of decisions: {n_decisions}", file=output)
    print(f"number of UP steps: {n_up}", file=output)
    print(f"{'-' * 45}", file=output)

    return sat, cpu_time, n_decisions, n_up, n_vars, n_cl


def parse_inputs(args: list[str],    path_prefix : str = "" # odkud voláme experiment
) -> tuple[list[str], bool, bool, str, bool]:
    """Parse and validate command-line arguments."""

    if len(args) != 5:
        print("Usage: experiments [output_file] [input_set] [w/a] [jw/lc/rand]")
        sys.exit(1)

    output_file = args[1]
    input_type = args[2]
    watched_lits = args[3] == "w"
    score_arg = args[4]

    score = {
        "jw": "jw",
        "lc": "lc",
        "rand": None,
        "vsids":"vsids"
    }.get(score_arg)

    if score_arg not in {"jw", "lc", "rand", "vsids"}:
        print("Error: heuristic must be one of [jw/lc/rand/vsids]")
        sys.exit(1)

    # Collect input files
    all_sat = True
    if input_type == "toy":
        file_names = [
            "..\\task1\\tsetin_inputs\\inputs\\nested_5.sat",
            "..\\task1\\tsetin_inputs\\inputs\\nested_8.sat",
            "..\\task1\\tsetin_inputs\\inputs\\toy_5.sat",
            "..\\task1\\tsetin_inputs\\inputs\\toy_50.sat",
            "..\\task1\\tsetin_inputs\\inputs\\toy_100.sat"
        ]
        is_dimacs = False
    elif input_type == "ais":
        pref = "" if path_prefix == "" else path_prefix + "\\"
        file_names = collect_files_ais(pref)
        is_dimacs = True
    elif input_type == "PHOLE":
        file_names = collect_files( path_prefix + "\\inputs\\pigeon-hole\\hole", 10, 6)
        is_dimacs = True
        all_sat = False
    else:
        prefix_map = {
            "utf20":  path_prefix + "\\inputs\\utf20\\uf20-0",
            "uuf50":  path_prefix + "\\inputs\\uuf50\\UUF50.218.1000\\uuf50-0",
            "uuf75":  path_prefix + "\\inputs\\uuf75\\UUF75.325.100\\uuf75-0",
            "uuf100": path_prefix + "\\inputs\\uuf100\\UUF100.430.1000\\uuf100-0",
            "utf50":  path_prefix + "\\inputs\\utf50\\uf50-0",
            "utf75":  path_prefix + "\\inputs\\utf75\\ai\\hoos\\Shortcuts\\UF75.325.100\\uf75-0",
            "utf100": path_prefix + "\\inputs\\utf100\\uf100-0",
            "uuf753": path_prefix + "\\inputs\\uuf753\\UUF175.753.100\\uuf175-0",
            "flat30": path_prefix + "\\inputs\\flat30\\flat30-",
            "flat50": path_prefix + "\\inputs\\flat50\\flat50-",
            "flat75": path_prefix + "\\inputs\\flat75\\ai\\hoos\\Research\\SAT\\GenGCP\\Flat75-180\\flat75-",
            "flat125":path_prefix + "\\inputs\\flat125\\ai\\hoos\\Research\\SAT\\GenGCP\\Flat125-301\\flat125-",
            "flat150":path_prefix + "\\inputs\\flat150\\ai\\hoos\\Research\\SAT\\GenGCP\\Flat150-360\\flat150-",
            "flat175":path_prefix + "\\inputs\\flat175\\ai\\hoos\\Research\\SAT\\GenGCP\\Flat175-417\\flat175-",
        }
        prefix = prefix_map.get(input_type)
        if not prefix:
            print(f"Unknown input type: {input_type}")
            sys.exit(1)
        file_names = collect_files(prefix, 100)
        is_dimacs = True
        all_sat = "uuf" not in input_type.lower()

    return file_names, is_dimacs, watched_lits, score, all_sat, output_file


if __name__ == "__main__":
    file_names, is_dimacs, watched_lits, score_h, all_sat, output_file = parse_inputs(sys.argv)

    total_time = total_n_dec = total_n_up = 0
    last_n_vars = last_n_cl = 0

    with open(output_file, "w") as f:
        for file_path in file_names:
            sat, t, n_dec, n_up, n_vars, n_cl = run_small_experiment(
                file_path, f, is_dimacs, watched_lits, score_h
            )
            total_time += t
            total_n_dec += n_dec
            total_n_up += n_up
            last_n_vars, last_n_cl = n_vars, n_cl
            assert sat == all_sat, f"{file_path} failed expected SAT={all_sat}"
        #    print(file_path + " DONE")

    avg_time = total_time / len(file_names)
    avg_dec = total_n_dec / len(file_names)
    avg_up = total_n_up / len(file_names)

    print("\n========== SUMMARY ==========")
    print(f"Number of variables         = {last_n_vars}")
    print(f"Number of clauses           = {last_n_cl}")
    print(f"Average CPU time            = {avg_time:.6f}")
    print(f"Average number of decisions = {avg_dec}")
    print(f"Average number of U-P steps = {avg_up}")
    print("DONE")
