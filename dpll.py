
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