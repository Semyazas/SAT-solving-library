import argparse
import time
from pysat.formula import CNF
from pysat.solvers import Minisat22
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')))

from task23.experiments import collect_files, collect_files_ais
from backbone import BackboneFinder
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

    with open(args.output_file,"w") as f:
        for file in file_names:
            cnf = CNF(from_file=file)
            
            bb = BackboneFinder(cnf)
            backbones, stats = bb.compute_backbones()
            print("\nFile: ", file, file=f)
            print("# Stats",file=f)
            for k, v in stats.items():
                print(f"{k}: {v}",file=f)
