def unit_propagate_basic(**args) -> tuple[bool,int]:
        """
        Standard unit propagation scanning all clauses.
        Returns True if consistent, False if conflict.
        """
        changed_literal = args["changed_literal"]
        adjacency_dict = args["adjacency_dict"]
        clauses = args["clauses"]
        value = args["value"]
        enqueue = args["enqueue"]
        steps_up = 0
        to_check = []
        if changed_literal != None:
            to_check = [changed_literal]
        while to_check:
            checked = None
            iterate_through = clauses
            if to_check != []:
                checked = to_check.pop()
                iterate_through = adjacency_dict[checked]
            for clause in iterate_through:
                # Check clause under current assignment
                satisfied = False
                unassigned = []
                for lit in clause:
                    val = value(lit)
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
                    if value(lit) is False:
                        return False, steps_up
                    if value(lit) is None:
                        enqueue(lit)
                        steps_up += 1
                        to_check.append(-lit)
                
        return True, steps_up