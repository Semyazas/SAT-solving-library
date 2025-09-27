from collections import defaultdict
def pre_select(**args) -> list[int]:
    clauses       = args["clauses"]
    clause_active = args["clause_active"]
    adjacency_dict= args["adjacency_dict"]
    nvars         = args["nvars"]
    assign        = args["assign"]
    percent       = args["percent"]

    lit_occ_gt2 = defaultdict(int)
    for ci, clause in enumerate(clauses):
        if len(clause) > 2 and clause_active[ci]:
            for lit in clause:
                lit_occ_gt2[lit] += 1

        # 2) compute CRA for each currently unassigned variable x
    CRA = {}
    free_vars = [v for v in range(1, nvars + 1) if assign[v] is None]

    for x in free_vars:
        sum_pos = 0
        sum_neg = 0

            # clauses where literal x appears (positive occurrence)
        for ci in adjacency_dict[x]:
            if not clause_active[ci]:
                continue
                # sum #>2(¬yi) for other literals yi in this clause
            for yi in clauses[ci]:
                if yi == x:
                    continue
                sum_pos += lit_occ_gt2.get(-yi, 0)

            # clauses where literal -x appears (negative occurrence)
        for ci in adjacency_dict[-x]:
            if not clause_active[ci]:
                continue
            for yi in clauses[ci]:
                if yi == -x:
                    continue
                sum_neg += lit_occ_gt2.get(-yi, 0)

        CRA[x] = sum_pos * sum_neg

        # 3) If no free vars, return empty list
    if not CRA:
        return []

        # 4) pick top `percent` percent variables by CRA score (ties broken by variable index)
    pct = max(1, int(len(CRA) * percent / 100))  # at least 1
        # sort by score descending, tie-breaker: smaller var index first
    sorted_vars = sorted(CRA.items(), key=lambda kv: (-kv[1], kv[0]))
    selected = [v for v, score in sorted_vars[:pct]]

    return selected