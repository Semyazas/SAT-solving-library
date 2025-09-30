import time
from parser import read_DIMACS, DIMACS_decoder
from solver.propagate import Unit_propagation_watched_literals
from solver.dpll_solver.decision_heuristics import choose_literal, lit_counts_h
import argparse
class SAT_dpll:
    """
    Class that implements SAT solver using dpll algorithm.
    If we call this file, it will use watched literals and literal counts 
    heuristic as default.
    """
    def __init__(self,
            clauses, 
            nvars,
            choose_lit,
            assign, 
            score_h = None, 
            VSIDS = None, 
            propagation = None):
        self.clauses = clauses
        self.nvars = nvars
        self.assign = assign   # 1-indexed
        self.trail = []                     # stack of assigned literals
        self.num_decisions = 0
        self.steps_up = 0
        self.choose_lit = choose_lit
        self.propagation = propagation

        self.score = None
        self.vsids = VSIDS
        # Precompute literal occurrences for fast heuristic
        if score_h != None:
            self.score = score_h(
                clauses = clauses,
                variables = [i for i in range(1,nvars+1)]
            )

    def value(self, lit):
        """Return literal truth value under current assignment or None."""
        val = self.assign[abs(lit)]
        return val if lit > 0 else (not val if val is not None else None)

    def enqueue(self, lit : int) -> None:
        """Assign literal and push to trail."""
        self.assign[abs(lit)] = lit > 0
        self.trail.append(lit)

    def backtrack(self, old_len : int) -> None:
        """Undo assignments down to old_len of trail."""
        while len(self.trail) > old_len:
            lit = self.trail.pop()
            self.assign[abs(lit)] = None
    
    def dpll(self,literal : int) -> bool:
        falsified_lit = literal if literal == None else -literal
        ok , steps_it = self.propagation.propagate(
            changed_literal = falsified_lit,
            clauses = self.clauses,
            value = self.value,
            enqueue = self.enqueue,
            assign = self.assign,
            trail = self.trail,
            vsids = self.vsids
        )
        self.steps_up+= steps_it
        if not ok:
            return False
        lit = self.choose_lit(
            assign = self.assign,
            score = self.score,
            vars = self.nvars)
        
        if lit is None:
            return True  # all variables assigned, SAT

        self.num_decisions += 1
        trail_len = len(self.trail)

        self.enqueue(lit)
        if self.dpll(lit):
            return True
        self.backtrack(trail_len)

        self.enqueue(-lit)
        if self.dpll(-lit):
            return True
        self.backtrack(trail_len)
        return False

    def solve(self):
        start = time.perf_counter()
        sat = self.dpll(None)
        end = time.perf_counter()
        model = {i: self.assign[i] for i in range(1, self.nvars+1)}
        return sat, model, end-start, self.num_decisions, self.steps_up

def main():
    parser = argparse.ArgumentParser(
        description="SAT solver using DPLL with DIMACS or solver input."
    )
    parser.add_argument(
        "mode",
        choices=["d", "s"],
        help="Choose input mode: -d for raw DIMACS file, -s for preprocessed solver input."
    )
    parser.add_argument(
        "filepath",
        help="Path to the input file."
    )
    args = parser.parse_args()
    clauses, variables = [], []
    dimacs = True

    if args.mode == "d":
        clauses, variables, _, _ = read_DIMACS(args.filepath)
    elif args.mode == "s":
        D_decoder = DIMACS_decoder(args.filepath)
        D_decoder.get_var_mapping()
        clauses = D_decoder.get_DIMACS()
        variables = list(D_decoder.var2dimacs_map.values())
        dimacs = False

    assign = [None] * (max(variables) + 1)  # 1-indexed
    solver = SAT_dpll(
        clauses,
        max(variables),
        choose_lit=choose_literal,
        score_h=lit_counts_h,
        VSIDS=None,
        assign=assign,
        propagation=Unit_propagation_watched_literals(
            clauses=clauses,
            enqueue=lambda x: solver.enqueue(x),
            assignment=assign,
            value=lambda x: solver.value(x)
        )
    )
    solved, model, t, n_dec, n_up = solver.solve()

    print("SAT:", solved)
    if model:
        vals = sorted(model.keys())
        if dimacs:
            for var in vals:
                print(var if model[var] else -var)
        else:
            for var in vals:
                print(D_decoder.dmacs2var_map[var], ": ", model[var])

    print("time:", t)
    print("decisions:", n_dec)
    print("unit propagations:", n_up)

if __name__ == "__main__":
    main()
