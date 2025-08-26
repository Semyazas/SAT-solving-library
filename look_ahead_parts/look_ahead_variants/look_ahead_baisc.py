    
def look_ahead_basic(**args):
    best_val = -10000
    best_lit = None
    propagate = args["propagate"]
    mod_stack = args["modstack"]
    pre_select= args["pre_select"]
    enqueue   = args["enqueue"]
    trail     = args["trail"]
    backtrack = args["backtrack"]
    steps_up  = args["steps_up"]
    diff      = args["diff"]
    mix_diff  = args["mix_diff"]
    

    for var in pre_select(**args):
        conflicts = [False,False]
        diff_vals = [0,0]
        trail_len = len(trail)
        old_modstack_len = len(mod_stack)
        for i,lit in enumerate([var,-var]):
            enqueue(lit)
            ok , steps_it = propagate(-lit)
            diff_vals[i] = diff(lit)
            conflicts[i] = not ok
            backtrack(trail_len,old_modstack_len)
            steps_up += steps_it

        current_val = mix_diff(diff_vals[0], diff_vals[1])
        if  conflicts[0] and conflicts[1]:
            return None, False
            
        for i,sign in enumerate([1,-1]):                        
            if conflicts[i]:
                enqueue(-sign * var)
                ok, _ = propagate(falsified_literal=sign*var)
                if not ok: return None, False
                continue

        if current_val > best_val:
            best_lit = var
            best_val = current_val
    return best_lit, True
    