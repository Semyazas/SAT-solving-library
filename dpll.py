
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
                        ) -> tuple[list[int], list[list[int]]]:
    """
    Perform unit propagation to reduce the number of variables in the model.
    """
    if [] in clauses:
        return None, []

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
            return clauses, []
        l = _unit_clause()
    return clauses, res

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
    
def dpll(clauses: list[list[int]],p_model : dict[int,bool]) \
                            ->tuple[bool,dict[int,bool]]:
    """
    Implements the DPLL algorithm for SAT problem resolution."
    """
    pass

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

if __name__ == "__main__":
    simple_test_correct_model()