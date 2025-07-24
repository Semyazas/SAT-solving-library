import time
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dpll import SAT_dpll
from DIMACS_reader import read_DIMACS
from task1.DIMACS_encoding import DIMACS_decoder

def run_small_experiment(
    input_file : str, f) -> None:
    tic = time.perf_counter()

    clauses, variables = [],[]
    D_decoder = DIMACS_decoder(input_file)
    D_decoder.get_var_mapping()
    clauses, variables =  D_decoder.get_DIMACS(), D_decoder.var2dimacs_map.values()
    solver = SAT_dpll(clauses,variables)
    solved = solver.dpll(clauses, {}) != None
    toc = time.perf_counter()

    print(f"SAT result: {solved}", file = f)
    print(f"Experiment with {input_file} lasted {toc - tic}", file = f)
    print(f"---------------------------------------------", file = f)

if __name__ == "__main__":
    file_names = ["..\\task1\\tsetin_inputs\\inputs\\nested_5.sat",
                  "..\\task1\\tsetin_inputs\\inputs\\nested_8.sat",
                  "..\\task1\\tsetin_inputs\\inputs\\toy_5.sat",
                  "..\\task1\\tsetin_inputs\\inputs\\toy_50.sat",
                  "..\\task1\\tsetin_inputs\\inputs\\toy_100.sat"                  
    ]

    with open(sys.argv[1],"w") as f:
        for file_name in file_names:
            run_small_experiment(file_name,f)