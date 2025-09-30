from .propagate import Unit_propagation
from collections import defaultdict

class Unit_propagation_watched_literals(Unit_propagation):
    def __init__(self, **args):
        super().__init__(**args)
        self.cl_wlits = defaultdict(list)
        self.lit_to_cls = defaultdict(set)
        self._begin_watched_literals()

        self.value = args["value"]
        self.assign = args["assignment"]

    def _begin_watched_literals(self) -> None:
        """Initialize watched literals data structures."""
        for cl_idx,clause in enumerate(self.clauses):
            self.cl_wlits[cl_idx] = [clause[0]]
            self.lit_to_cls[clause[0]].add(cl_idx)
            if len(clause) >=2:
                self.cl_wlits[cl_idx].append(clause[1])
                self.lit_to_cls[clause[1]].add(cl_idx)

    def _try_move_watched_literal(self,
        cl_idx: int, checked: int, other: int) -> bool:
        """
        Try to move the watched literal in clause `cl_idx` that is currently `checked`.
        Returns True if moved, False if not possible.
        """
        for lit in self.clauses[cl_idx]:
            if lit != other:
                v = self.assign[abs(lit)]
                if v is None or (v and lit > 0) or (v is False and lit < 0):
                    self.cl_wlits[cl_idx] = [other, lit]
                    self.lit_to_cls[lit].add(cl_idx)
                    self.lit_to_cls[checked].discard(cl_idx)
                    return True  # Successfully moved
        return False  # Could not move

    def propagate(self,
        **args) -> tuple[bool,int]:
        """
        Standard unit propagation using watched literals.
        Returns True if consistent, False if conflict.
        """
        changed_literal = args["changed_literal"]

        to_check = [changed_literal] if changed_literal is not None else []
        steps_up = 0
        vsids = args.get("vsids", None) 
        while to_check:
            checked = to_check.pop()
            for cl_idx in list(self.lit_to_cls[checked]):  # iterate over copy
                if len(self.cl_wlits[cl_idx]) == 1:
                    w1 = self.cl_wlits[cl_idx][0]
                    other = w1
                else:
                    w1, w2 = self.cl_wlits[cl_idx]
                    other = w1 if w1 != checked else w2

                # check if clause is already satisfied
                val = self.assign[abs(other)]

                if (val and other > 0) or (val is False and other < 0):
                    continue
                moved = self._try_move_watched_literal(cl_idx, checked, other)

                if not moved:
                    if val is False or (val is True and other < 0):
                        if vsids is not None:
                            vsids.bump_vars_from_clause(self.clauses[cl_idx])
                        return False, steps_up  # conflict
                    if val is None:
                        self.enqueue(other)
                        steps_up += 1   # Only count enqueues
                        to_check.append(-other)
        return True,steps_up