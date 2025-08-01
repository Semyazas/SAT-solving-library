from collections import defaultdict
import time
import sys
from DIMACS_reader import read_DIMACS
from task1.DIMACS_encoding import DIMACS_decoder

class SAT_dpll:
    def __init__(self, clauses, nvars):
        self.clauses = clauses
        self.nvars = nvars
        self.assign = [None for _ in range(nvars+1)]   # 1-indexed
        self.trail = []                     # stack of assigned literals
        self.num_decisions = 0
        self.steps_up = 0
        self.adjacency_dict = defaultdict(list)

        # Precompute literal occurrences for fast heuristic
        self.lit_counts = defaultdict(int)
        for clause in clauses:
            for lit in clause:
                self.lit_counts[lit] += 1
                self.adjacency_dict[lit].append(clause)

    def value(self, lit):
        """Return literal truth value under current assignment or None."""
        val = self.assign[abs(lit)]
        return val if lit > 0 else (not val if val is not None else None)

    def enqueue(self, lit):
        """Assign literal and push to trail."""
        self.assign[abs(lit)] = lit > 0
        self.trail.append(lit)

    def backtrack(self, old_len):
        """Undo assignments down to old_len of trail."""
        while len(self.trail) > old_len:
            lit = self.trail.pop()
            self.assign[abs(lit)] = None

    def unit_propagate(self, changed_literal : int = None) -> bool:
        """
        Standard unit propagation scanning all clauses.
        Returns True if consistent, False if conflict.
        """
        to_check = []
        if changed_literal != None:
            to_check = [changed_literal]
        while to_check:
            checked = None
            iterate_through = self.clauses
            if to_check != []:
                checked = to_check.pop()
                iterate_through = self.adjacency_dict[checked]
            for clause in iterate_through:
                # Check clause under current assignment
                satisfied = False
                unassigned = []
                for lit in clause:
                    val = self.value(lit)
                    if val is True:
                        satisfied = True
                        break
                    if val is None:
                        unassigned.append(lit)

                if satisfied:
                    continue
                if len(unassigned) == 0:
                    return False  # conflict
                if len(unassigned) == 1:
                    # Unit literal
                    lit = unassigned[0]
                    if self.value(lit) is False:
                        return False
                    if self.value(lit) is None:
                        self.enqueue(lit)
                        self.steps_up += 1
                        to_check.append(-lit)
                
        return True

    def choose_literal(self):
        """Pick literal with maximum occurrence among unassigned vars."""
        best_lit = None
        best_count = -1
        for var in range(1, self.nvars+1):
            if self.assign[var] is None:
                cnt_pos = self.lit_counts[var]
                cnt_neg = self.lit_counts[-var]
                if cnt_pos >= cnt_neg:
                    lit = var
                    cnt = cnt_pos
                else:
                    lit = -var
                    cnt = cnt_neg
                if cnt > best_count:
                    best_count = cnt
                    best_lit = lit
        return best_lit

    def dpll(self,literal):
        a = literal if literal == None else -literal
        if not self.unit_propagate(a):
            return False
        lit = self.choose_literal()
        if lit is None:
            return True  # all variables assigned, SAT

        self.num_decisions += 1
        trail_len = len(self.trail)

        # Try True
        self.enqueue(lit)
        if self.dpll(lit):
            return True
        self.backtrack(trail_len)

        # Try False
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


if __name__ == "__main__":
    clauses, variables = [], []
    dimacs = True
    if len(sys.argv) == 3:
        if sys.argv[1] == "-d":
            clauses, variables = read_DIMACS(sys.argv[2])
        elif sys.argv[1] == "-s":
            D_decoder = DIMACS_decoder(sys.argv[2])
            D_decoder.get_var_mapping()
            clauses = D_decoder.get_DIMACS()
            variables = list(D_decoder.var2dimacs_map.values())
            dimacs = False

    solver = SAT_dpll(clauses, max(variables))
    solved, model, t, n_dec, n_up = solver.solve()

    print("SAT:", solved)
    if model:
        vals = sorted(model.keys())
        for var in vals:
            print(var if model[var] else -var)
    print("time:", t)
    print("decisions:", n_dec)
    print("unit propagations:", n_up)