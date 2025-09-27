import random

class VSIDs:
    def __init__(self, nvars, decay=0.95):
        self.activity = [0.0] * (nvars + 1)  # index by var, ignore 0
        self.decay = decay
        self.bump_value = 1.0
        self.nvars = nvars


    def pick_literal(self, **args) -> int:
        assigned = args["assign"]
        unassigned_vars = [i for i,l in enumerate(assigned)
                        if l is None]
      #  print("funguju")
        var = None if not unassigned_vars else max(unassigned_vars, key=lambda v: self.activity[v])
        if var == None:
            return None
        return var if random.random() < 0.5 else -var

    def bump_var(self, var):
        self.activity[var] += self.bump_value

    def bump_vars_from_clause(self, clause):
        for lit in clause:
            self.bump_var(abs(lit))
        # instead of decaying all activities, increase bump value
        self.bump_value /= self.decay
