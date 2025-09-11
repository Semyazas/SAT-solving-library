
from pysat.formula import CNF, IDPool
from pysat.solvers import Minisat22
import argparse
import time
import sys
import os
import matplotlib.pyplot as plt
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')))

from task23.experiments import collect_files, collect_files_ais
from solution import iterative_method, non_iterative_method, iterative_method_old

def parse_inputs(input_type, path_prefix):
    if input_type == "ais":
        pref = "" if path_prefix == "" else path_prefix + "\\"
        file_names = collect_files_ais(pref)
    elif input_type == "PHOLE":
        file_names = collect_files( path_prefix + "\\inputs\\pigeon-hole\\hole", 10, 6)
    else:
        prefix_map = {
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
            exit(1)
        file_names = collect_files(prefix, 100)

    return file_names

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Running experiments on bacbone.")
    ap.add_argument("type", help="Input: ais, phole, flat[30/75/125]")
    ap.add_argument("output_file", help = "output file should be .txt")

    args = ap.parse_args()
    path_prefix="..\\..\\task23"
    file_names = parse_inputs(args.type,path_prefix)
    
    number_of_equivalences = 0 # this should be > 1

    times_it_old = []
    times_it     = []
    times_not_it = []

    implication_matrix = [
        [False for _ in range(len(file_names))] for _ in range(len(file_names))
    ]
    x = []
    with open(args.output_file,"w") as f:
        for i,file in enumerate(file_names):
            print(i)
            cnf = CNF(from_file=file)
            x.append(cnf.nv)
            methods_times = [
                (iterative_method, times_it),
                (iterative_method_old,  times_it_old),
                (non_iterative_method, times_not_it)
            ]
            for method,  tim in methods_times:
                time_tot = 0
                N = 0
                for j in range(len(file_names)):
                    N +=1
                    cnf2 = CNF(from_file=file_names[j])
                    stats_left_to_right = method(cnf,cnf2)
                    implication_matrix[i][j] = stats_left_to_right["implied"]

                    assert(stats_left_to_right["implied"] \
                            == stats_left_to_right["implied"])
                    time_tot += stats_left_to_right["time"]
                tim.append(time_tot / N)
        number_of_equivalences = sum(
            sum(1 for j in range(len(implication_matrix)) if implication_matrix[i][j] and implication_matrix[j][i])
                for i in range(len(implication_matrix))
        ) 
        print("average_time_iterative_new: ", sum(times_it)/len(times_it),file=f)
        print("average_time_iterative_old: ", sum(times_it_old)/len(times_it),file=f)
        print("average_time_non_iterative: ", sum(times_not_it)/len(times_it),file=f)  
        print("number of equivalences: ", number_of_equivalences,file=f)             
        
        plt.figure(figsize=(8,6))

        plt.plot(x,times_it, marker="o", label="iterative new")
        plt.plot(x,times_not_it, marker="x", label="not iterative")
        plt.plot(x,times_it_old, marker = "o", label = "times iterative old")
        plt.xlabel("number of vars of (CNF1)")
        plt.ylabel("Average time for when CNF 1 is on the left (Time (s))")
        plt.yscale("log")
        plt.title("Non iterative vs iterative method comparison")
        plt.legend(title="Solver")
        plt.grid(True)

        plt.savefig(f"graph_{args.type}.png")
        plt.show()