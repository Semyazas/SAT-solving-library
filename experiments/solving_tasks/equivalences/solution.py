from pysat.formula import CNF, IDPool
from pysat.solvers import Minisat22
import argparse
import time
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')))


def cnf_with_neg_alpha(F: CNF, Alpha: CNF) -> tuple[CNF, int]:
    """
    Retrn CNF encoding F and neg Alpha, using Tseitin.
    """
    maxvar = max(F.nv, *(abs(l) for cl in F.clauses for l in cl)) if F.clauses else F.nv
    pool = IDPool(start_from=maxvar + 1)  
    enc = CNF()

    for cl in F.clauses:
        enc.append(cl)

    neg_clause_vars = []
    for i, clause in enumerate(Alpha.clauses):
        nc_var = pool.id(f'negC_{i}') # introduce new variable
        neg_clause_vars.append(nc_var)

        for lit in clause:
            enc.append([-nc_var, -lit]) # if some lit holds, n_var has to hold, also if nc_var holds, some lit has to hold
        enc.append([nc_var] + clause)   # at at least some lit or nc_var hold
    f_alpha = pool.id('neg_alpha_root')

    if neg_clause_vars:
        enc.append([-f_alpha] + neg_clause_vars) # f_alpha or some new vars hold
        for v in neg_clause_vars:   
            enc.append([-v, f_alpha]) # at least some new variable holds or f_alpha hold
    else:
        pass
    enc.append([f_alpha])
    return enc, f_alpha

def non_iterative_method(F : CNF, Alpha : CNF)->dict:
    tic = time.perf_counter()

    enc, _ = cnf_with_neg_alpha(F,Alpha)
   # enc = F.clauses + Alpha.negate().clauses
    solver = Minisat22(use_timer=True)
    for cl in enc.clauses: solver.add_clause(cl)
    sat = solver.solve()
    toc = time.perf_counter()

    return {
        "implied" : not sat,
        "time": toc - tic
    } 
def iterative_method_old(F: CNF, Alpha : CNF)->tuple[bool,float]:
    tic = time.perf_counter()
    for clause in Alpha.clauses:
        solver = Minisat22(use_timer=True)
        for cl in F.clauses: solver.add_clause(cl)
        for lit in clause: solver.add_clause([-lit])
        sat = solver.solve()
        if sat: return {
        "implied" : False,
        "time": time.perf_counter() - tic
    } 
    toc = time.perf_counter()
    return {
        "implied" : True,
        "time": toc - tic
    } 
def iterative_method(F: CNF, Alpha: CNF) -> dict:
    tic = time.perf_counter()

    # initialize solver ONCE with base formula F
    with Minisat22(bootstrap_with=F.clauses, use_timer=True) as solver:
        for clause in Alpha.clauses:
            assumptions = [-lit for lit in clause]
            for assumption in assumptions:
                sat = solver.solve(assumptions=[assumption])
                if sat:
                    return {
                        "implied": False,
                        "time": time.perf_counter() - tic
                    }
    toc = time.perf_counter()
    return {
        "implied": True,
        "time": toc - tic
    }
if __name__ == "__main__":
    # we do implication from left to right
    ap = argparse.ArgumentParser(description="Running experiments on bacbone.")
    ap.add_argument("input_file1", help="left part of implication")
    ap.add_argument("input_file2", help="right part of implication")
    ap.add_argument("output_file", help = "output file should be .txt")
    ap.add_argument("solver", help="Which solver to use ?: [it,n]")

    args = ap.parse_args()

    with open(args.output_file, "w") as f:
        cnf1 = CNF(from_file=args.input_file1)
        cnf2 = CNF(from_file=args.input_file2)
        is_implied_left_to_right = None
        if args.solver == "it":
            is_implied_left_to_right = iterative_method
        elif args.solver == "n":
            is_implied_left_to_right = non_iterative_method

        print(f"x: {args.input_file1}",file=f)
        print(f"y: {args.input_file2}",file=f)
        l_to_r_implication = is_implied_left_to_right(cnf1,cnf2) 
        r_to_l_implication = is_implied_left_to_right(cnf2,cnf1)

        print("Average completion time: ", (l_to_r_implication["time"] \
            + r_to_l_implication["time"])/2,file = f)
        print("x -> y ?: ", l_to_r_implication["implied"],file = f)             
        print("x <- y ?: ", r_to_l_implication["implied"],file = f) 
        print("x <-> y ?: ", l_to_r_implication["implied"]\
            and r_to_l_implication["implied"] ,file = f)             
            


