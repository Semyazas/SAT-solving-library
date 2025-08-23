from collections import defaultdict
from difference_heuristics.heuristic import DifferenceHeuristic

class WBH_heuristic(DifferenceHeuristic):
    def __init__(self, **args):
        self.clauses        = args["clauses"]
        self.cl_unassigned  = args["cl_unassigned"]
        self.assign         = args["assign"]
        self.mod_stack      = args["modstack"]
        self.clause_active  = args["clause_active"]
        self.adjacency_dict = args["adjacency_dict"]
        self._gamma         = {}
        def _gamma_k(k: int) -> float:
            if k in self._gamma: return self._gamma[k]
            else: v = 5 ** (k - 3)
            self._gamma[k]= v
            return v
        self._gamma_k         = _gamma_k
        self.literal_weight = self._init_literal_weights()
        self.wbh_score      = self._init_literal_score()

    def _init_literal_weights(self):
        # All clauses active, all literals unassigned at start
        literal_weight = defaultdict(float)
        for ci, clause in enumerate(self.clauses):
            k = len(clause)
            if k == 0: 
                continue
            w = self._gamma_k(k)
            for lit in clause:
                literal_weight[lit] += w
        return literal_weight
    
    def _init_literal_score(self) -> int:
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
    
    def update_weights(self,lit):
        for ci in self.adjacency_dict[lit]:
            if self.clause_active[ci]:
                for lit in self.clauses[ci]:
                    self.literal_weight[lit] -= \
                        self._gamma_k(self.cl_unassigned[ci])
                    self.mod_stack.append((
                        "add",
                        lit,
                        self._gamma_k(self.cl_unassigned[ci])
                    ))
                    
    def diff(self, var) -> float:
        #TODO: maybe more precompute
        # Step 1: compute w_WBH(l) for all literals
        # Step 2: compute WBH(var) using binary clauses containing var
      #  print(self.wbh_score)
        return self.wbh_score
    def remove_binary_clause(self, ci, x, y):
        delta = self.literal_weight[-x] + self.literal_weight[-y]
        self.wbh_score -= delta
        self.mod_stack.append(("add_score", ci, delta))