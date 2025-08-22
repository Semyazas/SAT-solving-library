from collections import defaultdict
from abc import ABC, abstractmethod

class DifferenceHeuristic:
    def __init__(self,**args):
        self.clauses = args["clauses"]
        self.adjacency_dict = args["adjacency_list"]

    @abstractmethod    
    def update_score(**args):
        pass
    @abstractmethod
    def update_score(**args):
        pass