import re
def read_file(filename: str) -> list[str]:
    """Reads a file and returns a list of lines stripped of whitespace."""
   # print("file to read:", filename)
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

class FormulaTree: # class that makes input into syntax tree, it is also capable of converting it to CNF
    def __init__(self, filename: str):
        self.filename = filename
        self.variables = set()
        self.formulas = []
        self.get_formulas()
        self.root = None
    

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

    #    print("Parsed Formulas:", self.formulas)  # Debug print

    def _parse_formula(self, tokens: list[str]) -> FormulaNode:
        """Recursively parses a list of tokens into a formula tree."""
        if not tokens:
            raise ValueError("Empty token list in _parse_formula")

        token = tokens.pop(0)
        while token == "(" or token == ")":
            token = tokens.pop(0)
      #  print(token)
        if token in {"and", "or"}:
            left = self._parse_formula(tokens)
            right = self._parse_formula(tokens)
            return FormulaNode(token, left, right)
        
        elif token == "not":
            subformula = self._parse_formula(tokens)  # Apply "not" to a node
            return FormulaNode("not", subformula)
        
        else:
            self.variables.add(token)
            return FormulaNode(token)


    def DetectOrAnd(self,root_tree : FormulaNode) -> bool:
        if root_tree is None:
            return False
        if root_tree.op == "or" and (root_tree.left.op == "and" or root_tree.right.op == "and"):
            return True
        elif root_tree.op in {"or", "and"}:
            return self.DetectOrAnd(root_tree.left) or self.DetectOrAnd(root_tree.right)

    def NNF_tree2CNF_tree(self, root_tree: FormulaNode) -> None:
        if root_tree is None:
            return
        if root_tree.op == "or":
            # Case: (X ∧ Y) ∨ P → (P ∨ X) ∧ (P ∨ Y)
            if root_tree.left and root_tree.left.op == "and":
                X = root_tree.left.left
                Y = root_tree.left.right
                P = root_tree.right

                root_tree.op = "and"
                root_tree.left = FormulaNode("or", P, X)
                root_tree.right = FormulaNode("or", P, Y)

            # Case: P ∨ (X ∧ Y) → (P ∨ X) ∧ (P ∨ Y)
            elif root_tree.right and root_tree.right.op == "and":
                P = root_tree.left
                X = root_tree.right.left
                Y = root_tree.right.right

                root_tree.op = "and"
                root_tree.left = FormulaNode("or", P, X)
                root_tree.right = FormulaNode("or", P, Y)

        # Recursive call (only if left/right exists)
        if root_tree.left:
            self.NNF_tree2CNF_tree(root_tree.left)
        if root_tree.right:
            self.NNF_tree2CNF_tree(root_tree.right)

    def NNF2CNF(self, formula: list[str]) -> None:
        """Converts a formula from Negation Normal Form (NNF) to Conjunctive Normal Form (CNF)."""
        root_tree = self._parse_formula(formula)
    #    print("NNF Syntax Tree:", root_tree)  # Debugging
        self.NNF_tree2CNF_tree(root_tree)
     #   print("CNF Syntax Tree:", root_tree) # Debugging

        while  self.DetectOrAnd(root_tree):
            self.NNF_tree2CNF_tree(root_tree)
    #        print("CNF Syntax Tree:", root_tree) # Debugging
        self.root = root_tree  # Placeholder until transformation is implemented
    
    def clean_CNF(self, formula: list[list[str]]) -> list[list[str]]:
        """By cleaning CNF we delete redundant clauses and redundant literals in clauses."""
        clean_formula = [] 
        for clause in formula:
            clean_clause = []

            for literal in clause:
                if literal not in clean_clause:
                    clean_clause.append(literal)
                splitted_literal = literal.split()

                if (len(splitted_literal) == 2 and splitted_literal[1] in clean_clause) or \
                    "not " + literal in clean_clause:
                    clean_clause = []
                    break

            if clean_clause != []:
                clean_formula.append(clean_clause)

        return clean_formula

    def _extract_clause(self, node : FormulaNode, clause : list[str]) -> FormulaNode:
        if node.op == "or":
            for child in [node.right, node.left]:
                if child.op == "not":
                    clause.append(child.op + " " + str(child.left))
                
                elif child.op == "or":
                    self._extract_clause(child, clause)
                else:
                    self._extract_clause(child, clause)

        elif node.op == "not":
            clause.append(node.op + " " + str(node.left))
            
        elif node.op != "and":
            clause.append(node.op)

    def extract_clauses(self,formula : FormulaNode, result : list[list[str]])-> list[list[str]]:
        """This extracts from tree that is in CNF clauses and puts them into clause list"""
        if formula.op == "and":
            self.extract_clauses(formula.left,result)
            self.extract_clauses(formula.right,result)
            
        if formula.op == "or":
            clause = []
            self._extract_clause(formula, clause)
            result.append(clause)
