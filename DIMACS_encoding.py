import re

def read_file(filename: str) -> list[str]:
    """Reads a file and returns a list of lines stripped of whitespace."""
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
        self.variables = set()
        self.formulas = []

    def split_parentheses(self, lines):
        """Splits parentheses while keeping tokens intact."""
        new_lines = []
        for line in lines:
            tokens = re.findall(r'\(|\)|\w+', line)  # Extracts words and parentheses separately
            new_lines.extend(tokens)
        return new_lines

    def get_formulas(self):
        """Parses formulas from the input file and stores them."""
        lines = read_file(self.filename)
        tokens = self.split_parentheses(lines)
        
        stack = []
        formula = []

        print("Tokens:", tokens)  # Debug print

        for token in tokens:
            if token == "(":
                stack.append(token)
            elif token == ")":
                if not stack:
                    raise SyntaxError("Mismatched closing parenthesis!")
                stack.pop()  # Corrected: use pop() instead of pop(0)
            else:
                if token not in {"or", "and", "not"} and token not in self.variables:
                    self.variables.add(token)  # Add new variables
            
            formula.append(token)

            if not stack:  # If all parentheses are closed, store the formula
                self.formulas.append(formula)
                formula = []
        
        if stack:
            raise SyntaxError("Unmatched opening parenthesis!")

        print("Parsed Formulas:", self.formulas)  # Debug print

    def _parse_formula(self, tokens: list[str]) -> FormulaNode:
        """Recursively parses a list of tokens into a formula tree."""
        if not tokens:
            raise ValueError("Empty token list in _parse_formula")

        token = tokens.pop(0)
        while token == "(" or token == ")":
            token = tokens.pop(0)
        print(token)
        if token in {"and", "or"}:
            left = self._parse_formula(tokens)
            right = self._parse_formula(token)
            return FormulaNode(token, left, right)
