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

        self.clause_to_Wliterals = defaultdict(list)
        self.literal_to_clauses = defaultdict(set)

        # Precompute literal occurrences for fast heuristic
        self.lit_counts = defaultdict(int)
        for clause in clauses:
            for lit in clause:
                self.lit_counts[lit] += 1

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


    def unit_propagate_w_watched_lits(self, changed_literal=None):
        to_check = [changed_literal] if changed_literal is not None else []
        assign = self.assign
        clauses = self.clauses
        cl_wlits = self.clause_to_Wliterals
        lit_to_cls = self.literal_to_clauses

        while to_check:
            checked = to_check.pop()
            for cl_idx in list(lit_to_cls[checked]):  # iterate over copy
                w1, w2 = cl_wlits[cl_idx]
                other = w1 if w1 != checked else w2

                # check if clause is already satisfied
                val = assign[abs(other)]
                if (val and other > 0) or (val is False and other < 0):
                    continue

                # try to move watched literal
                moved = False
                for lit in clauses[cl_idx]:
                    if lit != other:
                        v = assign[abs(lit)]
                        if v is None or (v and lit > 0) or (v is False and lit < 0):
                            cl_wlits[cl_idx] = [other, lit]
                            lit_to_cls[lit].add(cl_idx)
                            lit_to_cls[checked].discard(cl_idx)
                            moved = True
                            break

                if not moved:
                    if val is False or (val is True and other < 0):
                        return False  # conflict
                    if val is None:
                        self.enqueue(other)
                        self.steps_up += 1
                        to_check.append(-other)
        return True

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
     #   print("rekurzuju")
        a = literal if literal == None else -literal
        ok = self.unit_propagate_w_watched_lits(a)
        if not ok:
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