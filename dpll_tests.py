from dpll import dpll, unit_propagation, is_model

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