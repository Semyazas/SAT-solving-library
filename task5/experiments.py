import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from task23.experiments import parse_inputs

from look_ahead import SAT_lookAhead
from DIMACS_reader import read_DIMACS
from task1.DIMACS_encoding import DIMACS_decoder
from look_ahead_parts.preselection.preselect import pre_select
from difference_heuristics.wbh import WBH_heuristic
from difference_heuristics.crh import CRH_heuristics
from propagate.propagate_binary import Binary_propagation
def run_small_experiment(
    input_file: str,
    output,
    DIMACS: bool = False,
    watched_lits: bool = False,
    score_h: str = None,
    threshold = 1e1000000
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

    # Choose difference heuristic
    h = None
    if score_h == "jw":
        h = WBH_heuristic
    elif score_h == "lc":
        h = CRH_heuristics

    prop = None
    if watched_lits:
        prop = Binary_propagation
    # Instantiate solver
    solver = SAT_lookAhead(
        clauses,
        max(variables),
        heuristic=h,
        propagation=prop,
        preselect=pre_select,
        threshold_mod=threshold
    )
    # Choose unit propagation method
    sat, _, cpu_time, n_decisions, n_up = solver.solve(prop.propagate_with_implications)

    # Output results
    print(f"SAT result: {sat}", file=output)
    print(f"number of clauses: {n_cl}", file=output)
    print(f"number of variables: {n_vars}", file=output)
    print(f"Experiment with {input_file} lasted {cpu_time:.6f}", file=output)
    print(f"number of decisions: {n_decisions}", file=output)
    print(f"number of UP steps: {n_up}", file=output)
    print(f"{'-' * 45}", file=output)

    return sat, cpu_time, n_decisions, n_up, n_vars, n_cl

if __name__ == "__main__":
    file_names, is_dimacs, watched_lits, score_h,\
    all_sat, output_file = parse_inputs(sys.argv[:5],path_prefix="..\\task23")
    threshold = 1e1000
    if len(sys.argv) == 6:
        threshold = float(sys.argv[5])
    total_time = total_n_dec = total_n_up = 0
    last_n_vars = last_n_cl = 0

    with open(output_file, "w") as f:
        for file_path in file_names:
            sat, t, n_dec, n_up, n_vars, n_cl = run_small_experiment(
                file_path, f, is_dimacs, watched_lits, score_h,threshold
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