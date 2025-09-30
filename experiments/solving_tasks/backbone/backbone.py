#!/usr/bin/env python3
import argparse
import time
from pysat.formula import CNF
from pysat.solvers import Minisat22
def normalize_model(model):
    seen = {}
    for lit in model:
        v = abs(lit)
        if v not in seen:
            seen[v] = 1 if lit > 0 else -1
    return set(v if sign > 0 else -v for v, sign in seen.items())

def literal_of_var_from_model(v, model_set):
    """Return v (positive) if v is true in model_set, else -v."""
    return v if v in model_set else -v

class BackboneFinder:
    def __init__(self, cnf: CNF):
        self.cnf = cnf
        self.batch_size = 64
        self.calls = 0
        self.solver = Minisat22(use_timer = True)
        self.initail_model = None
        for cl in cnf.clauses:
            self.solver.add_clause(cl)
    def reset_solver(self):
        self.solver = Minisat22(use_timer = True)
        for cl in self.cnf.clauses:
            self.solver.add_clause(cl)

    def batch_probe(self, batch, confirmed_backbones, candidates):
        """
        Try to falsify a batch of candidate literals at once:
          - If SAT: intersect candidates with new model (shrinks candidates).
          - If UNSAT: recurse (split batch) to isolate singleton backbones.
        """
        if not batch:
            return

        # Assume negations of the batch
        assumps = [-l for l in batch]
        self.calls += 1
        self.reset_solver
        if self.solver.solve(assumptions=assumps):
            model_set = normalize_model(self.solver.get_model())
            # shrink candidates to literals that stay the same across seen models
            new_candidates = set(
                literal_of_var_from_model(abs(l), model_set)
                for l in candidates
            )
            candidates.intersection_update(new_candidates)
            return  # no backbones found in this SAT branch
        else:
            # UNSAT under joint assumptions; if batch is singleton -> backbone
            if len(batch) == 1:
                confirmed_backbones.add(batch[0])
                return
            # Split & recurse (divide & conquer)
            mid = len(batch) // 2
            left = batch[:mid]
            right = batch[mid:]
            self.batch_probe(left, confirmed_backbones, candidates)
            self.batch_probe(right, confirmed_backbones, candidates)

    def compute_backbones(self):
        t0 = time.perf_counter()
        sat = self.solver.solve()
        print(sat)
        model = self.solver.get_model()
        self.initail_model = model
       # print(model is None)
        if model is None:
            t1 = time.perf_counter()
            return set(), {
                "sat": False,
                "sat_calls": self.calls,
                "time_sec": t1 - t0,
                "notes": "Formula is UNSAT; backbones are undefined."
            }
        candidates = normalize_model(model)  # one literal per variable
        confirmed = set()

        while True:
            frontier = list(candidates - confirmed)
            if not frontier:
                break
            batch = frontier[: self.batch_size]
            self.batch_probe(batch, confirmed, candidates)

            if set(frontier) == set(candidates - confirmed) and len(batch) == 1:
                # last step did nothing; break to final verification
                break

        # Final exact check on any remaining unconfirmed candidates
        remaining = list(candidates - confirmed)
        for lit in remaining:
            self.calls += 1
            self.reset_solver()            
            if  self.solver.solve(assumptions=[-lit]):  # SAT -> not a backbone
                # could intersect candidates again to be safe:
                model_set = normalize_model(self.solver.get_model())
                candidates.intersection_update(
                    set(literal_of_var_from_model(abs(l), model_set) for l in candidates)
                )
            else:
                confirmed.add(lit)

        t1 = time.perf_counter()
        return confirmed, {
            "sat": True,
            "sat_calls": self.calls,
            "time_sec": t1 - t0,
            "vars": self.cnf.nv,
            "clauses": len(self.cnf.clauses),
            "confirmed_backbones": len(confirmed),
        }

# ---------- CLI ----------
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Backbone finder using a SAT solver (PySAT).")
    ap.add_argument("cnf", help="Input CNF in DIMACS format")
    args = ap.parse_args()

    cnf = CNF(from_file=args.cnf)
    bb = BackboneFinder(cnf)
    backbones, stats = bb.compute_backbones()

    if not stats["sat"]:
        print("UNSAT formula — backbones undefined.")
        print(f"SAT calls: {stats['sat_calls']} | time: {stats['time_sec']:.4f}s")
        exit()

    print("\n# Stats")
    for k, v in stats.items():
        print(f"{k}: {v}")
    
    model = bb.initail_model   # or store the model after first solve
    blocking = [-lit for lit in model]

    s2 = Minisat22(bootstrap_with=cnf.clauses)  # use cnf.clauses, not cnf directly
    s2.add_clause(blocking)
    print('is there a second model?', s2.solve())