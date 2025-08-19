from collections import defaultdict
import time
import sys
from DIMACS_reader import read_DIMACS
from task1.DIMACS_encoding import DIMACS_decoder
from propagate.propagate_binary import propagate_with_implications
from decision_heuristics.choose_literal.choose_best_score import choose_literal
from decision_heuristics.precompute_score.lit_counts_h import lit_counts_h
import os
"""
TODO: 
    1) push changes             DONE
    2) create heuristics        Partially DONE
    3) double literals          Huh ? 
    4) fancy data structure     In progress
"""
class SAT_lookAhead:
    def __init__(self,
            clauses, 
            nvars, 
            choose_lit,
            score_h = None, 
            VSIDS = None) -> None:
        self.clauses = clauses
        self.nvars = nvars
        # in __init__
        self.var_to_clauses = [[] for _ in range(self.nvars + 1)]
        self.cl_unassigned = [len(cl) for cl in self.clauses]  # incremental unassigned count
        self.mod_stack = []  # (kind, cl_idx, old_value) where kind in {"active","u"}
        # tiny cache for gamma_k
        self._gamma = {}
        def _gamma_k(k: int) -> float:
            if k in self._gamma: return self._gamma[k]
            if k == 2: v = 1.0
            elif k == 3: v = 0.2
            elif k == 4: v = 0.05
            elif k == 5: v = 0.01
            elif k == 6: v = 0.003
            else: v = 20.4514 * (0.218673 ** k)
            self._gamma[k] = v
            return v
        self.adjacency_dict = defaultdict(list)

        self._gamma_k = _gamma_k
        self.clause_active = [True for _ in range(len(clauses))]
        # build adjacency_dict (literal -> clause idx) AND var_to_clauses (var -> clause idx)
        for ci, clause in enumerate(self.clauses):
            for lit in clause:
                self.adjacency_dict[lit].append(ci)
                self.var_to_clauses[abs(lit)].append(ci)


        self.nvars = nvars
        self.assign = [None for _ in range(nvars+1)]   # 1-indexed
        self.trail = []                     # stack of assigned literals
        self.num_decisions = 0
        self.steps_up = 0
        self.choose_lit = choose_lit

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
        for i,clause in enumerate(clauses):
            for lit in clause:
                self.adjacency_dict[lit].append(i)

        self.begin_watched_literals()
        self.implications = defaultdict(list)  # lit -> [implied_lit, ...]

        for clause in self.clauses:
            if len(clause) == 2:
                a, b = clause
                # When 'a' is falsified, clause becomes unit 'b'
                # When 'b' is falsified, clause becomes unit 'a'
                self.implications[a].append(b)
                self.implications[b].append(a)


    def value(self, lit):
        """Return literal truth value under current assignment or None."""
        val = self.assign[abs(lit)]
        return val if lit > 0 else (not val if val is not None else None)

    def enqueue(self, lit: int) -> None:
        v = abs(lit)
        self.assign[v] = (lit > 0)
        self.trail.append(lit)

        # 1) mark satisfied clauses for the satisfying polarity
        for ci in self.adjacency_dict[lit]:
            if self.clause_active[ci]:
                self.mod_stack.append(("active", ci, True))  # old active = True
                self.clause_active[ci] = False

        # 2) decrement unassigned count for all clauses containing this variable (any polarity),
        #    but only if the clause is still active (i.e., not satisfied)
        for ci in self.var_to_clauses[v]:
            if self.clause_active[ci]:
                old_u = self.cl_unassigned[ci]
                if old_u:  # guard
                    self.mod_stack.append(("u", ci, old_u))
                    self.cl_unassigned[ci] = old_u - 1
                

    def assign_lit(self, lit: int) -> None:
        """Only assign, do not touch clause_active."""
        self.assign[abs(lit)] = lit > 0
        self.trail.append(lit)
        
    def backtrack(self, old_len: int, old_mod_stack: int) -> None:
        while len(self.trail) > old_len:
            lit = self.trail.pop()
            self.assign[abs(lit)] = None
        while len(self.mod_stack) > old_mod_stack:
            kind, ci, old = self.mod_stack.pop()
            if kind == "active":
                self.clause_active[ci] = old
            else:  # "u"
                self.cl_unassigned[ci] = old


    def begin_watched_literals(self) -> None:
        for  cl_idx,clause in enumerate(self.clauses):
            self.clause_to_Wliterals[cl_idx] = [clause[0]]
            self.literal_to_clauses[clause[0]].add(cl_idx)
            if len(clause) >=2:
                self.clause_to_Wliterals[cl_idx].append(clause[1])
                self.literal_to_clauses[clause[1]].add(cl_idx)

    def diff(self, literal) -> float:
        score = 0.0
        g = self._gamma_k
        for ci in self.adjacency_dict[literal]:
            if not self.clause_active[ci]:
                continue
            u = self.cl_unassigned[ci]
            if u > 0:
                score += g(u)
        return score


    def WBH(self, var) -> float:
        def gamma_k(k: int) -> float:
            return 5 ** (k - 3)

        # Step 1: compute w_WBH(l) for all literals
        weight_of_literal = defaultdict(float)
        for i,clause in enumerate(self.clauses):
            # skip satisfied clauses
            if  not self.clause_active[i]:
                continue
            k = self.cl_unassigned[i]
            if k == 0:
                continue
            for l in clause:
                if self.assign[abs(l)] is None:  # only count unassigned
                    weight_of_literal[l] += gamma_k(k)

        # Step 2: compute WBH(var) using binary clauses containing var
        score = 0
        for i,clause in enumerate(self.clauses):
            # skip satisfied clauses
            if  not self.clause_active[i]:
                continue
            if self.cl_unassigned[i] != 2:
                continue
            if var in clause or -var in clause:
                x, y = [lit for lit in clause if self.assign[abs(lit)] is None]
                score += weight_of_literal[-x] + weight_of_literal[-y]
        return score

    def mix_diff(self,x : int, y : int) -> float:
        """
        Historical mix_diff from posit program.
        """
        return x + y + x*y*1024

    def __propagate(self, propagate, falsified_literal)->None:
        ok , steps_it = propagate_with_implications(
            changed_literal = falsified_literal,
            adjacency_dict = self.adjacency_dict,
            clauses = self.clauses,
            value = self.value,
            enqueue = self.enqueue,
            assign = self.assign,
            clause_to_Wliterals = self.clause_to_Wliterals,
            literal_to_clauses = self.literal_to_clauses,
            trail = self.trail,
            vsids = self.vsids,
            implications = self.implications
        )
        return ok, steps_it

    def look_ahead(self,propagate):
        unassigned = [i for i,val in enumerate(self.assign) if val is None]
        best_val = -10000
        best_lit = None
      #  print("poustim lookahead")
        for var in unassigned[1:]:
            conflicts = [False,False]
            diff_vals = [0,0]
            trail_len = len(self.trail)
            old_modstack_len = len(self.mod_stack)
            for i,lit in enumerate([var,-var]):
       #         print("lit: ", lit)
                self.enqueue(lit)
                ok , steps_it = self.__propagate(propagate,-lit)
                diff_vals[i] = self.WBH(lit)
                conflicts[i] = not ok
                self.backtrack(trail_len,old_modstack_len)
                self.steps_up += steps_it

            current_val = self.mix_diff(diff_vals[0], diff_vals[1])
            if  conflicts[0] and conflicts[1]:
           #     print("boucham tady")
                return None, False
            
            for i,sign in enumerate([1,-1]):                        
                if conflicts[i]:
                    self.enqueue(-sign * var)
                    ok, _ = self.__propagate(propagate,falsified_literal=sign*var)
                    if not ok: return None, False
                    continue
            if current_val > best_val:
                best_lit = var
                best_val = current_val

        return best_lit, True
    
    
    def solve_with_look_ahead(self,propagate) -> bool:
        if self.clauses == []: # TODO: debug 
            return True
      #  print("rekurzuju")
        dec_literal, ok  = self.look_ahead(propagate)
        if not ok: # contradiction ... UNSAT
     #       print("UNSAT")
            return False

        if dec_literal is None:
            return True  # all variables assigned, SAT

        self.num_decisions += 1
        trail_len = len(self.trail)
        old_mod_stack_len = len(self.mod_stack)

        for sign in [1,-1]:
            self.enqueue(sign * dec_literal)
            ok, steps = self.__propagate(propagate,falsified_literal=-sign*dec_literal)
            self.steps_up += steps

            if ok and self.solve_with_look_ahead(propagate):
                return True
            self.backtrack(trail_len,old_mod_stack=old_mod_stack_len)

        return False
    def solve(self, propagete ):
        start = time.perf_counter()
        sat = self.solve_with_look_ahead(propagete)
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

    solver = SAT_lookAhead(
        clauses,
        max(variables),
        choose_lit=choose_literal,
        score_h=lit_counts_h,
        VSIDS=None
    )
    solved, model, t, n_dec, n_up = solver.solve(propagate_with_implications)

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