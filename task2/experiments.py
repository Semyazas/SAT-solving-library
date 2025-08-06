import time
import sys
import os

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

def collect_files_ais() -> list[str]:
    file_names = [
        "inputs\\ais\\ais"  + str(i) + ".cnf" for i in range(6,13,2)
    ]
    return file_names
def collect_files(prefix : str, rng: int, start = 0) -> list[str]:
    file_names = [
        prefix + str(i+1) + ".cnf" for i in range(start,rng)
    ]
   # print(file_names)
    return file_names

def run_small_experiment(
        input_file : str,
        f, 
        DIMACS  : bool = False,
        watched_l : bool = False,
        score_h : str= None
        ) -> tuple[bool, int]:
    
    clauses, variables = [],[]
    n_vars,n_cl = 0,0

    if not DIMACS:
        D_decoder = DIMACS_decoder(input_file)
        D_decoder.get_var_mapping()
        clauses, variables =  D_decoder.get_DIMACS(), D_decoder.var2dimacs_map.values()
    else:
        clauses, variables, n_vars, n_cl =  read_DIMACS(input_file)

   # print("vars: ", variables)
    solver = None
    if score_h is None:
        solver = SAT_dpll(
            clauses,
            max(variables),
            choose_lit = choose_random
        )
    else:
        score_heur = JW_heuristic if score_h == "jw" else lit_counts_h
        solver = SAT_dpll(
            clauses,
            max(variables),
            choose_lit = choose_literal,
            score_h=score_heur
        )

    propagate = unit_propagate_w_watched_lits if watched_l else unit_propagate_basic

    solved, _, cpu_time, n_dec, n_up   = solver.solve(propagate)
    print(f"SAT result: {solved}", file = f)
    print(f"number of clauses: ", n_cl ,file=f)
    print(f"number of variables: ", n_vars,file=f)
    print(f"Experiment with {input_file} lasted {cpu_time}", file = f)
    print(f"number of decisions: ", n_dec, file=f)
    print(f"number of UP steps: ", n_up, file=f)
    print(f"---------------------------------------------", file = f)

    return solved, cpu_time, n_dec, n_up, n_vars, n_cl

if __name__ == "__main__":
    file_names = []
    is_dimacs = False
    all_sat = False
    if  (len(sys.argv) == 5):
        if sys.argv[2] == "toy":
            file_names = ["..\\task1\\tsetin_inputs\\inputs\\nested_5.sat",
                        "..\\task1\\tsetin_inputs\\inputs\\nested_8.sat",
                        "..\\task1\\tsetin_inputs\\inputs\\toy_5.sat",
                        "..\\task1\\tsetin_inputs\\inputs\\toy_50.sat",
                        "..\\task1\\tsetin_inputs\\inputs\\toy_100.sat"                  
            ]
        elif sys.argv[2] == "ais":
            file_names = collect_files_ais()
            all_sat = True
        elif sys.argv[2] == "utf20":
            file_names = collect_files("inputs\\utf20\\uf20-0",100)
            all_sat = True

        elif sys.argv[2] == "utf635":
            file_names = collect_files("inputs\\uf645\\ai\\hoos\\Research\\SAT\\Formulae\\UF150.645.100\\uf150-0",100)
            all_sat = True
        elif sys.argv[2] == "uuf753":
            file_names = collect_files("inputs\\uuf753\\UUF175.753.100\\uuf175-0",100)
            print(file_names[0])
            print("funguju")
            all_sat = False
        elif sys.argv[2] == "uuf50":
            file_names = collect_files("inputs\\uuf50\\UUF50.218.1000\\uuf50-0",100)
            all_sat = False

        elif sys.argv[2] == "cbs_b10":
            file_names = collect_files("inputs\\cbs_b10\\UUF50.218.1000\\uuf50-0",100)
            all_sat = True

        elif sys.argv[2] == "flat30":
            file_names = collect_files("inputs\\flat30\\flat30-",100)

            all_sat = True
        elif sys.argv[2] == "flat50":
            file_names = collect_files("inputs\\flat50\\flat50-",1000)
            all_sat = True
        
        elif sys.argv[2] == "flat75":
            file_names = collect_files("inputs\\flat75\\ai\\hoos\\Research\\SAT\\GenGCP\\Flat75-180\\flat75-",100)
            all_sat= True
        elif sys.argv[2] == "flat125":
            file_names = collect_files("inputs\\flat125\\ai\\hoos\\Research\\SAT\\GenGCP\\Flat125-301\\flat125-",100)
            all_sat= True
        elif sys.argv[2] == "flat150":
            file_names = collect_files("inputs\\flat150\\ai\\hoos\\Research\\SAT\\GenGCP\\Flat150-360\\flat150-",100)
            all_sat= True
        elif sys.argv[2] == "flat175":
            file_names = collect_files("inputs\\flat175\\ai\\hoos\\Research\\SAT\\GenGCP\\Flat175-417\\flat175-",100)
            all_sat= True
        
        elif sys.argv[2] == "PHOLE":
            file_names = collect_files("inputs\\pigeon-hole\\hole",10, 6)
            all_sat= False
        is_dimacs = True
    else:
        print("Something wrong, input format is: experiments [output_file] [input_directory/toy] [w/a] [jw/lc/rand]")
        exit(0)

    total_time = 0
    total_n_dec = 0
    total_n_UP = 0
    n_cl = 0
    n_vars = 0
  #  print(file_names)
    watched_l = True if sys.argv[3] == "w" else False
    print(watched_l)

    score_h = None
    if sys.argv[4] == "jw":
        score_h = JW_heuristic
    elif sys.argv[4] == "lc":
        score_h = lit_counts_h    

    with open(sys.argv[1],"w") as file:
        for file_name in file_names:       
            sat , t, n_dec, n_up, n_vars, n_cl = run_small_experiment(
                file_name,
                file,   
                is_dimacs, 
                watched_l,
                score_h
            )
            total_time += t
            total_n_dec += n_dec
            total_n_UP += n_up
            assert(sat == all_sat)
            print(file_name + " DONE")
            
    average_time = total_time/len(file_names)
    average_n_UP = total_n_UP / len(file_names)
    average_n_dec = total_n_dec / len(file_names)

    print("number of variables         = ", n_vars)
    print("number of clauses           = ", n_cl)
    print("average cpu time            = ",average_time)
    print("average number of decisions = ",average_n_dec)
    print("average number of U-P steps = ",average_n_UP)

    print("DONE")