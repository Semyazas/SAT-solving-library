from collections import defaultdict
from functools import partial

def JW_heuristic(clauses : list[list[int]],
                 variables : list[int]) -> dict:

    scores = defaultdict(float)
    for var in variables:
        for lit in [var,-var]:
            l_score = 0
            for clause in clauses:
                if lit in clause:
                    l_score += (1/2)**len(clause)
            scores[lit] = l_score
    return scores
"""
def get_JW_val(literal : int, scores : defaultdict) -> float:
    return scores[literal]
"""
if __name__ == "__main__":
    clauses = [[1,2],[1,2,3,4],[3],[-3,1,5]]
    scores = JW_heuristic(clauses=clauses,variables=[1,2,3])
    
    h = partial(get_JW_val,scores = scores)
    print(h(literal = 1))
    print(h(literal = 3)) 

    assert(h(literal=3) == 1/2 + (1/2)**4 )
    assert(h(literal=1) == 1/2**2 + (1/2)**4 + 1/2**3)
