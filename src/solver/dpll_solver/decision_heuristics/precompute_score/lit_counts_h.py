from collections import defaultdict
def lit_counts_h(**args) -> dict:
    lit_counts = defaultdict(int)
    for clause in args["clauses"]:
        for lit in clause:
            lit_counts[lit] += 1
    return lit_counts