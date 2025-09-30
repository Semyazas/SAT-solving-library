from collections import defaultdict
import time
import argparse
from parser import read_DIMACS, DIMACS_decoder
from solver.propagate import Binary_propagation
from solver.look_ahead_solver.difference_heuristics import WBH_heuristic
from solver.look_ahead_solver.look_ahead_parts.preselection.preselect import pre_select
class SAT_lookAhead:
    def __init__(self,
            clauses, 
            nvars,
            heuristic,
            propagation,
            preselect,
            threshold_mod=1) -> None:
        self.clauses = clauses
        self.nvars = nvars
        self.threshold_mod = threshold_mod
        # in __init__
        self.cl_unassigned = [len(cl) for cl in self.clauses]  # incremental unassigned count
        self.mod_stack = []  # (kind, cl_idx, old_value) where kind in {"active","u"}
        # tiny cache for gamma_k
        self.adjacency_dict = defaultdict(list)
        self.clause_active = [True for _ in range(len(clauses))]
        # build adjacency_dict (literal -> clause idx) AND var_to_clauses (var -> clause idx)
        self._init_adjacency_dict()
        self.nvars = nvars
        self.assign = [None for _ in range(nvars+1)]   # 1-indexed
        self.trail = []                     # stack of assigned literals
        self.num_decisions = 0
        self.steps_up = 0
        # Precompute literal occurrences for fast heuristic
        self.prop = propagation(
            clauses = self.clauses,
            assignment  = self.assign,
            enqueue = self.enqueue,
            value = self._value
        )
        self.heuristic = heuristic(
            clauses        = self.clauses,
            adjacency_dict = self.adjacency_dict,
            cl_unassigned  = self.cl_unassigned,
            assign         = self.assign,
            modstack       = self.mod_stack,
            clause_active  = self.clause_active
        )
        self.pre_select = pre_select 

    def _value(self, lit):
        """Return literal truth value under current assignment or None."""
        val = self.assign[abs(lit)]
        return val if lit > 0 else (not val if val is not None else None)

    def _init_adjacency_dict(self):
        for ci, clause in enumerate(self.clauses):
            for lit in clause:
                self.adjacency_dict[lit].append(ci)

    def _update_cl_lens(self,lit : int, v : int)->None:
        for ci in self.adjacency_dict[-lit if self.assign[v] else lit]:
            if self.clause_active[ci]:
                old_u = self.cl_unassigned[ci]
                self.mod_stack.append(("u", ci, old_u))
                self.cl_unassigned[ci] = old_u - 1
        
    def enqueue(self, lit: int) -> None:
        v = abs(lit)
        self.assign[v] = (lit > 0)
        self.trail.append(lit)

        for ci in self.adjacency_dict[lit]:
            if self.clause_active[ci]:
                # --- score update first ---
                self.heuristic.update_score(ci = ci, lit = lit)

                # --- then mark clause inactive ---
                self.clause_active[ci] = False
                self.mod_stack.append(("active", ci, True))

        self.heuristic.update_weights(lit=lit)
        self._update_cl_lens(lit, v)
         
    def backtrack(self, old_len: int, old_mod_stack: int) -> None:
        while len(self.trail) > old_len:
            lit = self.trail.pop()
            self.assign[abs(lit)] = None
        while len(self.mod_stack) > old_mod_stack:
            kind, ci, old = self.mod_stack.pop()
            if kind == "active":
                self.clause_active[ci] = old
            elif kind == "add":
                self.heuristic.literal_weight[ci] += old
            elif kind == "add_score":
                self.heuristic.wbh_score += old
            else:  # "u"
                self.cl_unassigned[ci] = old

    def mix_diff(self,x : int, y : int) -> float:
        """
        Historical mix_diff from posit program.
        """
        return x + y + x*y*1024

    def __propagate(self, falsified_literal)->None:
        ok , steps_it = self.prop.propagate(
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

    def inner_look_ahead(self, conflicts : list[int]) -> int:
        second_best = -10000
        for var2 in self.pre_select(
                clauses=self.clauses, clause_active=self.clause_active,
                adjacency_dict=self.adjacency_dict, nvars=self.nvars,
                assign=self.assign, percent=10):
            trail2 = len(self.trail)
            mod2 = len(self.mod_stack)
            inner_conf = [False, False]
            inner_diff = [0,0]
            for j, lit2 in enumerate([var2, -var2]):
                self.enqueue(lit2)
                ok2, steps2 = self.__propagate(-lit2)
                inner_diff[j] = self.heuristic.diff(lit2)
                inner_conf[j] = not ok2
                self.backtrack(trail2, mod2)
                self.steps_up += steps2

                if inner_conf[0] and inner_conf[1]:
                    conflicts[i] = True
                    break
                score2 = self.mix_diff(inner_diff[0], inner_diff[1])
                if score2 > second_best:
                    second_best = score2 

        return second_best           
    
    def double_look_ahead(self):
        best_val = -10000
        best_lit = None
        threshold = self.nvars*0.17 *self.threshold_mod
        for var in self.pre_select(
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
                diff_vals[i] = self.heuristic.diff(lit)
                conflicts[i] = not ok
                if ok  and \
                    self.get_number_of_new_binary_clauses(-lit) > threshold:
                    # SECOND-LEVEL LOOKAHEAD                   
                    diff_vals[i] = self.inner_look_ahead(conflicts)
                self.backtrack(trail_len, old_modstack_len)
                self.steps_up += steps_it

            # decision for var
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

    def solve_with_look_ahead(self,propagate) -> bool:
        if self.clauses == []: # TODO: debug 
            return True

        dec_literal, ok  = self.double_look_ahead()
        if not ok: # contradiction ... UNSAT
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
    
def main()->None:
    parser = argparse.ArgumentParser(
        description="SAT solver with look-ahead and different input formats."
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
    parser.add_argument(
        "threshold",
        type=float,
        nargs="?",
        default=1.0,
        help="Threshold modifier (default=1.0)."
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
    solver = SAT_lookAhead(
        clauses,
        max(variables),
        heuristic=WBH_heuristic,
        propagation=Binary_propagation,
        preselect=pre_select,
        threshold_mod=args.threshold
    )
    solved, model, t, n_dec, n_up = solver.solve(solver.prop.propagate)

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