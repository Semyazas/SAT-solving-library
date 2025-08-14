from collections import defaultdict
import time
import sys
from DIMACS_reader import read_DIMACS
from task1.DIMACS_encoding import DIMACS_decoder
from propagate.unit_propagate_watched_literals import unit_propagate_w_watched_lits
from decision_heuristics.choose_literal.choose_best_score import choose_literal
from decision_heuristics.precompute_score.lit_counts_h import lit_counts_h
import os
class SAT_dpll:
    """
    Class that implements SAT solver using dpll algorithm.
    If we call this file, it will use watched literals and literal counts 
    heuristic as default.
    """
    def __init__(self, clauses, nvars,choose_lit ,score_h = None, VSIDS = None):
        self.clauses = clauses
        self.nvars = nvars
        self.assign = [None for _ in range(nvars+1)]   # 1-indexed
        self.trail = []                     # stack of assigned literals
        self.num_decisions = 0
        self.steps_up = 0
        self.choose_lit = choose_lit

        self.adjacency_dict = defaultdict(list)
        self.clause_to_Wliterals = defaultdict(list)
        self.literal_to_clauses = defaultdict(set)
        self.score = None
        self.vsids = VSIDS
        # Precompute literal occurrences for fast heuristic
        if score_h != None:
            self.score = score_h(
                clauses = clauses,
                variables = [i for i in range(1,nvars+1)]
            )
        for clause in clauses:
            for lit in clause:
                self.adjacency_dict[lit].append(clause)

        self.begin_watched_literals()

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
    
    def begin_watched_literals(self) -> None:
        for  cl_idx,clause in enumerate(self.clauses):
            self.clause_to_Wliterals[cl_idx] = [clause[0]]
            self.literal_to_clauses[clause[0]].add(cl_idx)
            if len(clause) >=2:
                self.clause_to_Wliterals[cl_idx].append(clause[1])
                self.literal_to_clauses[clause[1]].add(cl_idx)


    def dpll(self,literal : int, propagate ) -> bool:
     #   print("rekurzuju")
        falsified_lit = literal if literal == None else -literal
        ok , steps_it = propagate(
            changed_literal = falsified_lit,
            adjacency_dict = self.adjacency_dict,
            clauses = self.clauses,
            value = self.value,
            enqueue = self.enqueue,
            assign = self.assign,
            clause_to_Wliterals = self.clause_to_Wliterals,
            literal_to_clauses = self.literal_to_clauses,
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
        if self.dpll(lit,propagate):
            return True
        self.backtrack(trail_len)

        self.enqueue(-lit)
        if self.dpll(-lit,propagate):
            return True
        self.backtrack(trail_len)
        return False

    def solve(self, propagete ):
        start = time.perf_counter()
        sat = self.dpll(None, propagete)
        end = time.perf_counter()
        model = {i: self.assign[i] for i in range(1, self.nvars+1)}
        return sat, model, end-start, self.num_decisions, self.steps_up

# TODO: debug -s variant
if __name__ == "__main__":
    clauses, variables = [], []
    dimacs = True
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    if len(sys.argv) == 3:
        filepath = os.path.join(BASE_DIR, sys.argv[2])
        if sys.argv[1] == "-d":
            clauses, variables,_,_ = read_DIMACS(filepath)
        elif sys.argv[1] == "-s":
            D_decoder = DIMACS_decoder(filepath)
            D_decoder.get_var_mapping()
            clauses = D_decoder.get_DIMACS()
            variables = list(D_decoder.var2dimacs_map.values())
            dimacs = False

    solver = SAT_dpll(
        clauses,
        max(variables),
        choose_lit=choose_literal,
        score_h=lit_counts_h,
        VSIDS=None
    )
    solved, model, t, n_dec, n_up = solver.solve(unit_propagate_w_watched_lits)

    print("SAT:", solved)
    if model:
        if dimacs:
            vals = sorted(model.keys())
            for var in vals:
                print(var if model[var] else -var)
        else:
            vals = sorted(model.keys())
            for var in vals:
                print(D_decoder.dmacs2var_map[var], ": ", model[var])

    print("time:", t)
    print("decisions:", n_dec)
    print("unit propagations:", n_up)