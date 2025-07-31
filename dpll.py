from collections import defaultdict
import time
import sys
from DIMACS_reader import read_DIMACS

class SAT_dpll:
    def __init__(self, clauses, nvars):
        self.clauses = clauses
        self.nvars = nvars
        print(nvars)
        self.assign = [None for _ in range(nvars+1)]   # 1-indexed
        self.trail = []                     # stack of assigned literals
        self.num_decisions = 0
        self.steps_up = 0
        self.adjacency_dict = {}

        # Precompute literal occurrences for fast heuristic
        self.lit_counts = defaultdict(int)
        for clause in clauses:
            for lit in clause:
                self.lit_counts[lit] += 1

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

    def unit_propagate(self, changed_literal : int) -> bool:
        """
        Standard unit propagation scanning all clauses.
        Returns True if consistent, False if conflict.
        """
        changed = True
        to_check = changed_literal
        while changed:
            changed = False
            for clause in self.clauses:
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
                        changed = True
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

    def dpll(self):
        if not self.unit_propagate():
            return False
        lit = self.choose_literal()
        if lit is None:
            return True  # all variables assigned, SAT

        self.num_decisions += 1
        trail_len = len(self.trail)

        # Try True
        self.enqueue(lit)
        if self.dpll():
            return True
        self.backtrack(trail_len)

        # Try False
        self.enqueue(-lit)
        if self.dpll():
            return True
        self.backtrack(trail_len)

        return False

    def solve(self):
        start = time.perf_counter()
        sat = self.dpll()
        end = time.perf_counter()
        model = {i: self.assign[i] for i in range(1, self.nvars+1)}
        return sat, model, end-start, self.num_decisions, self.steps_up


if __name__ == "__main__":
    clauses, variables = [], []
    if len(sys.argv) == 3 and sys.argv[1] == "-d":
        clauses, variables = read_DIMACS(sys.argv[2])
    print("vars: ", variables)
    solver = SAT_dpll(clauses, max(variables))
    sat, model, t, decs, ups = solver.solve()
    print("SAT:", sat)
    print("time:", t, "decisions:", decs, "UP steps:", ups)
