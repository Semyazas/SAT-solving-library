def unit_propagate_w_watched_lits(
    **args) -> tuple[bool,int]:
    """
    Standard unit propagation using watched literals.
    Returns True if consistent, False if conflict.
    """
    changed_literal = args["changed_literal"]
    clauses = args["clauses"]
    enqueue = args["enqueue"]
    assign = args["assign"]
    cl_wlits = args["clause_to_Wliterals"]
    lit_to_cls = args["literal_to_clauses"]
    to_check = [changed_literal] if changed_literal is not None else []
    steps_up = 0
    while to_check:
        checked = to_check.pop()
        for cl_idx in list(lit_to_cls[checked]):  # iterate over copy
            w1, w2 = cl_wlits[cl_idx]
            other = w1 if w1 != checked else w2

            # check if clause is already satisfied
            val = assign[abs(other)]
            if (val and other > 0) or (val is False and other < 0):
                continue

                # try to move watched literal
            moved = False
            for lit in clauses[cl_idx]:
                if lit != other:
                    v = assign[abs(lit)]
                    if v is None or (v and lit > 0) or (v is False and lit < 0):
                        cl_wlits[cl_idx] = [other, lit]
                        lit_to_cls[lit].add(cl_idx)
                        lit_to_cls[checked].discard(cl_idx)
                        moved = True
                        break
            if not moved:
                if val is False or (val is True and other < 0):
                    return False, steps_up  # conflict
                if val is None:
                    enqueue(other)
                    steps_up += 1   # Only count enqueues
                    to_check.append(-other)
    return True,steps_up