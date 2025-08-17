from collections import defaultdict
import time
import sys
from DIMACS_reader import read_DIMACS
from task1.DIMACS_encoding import DIMACS_decoder
from propagate.unit_propagate_watched_literals import unit_propagate_w_watched_lits
from decision_heuristics.choose_literal.choose_best_score import choose_literal
from decision_heuristics.precompute_score.lit_counts_h import lit_counts_h
import os
"""
TODO: 
    1) push changes
    2) create heuristics
    3) double literals
    4) fancy data structure
"""
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

    def diff(self, literal) -> float:
        """
        Currently, just clause reduction heuristic
        """
        #TODO: debugni
        def gamma_k(k : int) -> float:
            if k == 2: return 1
            if k == 3: return 0.2
            if k == 4: return 0.05
            if k == 5: return 0.01
            if k == 6: return 0.003
            else:      return 20.4514 * (0.218673 ** k)
        sum = 0
        for clause in self.adjacency_dict[literal]:
            for l in clause:
                val = self.assign[abs(l)]
                if (val and l > 0) or (val is False and l < 0):
                    continue #clause satisfied
            sum += len([l for l in clause if self.assign[abs(l)] is None]) * gamma_k(len([l for l in clause if self.assign[abs(l)] is None]))
        return sum
    
    def WBH(self, literal) -> float:
        """
        Currently, just clause reduction heuristic
        """
        def gamma_k(k : int) -> float:
            return 5 ** (k-3)
        # #_k (x_i) ...number of occurences of not x_i in clauses of size k
        # w(x_i) = \sum gamma_k #_k(x_i)
        binary_clauseses = set()
        for clause in self.clauses:
            unassigned = [l for l in clause if self.assign[l] is not None]
            if len(unassigned) == 2:
                binary_clauseses.add(tuple(unassigned))

        weight_of_literal = defaultdict(float)
        for clause in binary_clauseses:
            satisfied = False
            for l in clause:
                val = self.assign[abs(l)]
                if (val and l > 0) or (val is False and l < 0):
                    satisfied = True
            if satisfied:
                continue
            for l in [l,-l]:
                if l not in weight_of_literal:
                    weight_of_literal[l] = 0
                    counts = defaultdict(int) # len(clause) -> count
                    for clause in self.adjacency_dict[-l]:
                        counts[
                            len([lit for lit in clause 
                                if self.assign[lit] is None]
                            )
                        ] += 1

                weight_of_literal[l] = sum(
                    counts[key] * gamma_k(counts[key])
                    for key in counts.keys()
                ) 
        return sum(
            weight_of_literal[-cl[0]] + \
            weight_of_literal[-cl[1]] 
            for cl in binary_clauseses
        )
    def mix_diff(self,x : int, y : int) -> float:
        """
        Historical mix_diff from posit program.
        """
        return x + y + x*y * 1024

    def __propagate(self, propagate, falsified_literal)->None:
        ok , steps_it = propagate(
            changed_literal = falsified_literal,
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
        return ok, steps_it

    def look_ahead(self,propagate):
        unassigned = [i for i,val in enumerate(self.assign) if val is None]
        best_val = -10000
        best_lit = None
        for var in unassigned[1:]:
            conflicts = [False,False]
            diff_vals = [0,0]
            trail_len = len(self.trail)
            for i,lit in enumerate([var,-var]):
                self.enqueue(lit)
                ok , steps_it = self.__propagate(propagate,-lit)
                diff_vals[i] = self.diff(lit)
                conflicts[i] = not ok
                self.backtrack(trail_len)
                self.steps_up += steps_it
                # 1. We need to check whether there is no contradiction for both literals
                # 2. if there is contradiction for only one, just enqueue put it into model
                # 3. track best variable and return this variable

            current_val = self.mix_diff(diff_vals[0], diff_vals[1])
        #    print("curry: ",current_val)
            if  conflicts[0] and conflicts[1]:
                return None, False
            
            if conflicts[0]:
                temp_len = len(self.trail)
                self.enqueue(-var)
                ok , steps_it = propagate(
                    changed_literal = var,
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
            #    self.backtrack(temp_len)
            #    if not ok: return None, False
            #    else: self.enqueue(-var)
                continue
            elif conflicts[1]:
                temp_len = len(self.trail)
                self.enqueue(var)
                ok , steps_it = propagate(
                    changed_literal = -var,
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
                #self.backtrack(temp_len)

               # if not ok: return None, False
                #else: self.enqueue(var)
         #       print("forcuju: ", var)
                continue
            if current_val > best_val:
                best_lit = var
                best_val = current_val

        return best_lit, True
    def solve_with_look_ahead(self,propagate) -> bool:
      #  print("rekurzuju")
        if self.clauses == []: # TODO: debug 
            return True
        
        dec_literal, ok  = self.look_ahead(propagate)
      #  print(self.assign)
      #  print("dec_literal: ", dec_literal)
        if not ok: # contradiction ... UNSAT
            return False

        if dec_literal is None:
      #      print("correct")
      #      print(self.assign)
            return True  # all variables assigned, SAT

        self.num_decisions += 1
        trail_len = len(self.trail)

        self.enqueue(dec_literal)
        ok, steps = propagate(
            changed_literal=-dec_literal,
            adjacency_dict=self.adjacency_dict,
            clauses=self.clauses,
            value=self.value,
            enqueue=self.enqueue,
            assign=self.assign,
            clause_to_Wliterals=self.clause_to_Wliterals,
            literal_to_clauses=self.literal_to_clauses,
            trail=self.trail,
            vsids=self.vsids,
        )
        self.steps_up += steps
        if ok and self.solve_with_look_ahead(propagate):
            return True
        self.backtrack(trail_len)

        # Try the opposite polarity
        self.enqueue(-dec_literal)
        ok, steps = propagate(
            changed_literal=dec_literal,
            adjacency_dict=self.adjacency_dict,
            clauses=self.clauses,
            value=self.value,
            enqueue=self.enqueue,
            assign=self.assign,
            clause_to_Wliterals=self.clause_to_Wliterals,
            literal_to_clauses=self.literal_to_clauses,
            trail=self.trail,
            vsids=self.vsids,
        )
        self.steps_up += steps
        if ok and self.solve_with_look_ahead(propagate):
            return True
        self.backtrack(trail_len)

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