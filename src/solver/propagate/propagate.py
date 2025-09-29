from abc import abstractmethod

class Unit_propagation:
    def __init__(self, **args):
        self.clauses = args["clauses"]
        self.enqueue = args["enqueue"]

    @abstractmethod
    def propagate():
        pass 