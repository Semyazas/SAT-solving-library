from collections import defaultdict
from DIMACS_reader import read_DIMACS
from DIMACS_encoding import DIMACS_decoder

import sys

def remove_clauses_with_l(l : int, clauses : list[int]) -> None:
    l_in_clauses = True
    while l_in_clauses:
        l_in_clauses = False
        for i in range(len(clauses)):
            if l in clauses[i]:
                clauses.remove(clauses[i])
                l_in_clauses = True
                break

#TODO: zajisti, aby jsi neměl klauzuli [1,-1]
def unit_propagation(clauses : list[list[int]], p_model : dict[int,bool], \
                        ) -> tuple[list[int], list[list[int]],dict[int,bool]]:
    """
    Perform unit propagation to reduce the number of variables in the model.
    """
    if [] in clauses:
        return None, [], p_model

    res = []
    def _unit_clause():
        return next((clause[0] for clause in clauses if len(clause) == 1), None)
       
    l = _unit_clause()
    while l != None:
        res.append(l)
        if l > 0:
            p_model[l] = True
        else:
            p_model[-l] = False
        remove_clauses_with_l(l,clauses)
        for clause in clauses:
            if -l in clause:
                clause.remove(-l)
        if [] in clauses:
            return clauses, [], {}
        l = _unit_clause()
    return clauses, res, p_model

def is_model(clauses: list[list[int]], p_model : dict[int,bool], \
                    variables: list[int]) -> bool:
    """
    Check if given model satisfies all clauses.
    """
    if len(variables) != len(p_model):
        return False
    
    for clause in clauses: 
        satisfied = False
        for literal in clause: # we simply loop over each clause, and check wheter model satisfies it
            if literal > 0:
                if p_model[literal]:
                    satisfied = True
                    break
            else:
                if not p_model[-literal]:
                    satisfied = True
                    break
        if not satisfied:
            return False
    return True
    
def choose_literal(clauses: list[list[int]]) -> int:
    """
    Choose a literal that appears in the most number of clauses.
    """
    lit_counts = defaultdict(int)
    for clause in clauses:
        for lit in clause:
            lit_counts[lit] += 1

    max_count = 0
    max_lit = None
    for lit, count in lit_counts.items():
        if count > max_count:
            max_count = count
            max_lit = lit
    return max_lit

def apply_l(l : int, clauses : list[list[int]]) -> list[list[int]]:
    """
    Apply unit propagation and return modified clauses.
    """
    remove_clauses_with_l(l, clauses )
    for clause in clauses:
        if -l in clause:
            clause.remove(-l)

    return clauses

def make_literal_val(literal : int, model : dict[int,bool], val = True) -> dict[int,bool]:
    if literal > 0:
        model[literal] = True
    else:
        model[-literal] = False
    return model

def dpll(clauses: list[list[int]],p_model : dict[int,bool]) \
                            ->tuple[bool,dict[int,bool]]:
    """
    Implements the DPLL algorithm for SAT problem resolution."
    """
    upd_clauses, _, upd_p_model = unit_propagation(clauses,p_model)
    if upd_clauses == []:
        return upd_p_model
    elif [] in upd_clauses:
        return None
    
    l = choose_literal(upd_clauses)
    tmp_clauses = apply_l(l,upd_clauses)

    tmp_model = make_literal_val(l,upd_p_model)
    res = dpll(tmp_clauses, tmp_model)

    if res != None:
        return res
    tmp_model = make_literal_val(l,upd_p_model,val = False)
    res = dpll(tmp_clauses,tmp_model,upd_p_model)
    if res!= None:
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
    print(dpll(clauses, {}))
