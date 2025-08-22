from difference_heuristics.heuristic import DifferenceHeuristic

class CRH_heuristics(DifferenceHeuristic):
    def __init__(self, **args):
        self.adjacency_dict = args["adjacency_dict"]
        self.clause_active  = args["clause_active"]
        self.cl_unassigned  = args["cl_unassigned"]
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
        self._gamma_k = _gamma_k

    def update_score(self, **args):
        pass
    def update_weights(self,**args):
        pass
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
    
