from collections import defaultdict
from DIMACS_reader import read_DIMACS
from task1.DIMACS_encoding import DIMACS_decoder
import time
import sys

#TODO: 

class SAT_dpll:
    def __init__(self, clauses, variables):
        self.clauses = clauses
        self.p_model = {}
        self.watched_literals = {}
        self.variables = variables
        self.number_of_decisions = 0
        self.steps_of_unit_propagation = 0
    #    self.literal_counts = 

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
    def unit_propagation(self, clauses, p_model):
        """
        Fast unit propagation: iterative, no repeated scans of all clauses.
        Returns (conflict_found, model, updated_clauses)
        """
        unit_queue = []
        updated_clauses = []

        # Initial scan: filter clauses & collect unit literals
        for clause in clauses:
            # If already satisfied, skip
            if self.clause_satisfied(clause, p_model):
                continue

            # Remove falsified literals
            new_clause = [lit for lit in clause
                        if abs(lit) not in p_model or p_model[abs(lit)] == (lit > 0)]

            # Empty clause → conflict
            if not new_clause:
                return None, {}, None

            updated_clauses.append(new_clause)

            # Collect new units
            if len(new_clause) == 1:
                unit_queue.append(new_clause[0])

        # Iteratively assign unit literals
        while unit_queue:
            
         #   print(updated_clauses)
            lit = unit_queue.pop()
         #   print(lit)
            val = lit > 0

            # Conflict if opposite assignment already exists
            if abs(lit) in p_model:
                if p_model[abs(lit)] != val:
                    return None, {}, None
                continue

            # Assign literal
            p_model[abs(lit)] = val
            self.steps_of_unit_propagation += 1

            # Propagate only on unsatisfied clauses
            new_clauses = []
            for clause in updated_clauses:
                # Skip satisfied
                if any(p_model.get(abs(l)) == (l > 0) for l in clause):
                    continue

                # Filter falsified literals
                new_clause = [l for l in clause
                            if abs(l) not in p_model or p_model[abs(l)] == (l > 0)]

                # Conflict?
                if not new_clause:
                    return None, {}, None

                # Unit clause detected → enqueue
                if len(new_clause) == 1 and new_clause[0] not in unit_queue:
                    unit_queue.append(new_clause[0])

                new_clauses.append(new_clause)

            updated_clauses = new_clauses
       # print("done")
        return [], p_model, updated_clauses



    def choose_literal(self, clauses: list[list[int]], model) -> int:
        #TODO: Debug this
        #TODO: repeating clauses: debug decoder
        """
        Choose a literal that appears in the most number of clauses.
        """
        unassigned_literals = set(self.variables) - model.keys()
        lit_counts = defaultdict(int)
        for clause in clauses:
            for lit in clause:
                if abs(lit) in unassigned_literals:
                    lit_counts[lit] += 1

        return max(lit_counts, key=lit_counts.get, default=None)


    def make_literal_val(self,literal : int, model : dict[int,bool], val = True) -> dict[int,bool]:
        if literal == None:
            return None
        if literal > 0:
            model[literal] = val
        else:
            model[-literal] = not val
        return model
    
    def dpll(self,clauses: list[list[int]],p_model : dict[int,bool]) \
                                ->tuple[bool,dict[int,bool]]:
        """
        Implements the DPLL algorithm for SAT problem resolution."
        """
        updated_vars, upd_p_model, updated_clauses = self.unit_propagation(clauses,p_model)

        #print("upd model: ",upd_p_model)
        #print(updated_clauses)
        if None == updated_vars:
            return None
        
        if not updated_clauses:
            return upd_p_model
        
        l = self.choose_literal(updated_clauses,upd_p_model)

        if l is None:
            return upd_p_model

        for v in [True, False]:
            self.number_of_decisions +=1
            tmp_model = self.make_literal_val(l,upd_p_model.copy(), v)
            if tmp_model is not None:   
                res = self.dpll(updated_clauses, tmp_model)
                if res != None:
                    return res
        return None
    
    def solve(self,clauses : list[list[int]]) :
        start_time = time.perf_counter()
        model = self.dpll(clauses,{})
        end_time = time.perf_counter()

        computation_time = end_time - start_time

        return (model != None,
                model, 
                computation_time,
                self.number_of_decisions,
                self.steps_of_unit_propagation
        )

if __name__ == "__main__":
    clauses, variables = [],[]
    print(sys.argv)
    dimacs = True
    if len(sys.argv) == 3:
        if sys.argv[1] == "-d":
            print("running")
            clauses, variables = read_DIMACS(sys.argv[2])

        elif sys.argv[1] == "-s":
            D_decoder = DIMACS_decoder(sys.argv[2])
            D_decoder.get_var_mapping()
            clauses, variables =  D_decoder.get_DIMACS(), D_decoder.var2dimacs_map.values()
            dimacs = False
    #print(clauses, variables)
    solver = SAT_dpll(clauses,variables)
    solved, model, computation_time, n_decs, st_up  =  solver.solve(clauses)

    print("SAT: ", solved)
    if not dimacs:
        for var in model:
            print(D_decoder.dmacs2var_map[var], " ", model[var])
    else:
        print(model)
        print(clauses)
        vals=  list(model.keys()).copy()
        vals.sort()
        for var in vals:
            if model[var] == False:
                print(-var)
            else:
                print(var)

    print("computation time: ", computation_time)
    print("number of decisions: ", n_decs)
    print("steps of unit propagation: ", st_up)