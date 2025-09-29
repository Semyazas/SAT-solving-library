
from .propagate import Unit_propagation

class Unit_propagation_basic(Unit_propagation):
    def __init__(self, **args):
        super().__init__(**args)
        self.adjacency_dict = {}
        self._init_adjacency_dict()
        self.value = args["value"]

    def _init_adjacency_dict(self) -> None:
        for clause in self.clauses:
            for lit in clause:
                if lit not in self.adjacency_dict:
                    self.adjacency_dict[lit] = []
                self.adjacency_dict[lit].append(clause)

    def propagate(self,**args) -> tuple[bool,int]:
        """
        Standard unit propagation scanning all clauses.
        Returns True if consistent, False if conflict.
        """
        changed_literal = args["changed_literal"]
        steps_up = 0
        to_check = []
        if changed_literal != None:
            to_check = [changed_literal]
        while to_check:
            checked = None
            iterate_through = self.clauses
            if to_check != []:
                checked = to_check.pop()
                iterate_through = self.adjacency_dict[checked]
            for clause in iterate_through:
                # Check clause under current assignment
                satisfied = False
                unassigned = []
                for lit in clause:
                    val = self.value(lit)
                    if val is True:
                        satisfied = True
                        break
                    if val is None:
                        unassigned.append(lit)
                if satisfied:
                    continue
                if len(unassigned) == 0:
                    return False,steps_up  # conflict
                if len(unassigned) == 1:
                    # Unit literal
                    lit = unassigned[0]
                    if self.value(lit) is False:
                        return False, steps_up
                    if self.value(lit) is None:
                        self.enqueue(lit)
                        steps_up += 1
                        to_check.append(-lit)
        return True, steps_up
    