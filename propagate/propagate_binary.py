from propagate.unit_propagate_watched_literals import unit_propagate_w_watched_lits

def propagate_with_implications(**args):
    assign = args["assign"]
    base_enqueue = args["enqueue"]
    implications = args["implications"]

    steps = 0
    stack = []
    first = args.get("changed_literal", None)
    if first is not None:
        # The solver must pass the FALSIFIED literal here.
        stack.append(first)

    # Wrap enqueue: any new assignment also schedules its falsified literal.
    def enqueue_and_queue(lit):
        nonlocal steps
        # If already assigned consistently, base_enqueue may be a no-op in your code,
        # but that’s fine; we still push the falsified literal to drive both engines.
        if assign[abs(lit)] is None:
            base_enqueue(lit)
            steps += 1
        # Always queue the falsified literal; watched/binary will skip if nothing to do.
        stack.append(-lit)

    # Local, non-destructive arg view for watched-literals
    local_args = dict(args)
    local_args["enqueue"] = enqueue_and_queue

    while stack:
        falsified = stack.pop()

        # --- Binary implications: falsifying `falsified` forces each implied
        for implied in implications[falsified]:
            val = assign[abs(implied)]
            if val is None:
                enqueue_and_queue(implied)
            elif (val and implied < 0) or (val is False and implied > 0):
                return False, steps  # conflict

        # --- Longer clauses via watched literals, also keyed by the falsified literal
        local_args["changed_literal"] = falsified
        ok, s = unit_propagate_w_watched_lits(**local_args)
        if not ok:
            return False, steps + s
        # Any enqueues done inside watched-literals re-enter via enqueue_and_queue

    return True, steps
