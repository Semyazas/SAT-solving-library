from collections import defaultdict

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
    upd_model = model.copy()
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

def unit_propagation_tests():
    formula_from_presentation = [
                                    [-1],
                                    [2,-3],
                                    [1,-2],
                                    [1,2,3],
                                    [-1,3]
                                ]
    p_model = {1:False, 2:False,3:True}

    assert [] == unit_propagation(formula_from_presentation,{})[1]

    almost_formula_from_presentation = [
                                    [-1],
                                    [2,-3],
                                    [1,4],
                                    [1,2,3],
                                    [-1,3]
                                ]
    p_model = [-1, 4]
    assert p_model == unit_propagation(almost_formula_from_presentation,{})[1]

def simple_test_correct_model():
    clauses1 = [[1,2],
               [-1,2],
               [3,-4,5],
               [-3,-5]
            ]
    p_model1 = {1:True, 2:True, 3:False, 4:False, 5:False}

    p_not_model1 = {1:True, 2:False, 3:True,4:True ,5:True}

    clauses2 = [[1],
               [-2],
            ]
    p_model2 = {1:True, 2:False}

    vars1 = [1,2,3,4,5]
    vars2 = [1,2]
    assert is_model(clauses2, p_model2,vars2)

    assert is_model(clauses1, p_model1, vars1)
    assert not is_model(clauses1, p_not_model1, vars1)

def simple_test_dpll():
    almost_formula_from_presentation = [
                                    [-1],
                                    [2,-3],
                                    [1,-4],
                                    [1,2,3],
                                    [3]
                                ]
    p_model1 = {1:False, 2:True, 3:True, 4:False}

    assert dpll(almost_formula_from_presentation, {}) == p_model1

    assert dpll([[-1,2],[-2],[1]],{}) == None

if __name__ == "__main__":
    simple_test_correct_model()
    unit_propagation_tests()
    simple_test_dpll()