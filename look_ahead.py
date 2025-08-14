from collections import defaultdict
import time

class SAT_lookAhead:
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

    def diff(clause) -> float:
        raise NotImplementedError
    
    def mix_diff(clause) -> float:
        raise NotImplementedError

    def look_ahead(clauses):
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
    def solve_with_look_ahead(self,propagate, clauses) -> bool:
     #   print("rekurzuju")
        if self.clauses == []: # TODO: debug 
            return True
        
        self.clauses, dec_variable  = self.look_ahead(self.clauses)

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