import re
from task1.Syntax_tree import FormulaTree
import sys

def read_file(filename: str) -> list[str]:
    """Reads a file and returns a list of lines stripped of whitespace."""
   # print(filename)
    with open(filename, 'r') as file:
        return [line.strip() for line in file.readlines() if line.strip()]  # Remove empty lines


class FormulaNode:
    def __init__(self, op, left=None, right=None):
        self.op = op   # 'and', 'or', 'not', or variable name
        self.left = left
        self.right = right  # Only used for binary ops
    
    def __repr__(self):
        if self.op in {"and", "or"}:
            return f"({self.op} {self.left} {self.right})"
        elif self.op == "not":
            return f"(not {self.left})"
        else:
            return self.op  # Variable
        

class DIMACS_decoder:
    def __init__(self, filename):
        self.filename = filename
        self.syntax_tree = FormulaTree(filename)
        self.syntax_tree.NNF2CNF(self.syntax_tree.formulas[0])
        self.clauses = []
        self.syntax_tree.extract_clauses(self.syntax_tree.root, self.clauses)
        self.clauses = self.syntax_tree.clean_CNF(self.clauses)
        self.clauses = self.get_rid_of_repeating_clauses()

        self.variables = self.syntax_tree.variables
        self.formulas = self.syntax_tree.formulas
        
        self.var2dimacs_map= {}
        self.dmacs2var_map = {}

    def get_var_mapping(self) -> None:
        for i,var in enumerate(list(self.variables)):
            self.var2dimacs_map[var] = i+1
            self.dmacs2var_map[i+1] = var

    def get_rid_of_repeating_clauses(self) -> list[list[int]]:
        upd_clauses = []
        for clause in self.clauses:
            clause.sort()

        for clause in self.clauses:
            if clause not in upd_clauses:
                upd_clauses.append(clause)

        return upd_clauses
    def get_DIMACS(self) -> list[list[int]]:
        DMACS_clauses = []
        for clause in self.clauses:
            DMACS_clause = []   
            for literal in clause:
                spl = literal.split()
                if len(spl) > 1:
                    DMACS_clause.append(-self.var2dimacs_map[spl[1]])
                else:
                    DMACS_clause.append(self.var2dimacs_map[spl[0]])
            DMACS_clauses.append(DMACS_clause)
        
        return DMACS_clauses
    
    def print_DIMACS(self, dmacs_formula):
        print("c")
        for variable in self.variables:
            print(f"c variable:  {variable} -> {self.var2dimacs_map[variable]}")
        print(f"p cnf {len(self.variables)} {len(dmacs_formula)}")
        for clause in dmacs_formula:
            to_print = ""
            for literal in clause:
                to_print += str(literal) + " "
            print(to_print.strip() + " 0")

if __name__ == "__main__":
    decoder = DIMACS_decoder(sys.argv[1])
    
    print(decoder.formulas)
    if decoder.formulas:

        decoder.get_var_mapping()
        print("Variables:", decoder.variables)
        print("mapping",decoder.var2dimacs_map)
        DIMACS = decoder.get_DIMACS()
        decoder.print_DIMACS(DIMACS)
        print(decoder.clauses)
