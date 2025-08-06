from collections import defaultdict

def choose_literal(
        assign : list[int], 
        score : defaultdict,
        nvars : int
        ) -> int:
    """Pick literal with maximum occurrence among unassigned vars."""
    best_lit = None
    best_count = -1
    for var in range(1, nvars+1):
        if assign[var] is None:
            cnt_pos = score[var]
            cnt_neg = score[-var]
            if cnt_pos >= cnt_neg:
                lit = var
                cnt = cnt_pos
            else:
                lit = -var
                cnt = cnt_neg
            if cnt > best_count:
                best_count = cnt
                best_lit = lit
    return best_lit