from collections import defaultdict
from DIMACS_reader import read_DIMACS
from DIMACS_encoding import DIMACS_decoder

import sys

class SAT_dpll:
    def __init__(self, clauses, variables):
        self.clauses = clauses
        self.p_model = {}
        self.watched_literals = {}
        self.variables = variables
        self._init_watched_literals()

    def _init_watched_literals(self):
        for clause in self.clauses:
            self.watched_literals.setdefault(abs(clause[0]),[]).append(clause)
            if len(clause) >= 2:
                self.watched_literals.setdefault(abs(clause[1]),[]).append(clause)

    def clause_satisfied(self,clause : list[int],p_model : dict) -> bool:
        return any(p_model[abs(lit)] == (lit > 0) for lit in clause if abs(lit) in p_model.keys())
    
    def is_model(self,clauses: list[list[int]], p_model : dict[int,bool]) -> bool:
        """
        Check if given model satisfies all clauses.
        """
        return all(self.clause_satisfied(clause, p_model) for clause in clauses)
    def unit_propagation(self,clauses : list[list[int]], p_model : dict[int,bool], \
                            ) -> tuple[list[int], dict[int,bool]]:
        """
        Perform unit propagation to reduce the number of variables in the model.
        """
        res = []
        unit_clauses = []
        for clause in clauses:
            unassigned_literals = [lit for lit in clause if abs(lit) not in p_model.keys()]
            if len(unassigned_literals) == 1:
                unit_clauses.append(unassigned_literals[0]) 

        while len(unit_clauses) != 0:
            l = unit_clauses.pop(0)
            res.append(l)
            val = l > 0
            if l in p_model and p_model[abs(l)] != val: # conflict
                return None, {}
            p_model[abs(l)] = val
            
            for clause in self.watched_literals.setdefault(abs(l),[]): # updating watched_literals
                if self.clause_satisfied(clause,p_model):
                    continue
                rest = [lit for lit in clause if lit not in (l, -l) 
                                  and abs(lit) not in p_model.keys()]
                if len(rest) == 1:
                    unit_clauses.append(rest[0]) 
                elif len(rest) == 0: # not satisfied and everything is assigned --> conflict
                    return None, {}
                else:
                    self.watched_literals.setdefault(abs(rest[0]), []).append(clause)

        return res, p_model
        
    def choose_literal(self, clauses: list[list[int]]) -> int:
        """
        Choose a literal that appears in the most number of clauses.
        """
        unassigned_literals = [lit for lit in self.variables if lit not in self.p_model]
        lit_counts = defaultdict(int)
        for clause in clauses:
            for lit in [l for l in clause if l in unassigned_literals]:
                lit_counts[lit] += 1

        max_count = 0
        max_lit = None
        for lit, count in lit_counts.items():
            if count > max_count:
                max_count = count
                max_lit = lit
        return max_lit


    def make_literal_val(literal : int, model : dict[int,bool], val = True) -> dict[int,bool]:
        if literal > 0:
            model[literal] = True
        else:
            model[-literal] = False
        return model

    def dpll(self,clauses: list[list[int]],p_model : dict[int,bool]) \
                                ->tuple[bool,dict[int,bool]]:
        """
        Implements the DPLL algorithm for SAT problem resolution."
        """
        updated_vars, upd_p_model = self.unit_propagation(clauses,p_model)

        if None == updated_vars:
            return None
        
        if self.is_model(clauses,upd_p_model):
            return upd_p_model
        
        l = self.choose_literal(clauses)

        for v in [True, False]:
            tmp_model = self.make_literal_val(l,upd_p_model,val = v)
            res = self.dpll(clauses, tmp_model)
            if res != None:
                return res
        return None

if __name__ == "__main__":
    clauses, variables = [],[]
    print(sys.argv)
    if len(sys.argv) == 3:
        if sys.argv[1] == "-d":
            print("running")
            clauses, variables = read_DIMACS(sys.argv[2])

        elif sys.argv[1] == "-s":
            D_decoder = DIMACS_decoder(sys.argv[2])
            D_decoder.get_var_mapping()
            clauses, variables =  D_decoder.get_DIMACS(), D_decoder.variables
    
    print(clauses, variables)
    solver = SAT_dpll(clauses,variables)
    print(solver(clauses, {}))
