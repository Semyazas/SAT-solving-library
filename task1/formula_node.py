def read_file(filename: str) -> list[str]:
    """
    Reads a file and returns a list of lines stripped of whitespace.
    """
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