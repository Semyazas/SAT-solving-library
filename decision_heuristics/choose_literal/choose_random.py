
import random

def choose_random(**kwargs) -> int:
    """Pick literal with maximum occurrence among unassigned vars."""
    var = random.choice(
        [i for i,l in enumerate(kwargs["assign"])
        if l is None and i != 0])
    lit = var if random.random() < 0.5 else -lit

    return lit 