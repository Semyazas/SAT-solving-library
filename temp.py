from collections import defaultdict
import time
import sys
from DIMACS_reader import read_DIMACS
from task1.DIMACS_encoding import DIMACS_decoder
from propagate.propagate_binary import Binary_propagation
from decision_heuristics.choose_literal.choose_best_score import choose_literal
from decision_heuristics.precompute_score.lit_counts_h import lit_counts_h
import os
from look_ahead_parts.preselection.preselect import pre_select

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
            WBH = False,
            propagation = None) -> None:
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
            else: v = 5 ** (k - 3)
            self._gamma[k]= v
            return v
        
        def _gamma_crh_k(k : int) -> float:
            if k in self._gamma: return self._gamma[k]
            if k == 2: v = 1.0
            elif k == 3: v = 0.2
            elif k == 4: v = 0.05
            elif k == 5: v = 0.01
            elif k == 6: v = 0.003
            else: v = 20.4514 * (0.218673 ** k)
            self._gamma[k] = v
            return v
        self.wbh = WBH

        self.adjacency_dict = defaultdict(list)
        self._gamma_k = _gamma_k if self.wbh else _gamma_crh_k
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

        self.clause_to_Wliterals = defaultdict(list)
        self.literal_to_clauses = defaultdict(set)
        self.score = None
        # Precompute literal occurrences for fast heuristic
        for i,clause in enumerate(clauses):
            for lit in clause:
                self.adjacency_dict[lit].append(i)


        self.literal_weight = defaultdict(float)
        self.wbh_score = 0
        self._init_literal_weights()
        self.wbh_score = self._init_literal_score()

        self.prop = propagation(
            clauses = self.clauses,
            assign  = self.assign,
            enqueue = self.enqueue
        )
    def value(self, lit):
        """Return literal truth value under current assignment or None."""
        val = self.assign[abs(lit)]
        return val if lit > 0 else (not val if val is not None else None)
    
    def _init_literal_score(self):
        #TODO: maybe more precompute
        # Step 1: compute w_WBH(l) for all literals
        # Step 2: compute WBH(var) using binary clauses containing var
        score = 0
        for i,clause in enumerate(self.clauses):
            if self.cl_unassigned[i] != 2:
                continue
            x, y = [lit for lit in clause if self.assign[abs(lit)] is None]
            score += self.literal_weight[-x] + self.literal_weight[-y]
        return score

    def _init_literal_weights(self):
        # All clauses active, all literals unassigned at start
        for ci, clause in enumerate(self.clauses):
            k = len(clause)
            if k == 0: 
                continue
            w = self._gamma_k(k)
            for lit in clause:
                self.literal_weight[lit] += w
    def enqueue(self, lit: int) -> None:
        v = abs(lit)
        self.assign[v] = (lit > 0)
        self.trail.append(lit)

        # 1) mark satisfied clauses for the satisfying polarity
        for ci in self.adjacency_dict[lit]:
            if self.clause_active[ci]:
                self.mod_stack.append(("active", ci, True))  # old active = True
                self.clause_active[ci] = False

                if self.wbh and self.cl_unassigned[ci] == 2:
                    x, y = [l for l in self.clauses[ci] if self.assign[abs(l)] is None or l == lit]
                    self.wbh_score -= self.literal_weight[-x] + self.literal_weight[-y]
                    self.mod_stack.append(("add_score", ci, self.literal_weight[-x] + self.literal_weight[-y]))  # old active = True

        # 1) mark satisfied clauses for the satisfying polarity
        for ci in self.adjacency_dict[lit]:
            if self.clause_active[ci]:
                for lit in self.clauses[ci]:
                    self.literal_weight[lit] -= self._gamma_k(self.cl_unassigned[ci])
                    self.mod_stack.append((
                        "add",
                        lit,
                        self._gamma_k(self.cl_unassigned[ci])
                    ))

        # 2) decrement unassigned count for all clauses containing this variable (any polarity),
        #    but only if the clause is still active (i.e., not satisfied)
        for ci in self.adjacency_dict[-lit if self.assign[v] else lit]:
            if self.clause_active[ci]:
                old_u = self.cl_unassigned[ci]
                if old_u:  # guard
                    self.mod_stack.append(("u", ci, old_u))
                    self.cl_unassigned[ci] = old_u - 1
                
    def backtrack(self, old_len: int, old_mod_stack: int) -> None:
        while len(self.trail) > old_len:
            lit = self.trail.pop()
            self.assign[abs(lit)] = None
        while len(self.mod_stack) > old_mod_stack:
            kind, ci, old = self.mod_stack.pop()
            if kind == "active":
                self.clause_active[ci] = old
            elif kind == "add":
                self.literal_weight[ci] += old
            elif kind == "add_score":
                self.wbh_score += old
            else:  # "u"
                self.cl_unassigned[ci] = old

    def CRH(self, literal) -> float:
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
        #TODO: maybe more precompute
        # Step 1: compute w_WBH(l) for all literals
        # Step 2: compute WBH(var) using binary clauses containing var
        return self.wbh_score

    def mix_diff(self,x : int, y : int) -> float:
        """
        Historical mix_diff from posit program.
        """
        return x + y + x*y*1024

    def __propagate(self, falsified_literal)->None:
        ok , steps_it = self.prop.propagate_with_implications(
            changed_literal = falsified_literal,
            adjacency_dict = self.adjacency_dict,
            clauses = self.clauses,
            enqueue = self.enqueue,
            assign = self.assign,
            clause_to_Wliterals = self.prop.clause_to_Wliterals,
            literal_to_clauses = self.prop.literal_to_clauses,
            trail = self.trail,
            implications = self.prop.implications
        )
        return ok, steps_it
    def get_number_of_new_binary_clauses(self,lit):
        res = 0
        for ci in self.adjacency_dict[lit]:
            if self.clause_active[ci] and self.cl_unassigned[ci] == 2:
                res +=1
        return res
    def double_look_ahead(self):
        best_val = -10000
        best_lit = None
        threshold = self.nvars*0.0017 #* 1e10
        for var in pre_select(
                clauses=self.clauses, clause_active=self.clause_active,
                adjacency_dict=self.adjacency_dict, nvars=self.nvars,
                assign=self.assign, percent=25):
            conflicts = [False, False]
            diff_vals = [0, 0]
            trail_len = len(self.trail)
            old_modstack_len = len(self.mod_stack)

            for i, lit in enumerate([var, -var]):
                self.enqueue(lit)
                ok, steps_it = self.__propagate(-lit)
                diff_vals[i] = self.WBH(lit) if self.wbh else self.CRH(lit)
                conflicts[i] = not ok
                if ok  and \
                    self.get_number_of_new_binary_clauses(-lit) > threshold:
                    # SECOND-LEVEL LOOKAHEAD
                    second_best = -10000
                    for var2 in pre_select(
                            clauses=self.clauses, clause_active=self.clause_active,
                            adjacency_dict=self.adjacency_dict, nvars=self.nvars,
                            assign=self.assign, percent=25):
                        trail2 = len(self.trail)
                        mod2 = len(self.mod_stack)
                        inner_conf = [False, False]
                        inner_diff = [0,0]
                        for j, lit2 in enumerate([var2, -var2]):
                            self.enqueue(lit2)
                            ok2, steps2 = self.__propagate(-lit2)
                            inner_diff[j] = self.WBH(lit2) if self.wbh else self.CRH(lit2)
                            inner_conf[j] = not ok2
                            self.backtrack(trail2, mod2)
                            self.steps_up += steps2

                        if inner_conf[0] and inner_conf[1]:
                            conflicts[i] = True
                            break
                        score2 = self.mix_diff(inner_diff[0], inner_diff[1])
                        if score2 > second_best:
                            second_best = score2
                    diff_vals[i] = second_best
                self.backtrack(trail_len, old_modstack_len)
                self.steps_up += steps_it

            current_val = self.mix_diff(diff_vals[0], diff_vals[1])
            if conflicts[0] and conflicts[1]:
                return None, False

            for i, sign in enumerate([1, -1]):
                if conflicts[i]:
                    self.enqueue(-sign * var)
                    ok, _ = self.__propagate(falsified_literal=sign * var)
                    if not ok:
                        return None, False
                    continue

            if current_val > best_val:
                best_val = current_val
                best_lit = var

        return best_lit, True
    def solve_with_look_ahead(self) -> bool:
        if self.clauses == []: # TODO: debug 
            return True
      #  print("rekurzuju")
        dec_literal, ok  = self.double_look_ahead()
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
            ok, steps = self.__propagate(falsified_literal=-sign*dec_literal)
            self.steps_up += steps

            if ok and self.solve_with_look_ahead():
                return True
            self.backtrack(trail_len,old_mod_stack=old_mod_stack_len)

        return False
    def solve(self):
        start = time.perf_counter()
        sat = self.solve_with_look_ahead()
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
        WBH=True,
        propagation=Binary_propagation
    )
    solved, model, t, n_dec, n_up = solver.solve()

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