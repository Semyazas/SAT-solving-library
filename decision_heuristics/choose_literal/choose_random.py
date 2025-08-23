
import random

def choose_random(**kwargs) -> int:
    """Pick literal with maximum occurrence among unassigned vars."""
    unassigned = [i for i,l in enumerate(kwargs["assign"]) if l is  None]
    if not unassigned:
        return None
  #  print(unassigned)
    var = random.choice(unassigned[1:])
    lit = var if random.random() < 0.5 else -var

    return lit 