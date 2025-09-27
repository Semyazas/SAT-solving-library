from .unit_propagate_watched_literals import unit_propagate_w_watched_lits
from collections import defaultdict
class Binary_propagation:
    def __init__(self,**args):
        self.assign = args["assign"]
        self.base_enqueue = args["enqueue"]
        self.implications =  defaultdict(list)
        self.clauses = args["clauses"]
        self.clause_to_Wliterals = defaultdict(list)
        self.literal_to_clauses = defaultdict(set)
        self._init_implications()
        self.begin_watched_literals()
    def _init_implications(self):
        for clause in self.clauses:
            if len(clause) == 2:
                a, b = clause
                # When 'a' is falsified, clause becomes unit 'b'
                # When 'b' is falsified, clause becomes unit 'a'
                self.implications[a].append(b)
                self.implications[b].append(a)

    def begin_watched_literals(self) -> None:
        for  cl_idx,clause in enumerate(self.clauses):
            self.clause_to_Wliterals[cl_idx] = [clause[0]]
            self.literal_to_clauses[clause[0]].add(cl_idx)
            if len(clause) >=2:
                self.clause_to_Wliterals[cl_idx].append(clause[1])
                self.literal_to_clauses[clause[1]].add(cl_idx)

    def propagate_with_implications(self,**args):
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
            if self.assign[abs(lit)] is None:
                self.base_enqueue(lit)
                steps += 1
            # Always queue the falsified literal; watched/binary will skip if nothing to do.
            stack.append(-lit)

        # Local, non-destructive arg view for watched-literals
        local_args = dict(args)
        local_args["enqueue"] = enqueue_and_queue

        while stack:
            falsified = stack.pop()

            # --- Binary implications: falsifying `falsified` forces each implied
            for implied in self.implications[falsified]:
                val = self.assign[abs(implied)]
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
